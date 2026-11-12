"""
Process Manager for Basket Operations Control Center.
Provides safe Windows process identification, tree-aware termination,
persistent logging, and health monitoring.
"""
import os
import sys
import time
import json
import socket
import logging
import threading
import subprocess
import ssl
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import urllib.request
import urllib.error

import psutil

from src.control.registry import (
    SERVICES,
    FRUITS,
    ServiceDef,
    BASKET_ROOT,
    LOGS_DIR,
    RUN_DIR,
)

logger = logging.getLogger("basket.process_manager")

# Ensure required directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RUN_DIR.mkdir(parents=True, exist_ok=True)

# Threading locks per service to prevent concurrent conflicting operations
_SERVICE_LOCKS: Dict[str, threading.Lock] = {
    s_id: threading.Lock() for s_id in SERVICES.keys()
}
_GLOBAL_LOCK = threading.Lock()

# Persistent operations history file
OPERATIONS_HISTORY_FILE = RUN_DIR / "operations.json"


def record_operation(
    service_id: str,
    action: str,
    status: str,
    duration_ms: int = 0,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Records an operation in persistent history."""
    entry = {
        "id": f"{int(time.time() * 1000)}-{service_id}-{action}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service_id": service_id,
        "action": action,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
    }
    
    with _GLOBAL_LOCK:
        try:
            history = []
            if OPERATIONS_HISTORY_FILE.exists():
                try:
                    history = json.loads(OPERATIONS_HISTORY_FILE.read_text(encoding="utf-8"))
                except Exception:
                    history = []
            history.insert(0, entry)
            # Retain up to 200 operations
            history = history[:200]
            OPERATIONS_HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist operation record: {e}")
            
    return entry


def get_operations_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns recent operations history."""
    with _GLOBAL_LOCK:
        if not OPERATIONS_HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(OPERATIONS_HISTORY_FILE.read_text(encoding="utf-8"))
            return data[:limit]
        except Exception:
            return []


def is_port_listening(host: str, port: int, timeout: float = 1.0) -> bool:
    """Checks if a TCP port is actively listening."""
    if not port:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            res = s.connect_ex((host or "127.0.0.1", port))
            return res == 0
    except Exception:
        return False


_SSL_CONTEXT = ssl._create_unverified_context()

def verify_http_health(url: str, timeout: float = 1.0) -> Tuple[bool, int, str]:
    """Tests an HTTP endpoint."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Basket-Operations-Monitor/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            status = resp.status
            return (200 <= status < 400), status, "OK"
    except urllib.error.HTTPError as e:
        # A 404 or 401 still proves the web server is running and responding!
        return (e.code < 500), e.code, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)


class ServiceManager:
    """
    Manages the lifecycle of a single ServiceDef.
    """

    def __init__(self, service: ServiceDef):
        self.service = service
        self.lock = _SERVICE_LOCKS.setdefault(service.id, threading.Lock())
        self.pid_file = RUN_DIR / f"{service.id}.pid"
        self.log_file = LOGS_DIR / f"{service.id}.log"

    def _read_pid_file(self) -> Optional[Tuple[int, float]]:
        """Reads cached PID and process creation time."""
        if not self.pid_file.exists():
            return None
        try:
            content = self.pid_file.read_text(encoding="utf-8").strip()
            if not content:
                return None
            parts = content.split(":")
            pid = int(parts[0])
            create_time = float(parts[1]) if len(parts) > 1 else 0.0
            return pid, create_time
        except Exception:
            return None

    def _write_pid_file(self, pid: int, create_time: float):
        """Writes PID and creation time."""
        try:
            self.pid_file.write_text(f"{pid}:{create_time}", encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not write PID file for {self.service.id}: {e}")

    def _clear_pid_file(self):
        """Removes PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass

    def find_process(self, proc_snapshot: Optional[List[psutil.Process]] = None) -> Optional[psutil.Process]:
        """
        Reliably locates the running process for this service using:
        1. Cached PID file with verified create_time
        2. System-wide scan matching executable names, cmdline args, and ports
        """
        # 1. Try cached PID
        pid_info = self._read_pid_file()
        if pid_info:
            pid, cached_ctime = pid_info
            try:
                p = psutil.Process(pid)
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    # Verify creation time within 2s tolerance if known
                    if cached_ctime == 0.0 or abs(p.create_time() - cached_ctime) < 2.0:
                        # Verify executable name match if specified
                        if not self.service.match_exe_names or p.name().lower() in [n.lower() for n in self.service.match_exe_names]:
                            if self._matches_process(p):
                                return p
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._clear_pid_file()

        # 2. Match by listening ports first (most reliable for network servers)
        if self.service.match_ports:
            for port in self.service.match_ports:
                for conn in psutil.net_connections(kind="inet"):
                    if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port == port:
                        if self.service.host and conn.laddr.ip not in ("0.0.0.0", "::", self.service.host):
                            continue
                        if conn.pid:
                            try:
                                p = psutil.Process(conn.pid)
                                if self._matches_process(p):
                                    self._write_pid_file(p.pid, p.create_time())
                                    return p
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

        # 3. Scan running processes by exe name and commandline
        procs = proc_snapshot if proc_snapshot is not None else psutil.process_iter(["pid", "name", "cmdline", "create_time"])
        for p in procs:
            try:
                if self._matches_process(p):
                    self._write_pid_file(p.pid, p.create_time())
                    return p
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return None

    def _matches_process(self, p: psutil.Process) -> bool:
        """Checks if a psutil.Process matches this service's rules."""
        try:
            name = p.name().lower()
            if self.service.match_exe_names:
                if not any(name == target.lower() for target in self.service.match_exe_names):
                    return False

            # Check commandline and cwd first if specified
            if self.service.match_cmdline_contains:
                try:
                    cmdline = " ".join(p.cmdline()).lower().replace("/", "\\")
                except Exception:
                    cmdline = ""
                try:
                    cwd = p.cwd().lower().replace("/", "\\")
                except Exception:
                    cwd = ""
                combined_context = f"{cmdline} {cwd}".strip()
                if combined_context:
                    matched = all(
                        needle.lower().replace("/", "\\") in combined_context
                        for needle in self.service.match_cmdline_contains
                    )
                    if not matched:
                        return False
                else:
                    # AccessDenied or empty cmdline: verify listening port
                    if not (self.service.port and is_port_listening(self.service.host, self.service.port)):
                        return False

            # Check listening ports on the process
            if self.service.match_ports:
                port_matched = False
                try:
                    for conn in p.net_connections(kind="inet"):
                        if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port in self.service.match_ports:
                            if not self.service.host or conn.laddr.ip in ("0.0.0.0", "::", self.service.host):
                                port_matched = True
                                break
                except Exception:
                    pass
                if not port_matched:
                    if not self.service.match_cmdline_contains:
                        return False

            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_status(self, proc_snapshot: Optional[List[psutil.Process]] = None) -> Dict[str, Any]:
        """Returns real-time status of this service."""
        proc = self.find_process(proc_snapshot=proc_snapshot)
        is_running = proc is not None
        is_listening = False
        health_ok = False
        health_message = "Stopped"
        status = "stopped"
        pid = None
        memory_mb = 0.0
        cpu_percent = 0.0
        uptime_sec = 0

        if is_running:
            pid = proc.pid
            status = "running"
            try:
                uptime_sec = int(time.time() - proc.create_time())
                memory_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
                cpu_percent = round(proc.cpu_percent(interval=0.0), 1)
            except Exception:
                pass

            # Check port listening
            if self.service.port:
                is_listening = is_port_listening(self.service.host, self.service.port)

            # Perform health check
            if self.service.health_type == "http" and self.service.health_url:
                h_ok, code, msg = verify_http_health(self.service.health_url)
                health_ok = h_ok
                health_message = f"HTTP {code} ({msg})" if code else msg
                status = "healthy" if health_ok else "degraded"
            elif self.service.health_type == "tcp" and self.service.health_port:
                health_ok = is_port_listening(self.service.host, self.service.health_port)
                health_message = "Port open" if health_ok else "Port not responding"
                status = "healthy" if health_ok else "degraded"
            else:
                health_ok = True
                health_message = "Process running"
                status = "healthy"

        return {
            "id": self.service.id,
            "name": self.service.name,
            "category": self.service.category,
            "fruit_id": self.service.fruit_id,
            "description": self.service.description,
            "status": status,
            "is_running": is_running,
            "is_healthy": health_ok,
            "is_listening": is_listening,
            "health_message": health_message,
            "pid": pid,
            "host": self.service.host,
            "port": self.service.port,
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "uptime_sec": uptime_sec,
            "log_file": str(self.log_file),
            "task_scheduler_task": self.service.task_scheduler_task,
        }

    def start(self) -> Dict[str, Any]:
        """Starts the service if not running."""
        with self.lock:
            start_time = time.time()
            existing = self.find_process()
            if existing:
                return {
                    "success": True,
                    "action": "start",
                    "status": "already_running",
                    "pid": existing.pid,
                    "message": f"{self.service.name} is already running (PID {existing.pid}).",
                }

            # Check if static only
            if self.service.is_static_only:
                return {
                    "success": True,
                    "action": "start",
                    "status": "static_only",
                    "message": f"{self.service.name} is a static frontend served by global Nginx.",
                }

            # Prepare environment
            env = os.environ.copy()
            if self.service.env:
                env.update(self.service.env)

            # Ensure log file
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n============================================================\n")
                    f.write(f"[{timestamp}] STARTING: {self.service.name}\n")
                    f.write(f"Command: {' '.join(self.service.command)}\n")
                    f.write(f"============================================================\n")
            except Exception:
                pass

            try:
                # On Windows, launch detached background process via Start-Process
                if sys.platform == "win32":
                    cmd_parts = []
                    for arg in self.service.command:
                        if " " in arg or "^" in arg or "&" in arg or "(" in arg or ")" in arg:
                            cmd_parts.append(f'"{arg}"')
                        else:
                            cmd_parts.append(arg)
                    cmd_full = " ".join(cmd_parts)
                    ps_arg = f'/c {cmd_full} >> "{self.log_file}" 2>&1'.replace('"', '`"')
                    ps_cmd = (
                        f'Start-Process -FilePath "cmd.exe" -ArgumentList "{ps_arg}" '
                        f'-WorkingDirectory "{self.service.work_dir}" -WindowStyle Hidden'
                    )
                    subprocess.run(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd], check=False)
                    time.sleep(1.2)

                    # Verification loop
                    for _ in range(8):
                        proc = self.find_process()
                        if proc:
                            self._write_pid_file(proc.pid, proc.create_time())
                            if not self.service.port or is_port_listening(self.service.host, self.service.port):
                                dur = int((time.time() - start_time) * 1000)
                                record_operation(self.service.id, "start", "success", dur)
                                return {
                                    "success": True,
                                    "action": "start",
                                    "status": "started",
                                    "pid": proc.pid,
                                    "message": f"Successfully started {self.service.name} (PID {proc.pid}).",
                                }
                        time.sleep(0.5)

                    proc = self.find_process()
                    if proc:
                        self._write_pid_file(proc.pid, proc.create_time())
                        dur = int((time.time() - start_time) * 1000)
                        record_operation(self.service.id, "start", "success", dur)
                        return {
                            "success": True,
                            "action": "start",
                            "status": "started",
                            "pid": proc.pid,
                            "message": f"Successfully started {self.service.name} (PID {proc.pid}).",
                        }
                    else:
                        dur = int((time.time() - start_time) * 1000)
                        err_msg = "Process did not remain running or failed to bind port. Check service log."
                        record_operation(self.service.id, "start", "failed", dur, err_msg)
                        return {
                            "success": False,
                            "action": "start",
                            "status": "failed",
                            "message": f"Failed to start {self.service.name}: {err_msg}",
                        }

                log_handle = open(self.log_file, "a", encoding="utf-8")
                proc = subprocess.Popen(
                    self.service.command,
                    cwd=self.service.work_dir,
                    env=env,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )

                self._write_pid_file(proc.pid, time.time())

                # Verification loop: wait up to 4s for process or port
                time.sleep(1.0)
                for _ in range(6):
                    if proc.poll() is not None:
                        dur = int((time.time() - start_time) * 1000)
                        err_msg = f"Process exited with code {proc.returncode}."
                        record_operation(self.service.id, "start", "failed", dur, err_msg)
                        return {
                            "success": False,
                            "action": "start",
                            "status": "failed",
                            "message": f"Failed to start {self.service.name}: {err_msg}",
                        }

                    if self.service.port and is_port_listening(self.service.host, self.service.port):
                        break
                    time.sleep(0.5)

                dur = int((time.time() - start_time) * 1000)
                record_operation(self.service.id, "start", "success", dur)
                return {
                    "success": True,
                    "action": "start",
                    "status": "started",
                    "pid": proc.pid,
                    "message": f"Successfully started {self.service.name} (PID {proc.pid}).",
                }

            except Exception as e:
                dur = int((time.time() - start_time) * 1000)
                err_msg = str(e)
                record_operation(self.service.id, "start", "failed", dur, err_msg)
                return {
                    "success": False,
                    "action": "start",
                    "status": "error",
                    "message": f"Exception starting {self.service.name}: {err_msg}",
                }

    def stop(self) -> Dict[str, Any]:
        """Safely ends the service process tree."""
        with self.lock:
            start_time = time.time()
            proc = self.find_process()

            if not proc:
                self._clear_pid_file()
                return {
                    "success": True,
                    "action": "end",
                    "status": "already_stopped",
                    "message": f"{self.service.name} was not running.",
                }

            # 1. Custom stop command if configured
            if self.service.custom_stop:
                try:
                    subprocess.run(
                        self.service.custom_stop,
                        cwd=self.service.work_dir,
                        capture_output=True,
                        timeout=5,
                    )
                    time.sleep(1.0)
                    if not proc.is_running():
                        self._clear_pid_file()
                        dur = int((time.time() - start_time) * 1000)
                        record_operation(self.service.id, "end", "success", dur)
                        return {
                            "success": True,
                            "action": "end",
                            "status": "stopped",
                            "message": f"{self.service.name} stopped gracefully via custom command.",
                        }
                except Exception as e:
                    logger.warning(f"Custom stop for {self.service.id} failed, falling back to process tree termination: {e}")

            # 2. Process tree termination
            try:
                children = proc.children(recursive=True)
                all_procs = children + [proc]

                # Graceful termination first
                for p in all_procs:
                    try:
                        p.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                gone, alive = psutil.wait_procs(all_procs, timeout=3.0)

                # Force kill any lingering processes in this verified tree
                for p in alive:
                    try:
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                self._clear_pid_file()

                # Log stop (safely ignore transient Windows file lock if handle is releasing)
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(f"\n[{timestamp}] STOPPED: {self.service.name}\n")
                except Exception:
                    pass

                dur = int((time.time() - start_time) * 1000)
                record_operation(self.service.id, "end", "success", dur)
                return {
                    "success": True,
                    "action": "end",
                    "status": "stopped",
                    "message": f"Successfully stopped {self.service.name}.",
                }

            except Exception as e:
                dur = int((time.time() - start_time) * 1000)
                err_msg = str(e)
                record_operation(self.service.id, "end", "failed", dur, err_msg)
                return {
                    "success": False,
                    "action": "end",
                    "status": "error",
                    "message": f"Error stopping {self.service.name}: {err_msg}",
                }

    def restart(self) -> Dict[str, Any]:
        """Restarts the service safely."""
        start_time = time.time()
        stop_res = self.stop()
        time.sleep(1.0)
        start_res = self.start()

        dur = int((time.time() - start_time) * 1000)
        success = start_res.get("success", False)
        record_operation(self.service.id, "restart", "success" if success else "failed", dur)

        return {
            "success": success,
            "action": "restart",
            "stop_result": stop_res,
            "start_result": start_res,
            "message": f"Restart completed for {self.service.name}." if success else f"Restart failed for {self.service.name}.",
        }

    def read_logs(self, lines: int = 150) -> List[str]:
        """Reads recent log lines for this service."""
        if not self.log_file.exists():
            return [f"No logs generated yet for {self.service.name}."]

        try:
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                return [line.rstrip("\r\n") for line in all_lines[-lines:]]
        except Exception as e:
            return [f"Error reading log file: {e}"]


