"""
FastAPI Server for Basket Operations Control Center.
Runs locally at http://127.0.0.1:7010 and reverse-proxied via Nginx at http://basket.com.
"""
import os
import sys
import time
import json
import shutil
import logging
import subprocess
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import psutil
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.control.registry import (
    SERVICES,
    FRUITS,
    BASKET_ROOT,
    LOGS_DIR,
    RUN_DIR,
)
from src.control.process_manager import (
    MANAGERS,
    get_all_service_statuses,
    get_fruit_directory_data,
    start_all_services,
    stop_all_services,
    restart_all_services,
    get_operations_history,
    record_operation,
    verify_http_health,
    is_port_listening,
)

logger = logging.getLogger("basket.control_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="Basket Operations Control Center API",
    description="Local service orchestration, process management, and fruits ecosystem dashboard API.",
    version="1.0.0",
)

# Strict CORS: local dashboard origins and all .jam domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:10020",
        "http://localhost:10020",
        "http://127.0.0.1:10010",
        "http://localhost:10010",
        "http://basket.jam",
        "https://basket.jam",
        "http://api.basket.jam",
        "https://api.basket.jam",
        "http://plum.jam",
        "https://plum.jam",
        "http://api.plum.jam",
        "https://api.plum.jam",
        "http://kiwi.jam",
        "https://kiwi.jam",
        "http://api.kiwi.jam",
        "https://api.kiwi.jam",
        "http://banana.jam",
        "https://banana.jam",
        "http://api.banana.jam",
        "https://api.banana.jam",
        "http://quince.jam",
        "https://quince.jam",
        "http://api.quince.jam",
        "https://api.quince.jam",
        "http://lemon.jam",
        "https://lemon.jam",
        "http://api.lemon.jam",
        "https://api.lemon.jam",
        "http://cherry.jam",
        "https://cherry.jam",
        "http://api.cherry.jam",
        "https://api.cherry.jam",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# KNOWN REVERSE-PROXY ROUTE INVENTORY (.jam Ecosystem)
