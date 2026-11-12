"""
Command-Line Management Interface for Basket Operations.
Invoked by BAT scripts and system operators.
"""
import sys
import json
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.control.registry import SERVICES, FRUITS
from src.control.process_manager import (
    MANAGERS,
    start_all_services,
    stop_all_services,
    restart_all_services,
    get_all_service_statuses,
)


def print_banner(title: str):
    print("\n" + "=" * 60)
    print(f"  {title.upper()}")
    print("=" * 60 + "\n")


def manage_single_service(action: str, service_id: str) -> int:
    if service_id not in MANAGERS:
        print(f"ERROR: Unknown service ID '{service_id}'.")
        print(f"Available services: {', '.join(SERVICES.keys())}")
        return 1

    mgr = MANAGERS[service_id]
    print(f"==> Action: {action.upper()} on service '{mgr.service.name}' [{service_id}]")

    if action == "start":
        res = mgr.start()
        print(res.get("message", ""))
        return 0 if res.get("success", False) else 1
    elif action in ("end", "stop"):
        res = mgr.stop()
        print(res.get("message", ""))
        return 0 if res.get("success", False) else 1
    elif action == "restart":
        res = mgr.restart()
        print(res.get("message", ""))
        return 0 if res.get("success", False) else 1
    elif action == "status":
        status = mgr.get_status()
        print(json.dumps(status, indent=2))
        return 0
    else:
        print(f"ERROR: Unknown action '{action}'. Valid actions: start, restart, end, status.")
        return 1


def manage_fruit(action: str, fruit_id: str) -> int:
    if fruit_id not in FRUITS:
        print(f"ERROR: Unknown fruit ID '{fruit_id}'.")
        print(f"Available fruits: {', '.join(FRUITS.keys())}")
        return 1

    fruit_meta = FRUITS[fruit_id]
    components = fruit_meta.get("components", [])

    print_banner(f"Fruit Operation: {action.upper()} {fruit_meta['name']}")

    if fruit_meta.get("is_android_client", False):
        print(f"[NOTE] {fruit_meta['name']} is an Android client (APK) running on a mobile device or emulator.")
        print("       There is no background Windows daemon process to manage.")
        return 0

    if not components:
        print(f"[NOTE] No background processes registered for {fruit_meta['name']}.")
        return 0

    overall_code = 0
    if action in ("end", "stop"):
        # Stop in reverse order
        for c_id in reversed(components):
            code = manage_single_service("end", c_id)
            if code != 0:
                overall_code = code
    else:
        for c_id in components:
            code = manage_single_service(action, c_id)
            if code != 0:
                overall_code = code

    # If fruit has a static frontend, report it
    if fruit_meta.get("frontend_upstream") and "Static Nginx" in fruit_meta.get("frontend_upstream", ""):
        print(f"[INFO] Frontend for {fruit_meta['name']} is statically hosted by Nginx. Global Nginx is preserved.")

    return overall_code


def manage_all(action: str) -> int:
    print_banner(f"Aggregate Operation: {action.upper()} ALL SERVICES")

    if action == "start":
        res = start_all_services()
        print(json.dumps(res, indent=2))
        return 0 if res["success"] else 1
    elif action in ("end", "stop"):
        res = stop_all_services()
        print(json.dumps(res, indent=2))
        return 0 if res["success"] else 1
    elif action == "restart":
        res = restart_all_services()
        print(json.dumps(res, indent=2))
        return 0 if res["success"] else 1
    elif action == "status":
        statuses = get_all_service_statuses()
        print(json.dumps(statuses, indent=2))
        return 0
    else:
        print(f"ERROR: Unknown aggregate action '{action}'. Valid: start, restart, end, status.")
        return 1


def manage_nginx(action: str) -> int:
    nginx_exe = Path(r"C:\nginx\nginx.exe")
    nginx_conf = Path(r"C:\nginx\conf\nginx.conf")

    if not nginx_exe.exists():
        print(f"ERROR: Nginx executable not found at {nginx_exe}")
        return 1

    if action == "test":
        print("Validating Nginx configuration syntax...")
        res = subprocess.run([str(nginx_exe), "-t", "-p", r"C:\nginx", "-c", str(nginx_conf)], cwd=r"C:\nginx", capture_output=True, text=True)
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    elif action == "reload":
        print("Validating before reload...")
        test_res = subprocess.run([str(nginx_exe), "-t", "-p", r"C:\nginx", "-c", str(nginx_conf)], cwd=r"C:\nginx", capture_output=True, text=True)
        if test_res.returncode != 0:
            print("ERROR: Nginx configuration test failed. Aborting reload.")
            print(test_res.stderr)
            return 1
        print("Reloading Nginx gracefully...")
        res = subprocess.run([str(nginx_exe), "-p", r"C:\nginx", "-s", "reload"], cwd=r"C:\nginx", capture_output=True, text=True)
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    else:
        return manage_single_service(action, "nginx")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.control.manage <action> <service_id>")
        print("  python -m src.control.manage fruit-<action> <fruit_id>")
        print("  python -m src.control.manage all-<action>")
        print("  python -m src.control.manage nginx-<test|reload>")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd.startswith("all-"):
        action = cmd.replace("all-", "")
        code = manage_all(action)
        sys.exit(code)

    if cmd.startswith("fruit-"):
        action = cmd.replace("fruit-", "")
        if len(sys.argv) < 3:
            print("ERROR: Fruit ID required. e.g. python -m src.control.manage fruit-start banana")
            sys.exit(1)
        fruit_id = sys.argv[2].lower()
        code = manage_fruit(action, fruit_id)
        sys.exit(code)

    if cmd.startswith("nginx-"):
        action = cmd.replace("nginx-", "")
        code = manage_nginx(action)
        sys.exit(code)

    if len(sys.argv) < 3:
        print("ERROR: Service ID required. e.g. python -m src.control.manage start mongodb")
        sys.exit(1)

    service_id = sys.argv[2].lower()
    code = manage_single_service(cmd, service_id)
    sys.exit(code)


if __name__ == "__main__":
    main()