# Global dictionary of managers
MANAGERS: Dict[str, ServiceManager] = {
    s_id: ServiceManager(s_def) for s_id, s_def in SERVICES.items()
}


def get_all_service_statuses() -> List[Dict[str, Any]]:
    """Returns status of every service in the registry using a single process snapshot."""
    try:
        proc_snapshot = list(psutil.process_iter(["pid", "name", "cmdline", "create_time"]))
    except Exception:
        proc_snapshot = None
    return [mgr.get_status(proc_snapshot=proc_snapshot) for mgr in MANAGERS.values()]


def get_fruit_directory_data(status_map: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Returns rich directory info for every fruit, including health and routes."""
    if status_map is None:
        status_map = {s["id"]: s for s in get_all_service_statuses()}
    results = []
    urls_to_check: List[Tuple[Dict[str, Any], str, str]] = []

    for fruit_id, fruit_meta in FRUITS.items():
        entry = dict(fruit_meta)
        
        # Check component statuses
        component_statuses = []
        overall_running = True if entry.get("components") else False
        for c_id in entry.get("components", []):
            if c_id in status_map:
                c_status = status_map[c_id]
                component_statuses.append(c_status)
                if not c_status["is_running"]:
                    overall_running = False
            elif c_id in MANAGERS:
                c_status = MANAGERS[c_id].get_status()
                component_statuses.append(c_status)
                if not c_status["is_running"]:
                    overall_running = False

        entry["component_details"] = component_statuses
        entry["is_running"] = overall_running
        entry["frontend_live"] = False
        entry["api_live"] = False

        f_url = entry.get("frontend_url") if entry.get("is_redirector_enabled") else None
        a_url = entry.get("api_url") if entry.get("is_redirector_enabled") else None

        if f_url:
            urls_to_check.append((entry, "frontend_live", f_url))
        if a_url:
            urls_to_check.append((entry, "api_live", a_url))

        results.append(entry)

    if urls_to_check:
        def _check(item: Tuple[Dict[str, Any], str, str]):
            ent, field, url = item
            ok, _, _ = verify_http_health(url, timeout=1.0)
            ent[field] = ok

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(urls_to_check))) as ex:
            list(ex.map(_check, urls_to_check))

    return results


def start_all_services() -> Dict[str, Any]:
    """Starts all services in verified dependency order (excluding decommissioned SearXNG)."""
    start_time = time.time()
    # Sort by startup_priority ascending
    sorted_services = sorted(SERVICES.values(), key=lambda s: s.startup_priority)
    results = {}
    overall_success = True

    for s_def in sorted_services:
        mgr = MANAGERS[s_def.id]
        res = mgr.start()
        results[s_def.id] = res
        if not res.get("success", False):
            overall_success = False

    dur = int((time.time() - start_time) * 1000)
    record_operation("all", "start", "success" if overall_success else "failed", dur)
    return {
        "success": overall_success,
        "action": "start_all",
        "results": results,
    }


def stop_all_services() -> Dict[str, Any]:
    """Stops all services in verified reverse dependency order."""
    start_time = time.time()
    # Sort by shutdown_priority ascending (lowest priority number shuts down first)
    sorted_services = sorted(SERVICES.values(), key=lambda s: s.shutdown_priority)
    results = {}
    overall_success = True

    for s_def in sorted_services:
        # Don't stop basket-control during stop_all unless explicitly targeted
        if s_def.id == "basket-control":
            continue
        mgr = MANAGERS[s_def.id]
        res = mgr.stop()
        results[s_def.id] = res
        if not res.get("success", False):
            overall_success = False

    dur = int((time.time() - start_time) * 1000)
    record_operation("all", "end", "success" if overall_success else "failed", dur)
    return {
        "success": overall_success,
        "action": "end_all",
        "results": results,
    }


def restart_all_services() -> Dict[str, Any]:
    """Safely ends all services and starts them back up in dependency order."""
    stop_res = stop_all_services()
    time.sleep(2.0)
    start_res = start_all_services()
    return {
        "success": stop_res["success"] and start_res["success"],
        "action": "restart_all",
        "stop_results": stop_res,
        "start_results": start_res,
    }