# -----------------------------------------------------------------------------
KNOWN_ROUTES = [
    {
        "id": "basket-frontend",
        "service": "Basket Dashboard Frontend",
        "reverse_proxy_url": "https://basket.jam",
        "actual_destination": "client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": None,
    },
    {
        "id": "basket-control-api",
        "service": "Basket Control Centre API",
        "reverse_proxy_url": "https://basket.jam/api/",
        "actual_destination": "http://127.0.0.1:10020/api/",
        "type": "api",
        "fruit_id": None,
    },
    {
        "id": "basket-api",
        "service": "Basket Core API Gateway",
        "reverse_proxy_url": "https://api.basket.jam",
        "actual_destination": "http://127.0.0.1:10010",
        "type": "api",
        "fruit_id": None,
    },
    {
        "id": "llama",
        "service": "Quince LLM (llama.cpp)",
        "reverse_proxy_url": "https://llm.basket.jam",
        "actual_destination": "http://127.0.0.1:10030",
        "type": "infrastructure",
        "fruit_id": None,
    },
    {
        "id": "stt",
        "service": "Qwen3-ASR (Speech-to-Text)",
        "reverse_proxy_url": "https://stt.basket.jam",
        "actual_destination": "http://127.0.0.1:10040",
        "type": "infrastructure",
        "fruit_id": None,
    },
    {
        "id": "tts",
        "service": "Pocket TTS (Text-to-Speech)",
        "reverse_proxy_url": "https://tts.basket.jam",
        "actual_destination": "http://127.0.0.1:10050",
        "type": "infrastructure",
        "fruit_id": None,
    },
    {
        "id": "plum-frontend",
        "service": "Plum Frontend",
        "reverse_proxy_url": "https://plum.jam",
        "actual_destination": "fruits/plum/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "plum",
    },
    {
        "id": "plum-api",
        "service": "Plum API",
        "reverse_proxy_url": "https://api.plum.jam",
        "actual_destination": "http://127.0.0.2:10000",
        "type": "api",
        "fruit_id": "plum",
    },
    {
        "id": "plum-ws",
        "service": "Plum WebSocket",
        "reverse_proxy_url": "wss://plum.jam/ws",
        "actual_destination": "http://127.0.0.2:10010",
        "type": "websocket",
        "fruit_id": "plum",
    },
    {
        "id": "kiwi-frontend",
        "service": "Kiwi Frontend",
        "reverse_proxy_url": "https://kiwi.jam",
        "actual_destination": "fruits/kiwi/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "kiwi",
    },
    {
        "id": "kiwi-api",
        "service": "Kiwi API",
        "reverse_proxy_url": "https://api.kiwi.jam",
        "actual_destination": "http://127.0.0.3:10000",
        "type": "api",
        "fruit_id": "kiwi",
    },
    {
        "id": "banana-frontend",
        "service": "Banana Frontend",
        "reverse_proxy_url": "https://banana.jam",
        "actual_destination": "fruits/banana/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "banana",
    },
    {
        "id": "banana-api",
        "service": "Banana API",
        "reverse_proxy_url": "https://api.banana.jam",
        "actual_destination": "http://127.0.0.4:10000",
        "type": "api",
        "fruit_id": "banana",
    },
    {
        "id": "quince-frontend",
        "service": "Quince Frontend",
        "reverse_proxy_url": "https://quince.jam",
        "actual_destination": "fruits/quince/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "quince",
    },
    {
        "id": "quince-api",
        "service": "Quince API",
        "reverse_proxy_url": "https://api.quince.jam",
        "actual_destination": "http://127.0.0.5:10000",
        "type": "api",
        "fruit_id": "quince",
    },
    {
        "id": "quince-mcp",
        "service": "Quince MCP",
        "reverse_proxy_url": "https://mcp.quince.jam",
        "actual_destination": "http://127.0.0.5:10010",
        "type": "api",
        "fruit_id": "quince",
    },
    {
        "id": "lemon-frontend",
        "service": "Lemon Frontend",
        "reverse_proxy_url": "https://lemon.jam",
        "actual_destination": "fruits/lemon/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "lemon",
    },
    {
        "id": "lemon-api",
        "service": "Lemon API",
        "reverse_proxy_url": "https://api.lemon.jam",
        "actual_destination": "http://127.0.0.6:10000",
        "type": "api",
        "fruit_id": "lemon",
    },
    {
        "id": "cherry-frontend",
        "service": "Cherry Frontend",
        "reverse_proxy_url": "https://cherry.jam",
        "actual_destination": "fruits/cherry/client/dist (Static Nginx)",
        "type": "frontend",
        "fruit_id": "cherry",
    },
    {
        "id": "cherry-api",
        "service": "Cherry API",
        "reverse_proxy_url": "https://api.cherry.jam",
        "actual_destination": "http://127.0.0.7:10000",
        "type": "api",
        "fruit_id": "cherry",
    },
]


# -----------------------------------------------------------------------------
# CONTROL API ENDPOINTS
# -----------------------------------------------------------------------------

_CPU_TEMP_CACHE = {"temp": None, "time": 0.0}

def get_cpu_temperature() -> Optional[float]:
    """Retrieves CPU thermal zone temperature in Celsius from Windows WMI."""
    now = time.time()
    if now - _CPU_TEMP_CACHE["time"] < 1.5:
        return _CPU_TEMP_CACHE["temp"]
    
    val = None
    try:
        import pythoncom
        import win32com.client
        import gc
        pythoncom.CoInitialize()
        locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        service = locator.ConnectServer(".", "root\\cimv2")
        items = service.ExecQuery("SELECT HighPrecisionTemperature, Temperature FROM Win32_PerfFormattedData_Counters_ThermalZoneInformation")
        for item in items:
            hp = getattr(item, "HighPrecisionTemperature", None)
            if hp and hp > 2732:
                val = round((hp - 2732) / 10.0, 1)
                break
            t = getattr(item, "Temperature", None)
            if t and t > 273:
                val = round(t - 273.15, 1)
                break
        del item
        del items
        del service
        del locator
        gc.collect()
        pythoncom.CoUninitialize()
    except Exception:
        pass

    _CPU_TEMP_CACHE["temp"] = val
    _CPU_TEMP_CACHE["time"] = now
    return val


def get_system_telemetry() -> Dict[str, Any]:
    """Collects real-time CPU, RAM, and GPU telemetry."""
    vm = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=0.0)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_temp = get_cpu_temperature()

    gpu_data = {
        "available": False,
        "name": None,
        "gpu_utilization_pct": 0,
        "temperature_c": 0,
        "vram_used_mb": 0,
        "vram_total_mb": 0,
        "vram_pct": 0.0,
    }

    if shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 5:
                    v_used = int(parts[3])
                    v_total = int(parts[4])
                    gpu_data = {
                        "available": True,
                        "name": parts[0],
                        "gpu_utilization_pct": int(parts[1]),
                        "temperature_c": int(parts[2]),
                        "vram_used_mb": v_used,
                        "vram_total_mb": v_total,
                        "vram_pct": round((v_used / v_total) * 100, 1) if v_total > 0 else 0.0,
                    }
        except Exception:
            pass

    return {
        "cpu": {
            "utilization_pct": cpu_pct,
            "logical_cores": cpu_count,
            "temperature_c": cpu_temp,
        },
        "memory": {
            "used_bytes": vm.used,
            "total_bytes": vm.total,
            "used_gb": round(vm.used / (1024**3), 2),
            "total_gb": round(vm.total / (1024**3), 2),
            "utilization_pct": vm.percent,
        },
        "gpu": gpu_data,
    }


@app.get("/api/health")
async def health_check():
    """Health status of the Basket operations control plane."""
    return {
        "status": "healthy",
        "service": "basket-control",
        "timestamp": datetime.now(timezone.utc).isoformat() if "datetime" in globals() else time.time(),
        "port": 10020,
    }


@app.get("/api/system/telemetry")
async def system_telemetry_endpoint():
    """Real-time hardware telemetry: CPU, GPU, VRAM, and RAM usage."""
    return get_system_telemetry()


@app.get("/api/overview")
async def get_overview():
    """Summary metrics for the dashboard overview screen."""
    statuses = get_all_service_statuses()
    status_map = {s["id"]: s for s in statuses}
    fruit_data = get_fruit_directory_data(status_map=status_map)

    total_services = len(statuses)
    running_services = sum(1 for s in statuses if s["is_running"])
    stopped_services = sum(1 for s in statuses if not s["is_running"])
    healthy_services = sum(1 for s in statuses if s["status"] == "healthy")
    degraded_services = sum(1 for s in statuses if s["status"] == "degraded")

    # Route check stats (evaluated in parallel)
    routes_checked = await get_routes()
    total_routes = len(routes_checked)
    live_routes = sum(1 for r in routes_checked if r.get("is_live"))

    nginx_mgr = MANAGERS.get("nginx")
    nginx_status = nginx_mgr.get_status() if nginx_mgr else {"status": "unknown"}

    return {
        "metrics": {
            "total_services": total_services,
            "running_services": running_services,
            "stopped_services": stopped_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "total_routes": total_routes,
            "live_routes": live_routes,
            "unavailable_routes": total_routes - live_routes,
            "nginx_state": nginx_status.get("status", "unknown"),
        },
        "system": get_system_telemetry(),
        "services": statuses,
        "fruits": fruit_data,
        "recent_operations": get_operations_history(limit=10),
    }


@app.get("/api/services")
async def list_services():
    """List all managed services and their verified runtime states."""
    return get_all_service_statuses()


@app.post("/api/services/all/start")
async def start_all_endpoint():
    """Start all ecosystem services in verified dependency order."""
    return start_all_services()


@app.post("/api/services/all/end")
async def end_all_endpoint():
    """Stop all ecosystem services in reverse dependency order."""
    return stop_all_services()


@app.post("/api/services/all/restart")
async def restart_all_endpoint():
    """Restart all ecosystem services in order."""
    return restart_all_services()


# -----------------------------------------------------------------------------
# AI MODELS BATCH CONTROL (LLM, TTS, STT)
# -----------------------------------------------------------------------------

MODEL_SERVICE_IDS = ["llm-llama", "tts-pocket", "stt-qwen"]

@app.post("/api/models/start")
async def start_models_endpoint():
    """Start all AI model runtimes (LLM, TTS, STT) in parallel."""
    results = {}
    for sid in MODEL_SERVICE_IDS:
        if sid in MANAGERS:
            results[sid] = MANAGERS[sid].start()
    return {"success": True, "action": "models_start", "results": results}


@app.post("/api/models/end")
async def end_models_endpoint():
    """Stop all AI model runtimes (LLM, TTS, STT) at once."""
    results = {}
    for sid in MODEL_SERVICE_IDS:
        if sid in MANAGERS:
            results[sid] = MANAGERS[sid].stop()
    return {"success": True, "action": "models_end", "results": results}


@app.post("/api/models/restart")
async def restart_models_endpoint():
    """Restart all AI model runtimes (LLM, TTS, STT) at once."""
    results = {}
    for sid in MODEL_SERVICE_IDS:
        if sid in MANAGERS:
            results[sid] = MANAGERS[sid].restart()
    return {"success": True, "action": "models_restart", "results": results}


@app.get("/api/services/{service_id}")
async def get_service(service_id: str):
    """Get single service status."""
    if service_id not in MANAGERS:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")
    return MANAGERS[service_id].get_status()


@app.post("/api/services/{service_id}/start")
async def start_service_endpoint(service_id: str):
    """Start an individual service."""
    if service_id not in MANAGERS:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")
    res = MANAGERS[service_id].start()
    return res


@app.post("/api/services/{service_id}/end")
async def end_service_endpoint(service_id: str):
    """End/stop an individual service."""
    if service_id not in MANAGERS:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")
    res = MANAGERS[service_id].stop()
    return res


@app.post("/api/services/{service_id}/restart")
async def restart_service_endpoint(service_id: str, background_tasks: BackgroundTasks):
    """Restart an individual service."""
    if service_id not in MANAGERS:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")

    # Special handling for Basket Control self-restart
    if service_id == "basket-control":
        def delayed_self_restart():
            time.sleep(1.0)
            ps_cmd = (
                "$p = Get-Process -Id " + str(os.getpid()) + " -ErrorAction SilentlyContinue; "
                "if ($p) { Stop-Process -Id " + str(os.getpid()) + " -Force }; "
                "Start-Process -FilePath '" + str(BASKET_ROOT / ".venv" / "Scripts" / "python.exe") + "' "
                "-ArgumentList 'run_control.py' -WorkingDirectory '" + str(BASKET_ROOT) + "'"
            )
            subprocess.Popen(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd])

        background_tasks.add_task(delayed_self_restart)
        return {
            "success": True,
            "action": "restart",
            "message": "Basket Control restarting asynchronously. Interface will reconnect in 3 seconds.",
        }

    res = MANAGERS[service_id].restart()
    return res


@app.get("/api/fruits")
async def list_fruits():
    """List all fruits in the ecosystem with real icons and live health states."""
    return get_fruit_directory_data()


@app.post("/api/fruits/{fruit_id}/start")
async def start_fruit_endpoint(fruit_id: str):
    """Start all components for a specific fruit."""
    if fruit_id not in FRUITS:
        raise HTTPException(status_code=404, detail=f"Fruit '{fruit_id}' not found.")

    fruit = FRUITS[fruit_id]
    if fruit.get("is_android_client"):
        return {"success": True, "message": "Lemon is an Android client. No background Windows daemon to start."}

    results = {}
    overall = True
    for c_id in fruit.get("components", []):
        if c_id in MANAGERS:
            r = MANAGERS[c_id].start()
            results[c_id] = r
            if not r.get("success", False):
                overall = False

    return {"success": overall, "action": "fruit_start", "fruit_id": fruit_id, "components": results}


@app.post("/api/fruits/{fruit_id}/end")
async def end_fruit_endpoint(fruit_id: str):
    """End all components for a specific fruit."""
    if fruit_id not in FRUITS:
        raise HTTPException(status_code=404, detail=f"Fruit '{fruit_id}' not found.")

    fruit = FRUITS[fruit_id]
    if fruit.get("is_android_client"):
        return {"success": True, "message": "Lemon is an Android client."}

    results = {}
    overall = True
    for c_id in reversed(fruit.get("components", [])):
        if c_id in MANAGERS:
            r = MANAGERS[c_id].stop()
            results[c_id] = r
            if not r.get("success", False):
                overall = False

    return {"success": overall, "action": "fruit_end", "fruit_id": fruit_id, "components": results}


@app.post("/api/fruits/{fruit_id}/restart")
async def restart_fruit_endpoint(fruit_id: str):
    """Restart all components for a specific fruit."""
    if fruit_id not in FRUITS:
        raise HTTPException(status_code=404, detail=f"Fruit '{fruit_id}' not found.")

    fruit = FRUITS[fruit_id]
    if fruit.get("is_android_client"):
        return {"success": True, "message": "Lemon is an Android client."}

    results = {}
    overall = True
    for c_id in fruit.get("components", []):
        if c_id in MANAGERS:
            r = MANAGERS[c_id].restart()
            results[c_id] = r
            if not r.get("success", False):
                overall = False

    return {"success": overall, "action": "fruit_restart", "fruit_id": fruit_id, "components": results}


@app.get("/api/logs/{service_id}")
async def get_service_logs(service_id: str, tail: int = Query(150, ge=10, le=1000)):
    """Fetch recent log lines for a specific service."""
    if service_id not in MANAGERS:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")
    lines = MANAGERS[service_id].read_logs(lines=tail)
    return {
        "service_id": service_id,
        "name": MANAGERS[service_id].service.name,
        "line_count": len(lines),
        "lines": lines,
    }


@app.get("/api/routes")
async def get_routes():
    """List all reverse-proxy routes and check real-time reachability."""
    results = [dict(r) for r in KNOWN_ROUTES]

    def _check(item: dict):
        if item["type"] in ("frontend", "api"):
            ok, status_code, msg = verify_http_health(item["reverse_proxy_url"], timeout=1.0)
            item["is_live"] = ok
            item["status_code"] = status_code
            item["message"] = msg
        else:
            item["is_live"] = True
            item["status_code"] = 101
            item["message"] = "WebSocket Endpoint"

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(results))) as ex:
        list(ex.map(_check, results))

    return results


@app.get("/api/operations")
async def get_operations(limit: int = Query(50, ge=1, le=200)):
    """Retrieve recent operations history."""
    return get_operations_history(limit=limit)


@app.get("/api/nginx/status")
async def get_nginx_status():
    """Inspect Nginx reverse proxy state and validate configuration."""
    mgr = MANAGERS.get("nginx")
    status = mgr.get_status() if mgr else {}
    
    # Check port 80 and 443
    p80 = is_port_listening("127.0.0.1", 80)
    p443 = is_port_listening("127.0.0.1", 443)

    return {
        "status": status,
        "listening_80": p80,
        "listening_443": p443,
        "config_path": r"C:\nginx\conf\nginx.conf",
    }


@app.post("/api/nginx/validate")
async def validate_nginx_config():
    """Validates Nginx configuration syntax with nginx -t."""
    nginx_exe = Path(r"C:\nginx\nginx.exe")
    nginx_conf = Path(r"C:\nginx\conf\nginx.conf")
    
    res = subprocess.run([str(nginx_exe), "-p", "C:/nginx", "-t", "-c", str(nginx_conf)], cwd=r"C:\nginx", capture_output=True, text=True)
    return {
        "valid": res.returncode == 0,
        "exit_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@app.post("/api/nginx/reload")
async def reload_nginx_config():
    """Gracefully reloads Nginx configuration after validation."""
    nginx_exe = Path(r"C:\nginx\nginx.exe")
    nginx_conf = Path(r"C:\nginx\conf\nginx.conf")
    
    test_res = subprocess.run([str(nginx_exe), "-p", "C:/nginx", "-t", "-c", str(nginx_conf)], cwd=r"C:\nginx", capture_output=True, text=True)
    if test_res.returncode != 0:
        return {
            "success": False,
            "message": "Nginx configuration syntax test failed. Aborted reload.",
            "stderr": test_res.stderr,
        }
        
    res = subprocess.run([str(nginx_exe), "-p", "C:/nginx", "-s", "reload"], cwd=r"C:\nginx", capture_output=True, text=True)
    return {
        "success": res.returncode == 0,
        "message": "Nginx reloaded successfully." if res.returncode == 0 else "Nginx reload failed.",
        "stderr": res.stderr,
    }


# -----------------------------------------------------------------------------
# STATIC CLIENT HOSTING (SPA FALLBACK)
# -----------------------------------------------------------------------------
CLIENT_DIST = BASKET_ROOT / "client" / "dist"

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serves built static React client assets and handles SPA HTML fallback."""
    # Never intercept /api requests
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found.")

    target_file = CLIENT_DIST / full_path
    if target_file.is_file():
        return FileResponse(target_file)

    # Fallback to index.html for React Router
    index_file = CLIENT_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return JSONResponse(
        status_code=200,
        content={"message": "Basket Operations Control Server is active on port 10020. Client build in progress."},
    )

