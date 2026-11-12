"""
Central Service Registry for Basket Operations Control Center.
Single source of truth for all manageable services, instances, and fruits.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

# Base Paths
BASKET_ROOT = Path(r"C:\Users\ADMIN\OneDrive\CODES\Projects\Projects\Basket")
INFRA_DIR = BASKET_ROOT / "infrastructure"
LOGS_DIR = INFRA_DIR / "logs"
RUN_DIR = INFRA_DIR / "run"

@dataclass
class ServiceDef:
    id: str
    name: str
    category: str  # 'infrastructure' | 'fruit' | 'database' | 'llm' | 'speech' | 'proxy' | 'control'
    description: str
    work_dir: Optional[str]
    command: List[str]
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = None
    env: Optional[Dict[str, str]] = None
    custom_stop: Optional[List[str]] = None
    
    # Process matching rules
    match_exe_names: List[str] = field(default_factory=list)
    match_cmdline_contains: List[str] = field(default_factory=list)
    match_ports: List[int] = field(default_factory=list)
    
    # Windows Task Scheduler
    task_scheduler_task: Optional[str] = None
    
    # Health check definition
    health_type: str = "http"  # 'http' | 'tcp' | 'cmd'
    health_url: Optional[str] = None
    health_port: Optional[int] = None
    
    # Dependencies & Priorities
    dependencies: List[str] = field(default_factory=list)
    startup_priority: int = 50
    shutdown_priority: int = 50
    
    # Metadata
    fruit_id: Optional[str] = None
    is_fruit_component: bool = False
    is_static_only: bool = False


SERVICES: Dict[str, ServiceDef] = {
    # ----------------------------------------------------
    # BASKET CONTROL & DASHBOARD
    # ----------------------------------------------------
    "basket-control": ServiceDef(
        id="basket-control",
        name="Basket Operations Dashboard & Control Service",
        category="control",
        description="Local operations backend and web dashboard for Basket and the Fruits ecosystem.",
        work_dir=str(BASKET_ROOT),
        command=[str(BASKET_ROOT / ".venv" / "Scripts" / "python.exe"), "run_control.py"],
        host="127.0.0.1",
        port=10020,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["run_control.py"],
        match_ports=[10020],
        health_type="tcp",
        health_port=10020,
        dependencies=[],
        startup_priority=60,
        shutdown_priority=20,
    ),

    # ----------------------------------------------------
    # BASKET CORE BACKEND API
    # ----------------------------------------------------
    "basket-api": ServiceDef(
        id="basket-api",
        name="Basket Core API Gateway",
        category="infrastructure",
        description="Core FastAPI AI backend, LLM router, STT/TTS gateway, and Quince MCP host.",
        work_dir=str(BASKET_ROOT),
        command=[str(BASKET_ROOT / ".venv" / "Scripts" / "python.exe"), "run.py"],
        host="127.0.0.1",
        port=10010,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["run.py"],
        match_ports=[10010],
        task_scheduler_task="Basket Server",
        health_type="http",
        health_url="http://127.0.0.1:10010/docs",
        health_port=10010,
        dependencies=["mongodb", "llm-llama"],
        startup_priority=30,
        shutdown_priority=60,
    ),

    # ----------------------------------------------------
    # NGINX REVERSE PROXY
    # ----------------------------------------------------
    "nginx": ServiceDef(
        id="nginx",
        name="Nginx Reverse Proxy",
        category="proxy",
        description="Local edge reverse proxy hosting *.jam SSL routes for the entire ecosystem.",
        work_dir=r"C:\nginx",
        command=["powershell.exe", "-NoProfile", "-Command", "Start-ScheduledTask -TaskName 'Start Enginx'"],
        custom_stop=["powershell.exe", "-NoProfile", "-Command", "Stop-ScheduledTask -TaskName 'Start Enginx'; Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue"],
        host="127.0.0.1",
        port=80,
        match_exe_names=["nginx.exe"],
        match_ports=[80, 443],
        task_scheduler_task="Start Enginx",
        health_type="http",
        health_url="http://127.0.0.1:80",
        health_port=80,
        dependencies=[],
        startup_priority=55,
        shutdown_priority=30,
    ),

    # ----------------------------------------------------
    # MONGODB (BASKET SUITE DATABASE)
    # Single unified database server for Basket & all Fruits
    # ----------------------------------------------------
    "mongodb": ServiceDef(
        id="mongodb",
        name="Basket MongoDB Database (Basket Suite)",
        category="database",
        description="Unified MongoDB instance for Basket and all Fruits ecosystem applications.",
        work_dir=r"C:\project-data\basket",
        command=["mongod", "--port", "10000", "--dbpath", r"C:\project-data\basket"],
        host="127.0.0.1",
        port=10000,
        match_exe_names=["mongod.exe"],
        match_cmdline_contains=["10000", "project-data\\basket"],
        match_ports=[10000],
        health_type="tcp",
        health_port=10000,
        dependencies=[],
        startup_priority=10,
        shutdown_priority=90,
    ),

    # ----------------------------------------------------
    # QUINCE LLM (llama.cpp CUDA)
    # ----------------------------------------------------
    "llm-llama": ServiceDef(
        id="llm-llama",
        name="Quince LLM (llama.cpp CUDA)",
        category="llm",
        description="GPU-accelerated local Qwen3.5-4B inference server for Quince and Basket.",
        work_dir=r"C:\llama-cuda",
        command=[
            r"C:\llama-cuda\llama-server.exe",
            "-m", r"C:\Users\ADMIN\models\Qwen3.5-4B-Q4_K_M\Qwen3.5-4B.Q4_K_M.gguf",
            "--mmproj", r"C:\Users\ADMIN\models\Qwen3.5-4B-Q4_K_M\mmproj-Qwen3.5-4B-BF16.gguf",
            "--alias", "quince-llm",
            "--host", "127.0.0.1",
            "--port", "10030",
            "--ctx-size", "16000",
            "--parallel", "1",
            "--n-gpu-layers", "99",
            "--cache-type-k", "q8_0",
            "--cache-type-v", "q8_0",
            "--jinja",
            "--flash-attn", "auto"
        ],
        host="127.0.0.1",
        port=10030,
        match_exe_names=["llama-server.exe"],
        match_cmdline_contains=["quince-llm", "10030"],
        match_ports=[10030],
        health_type="http",
        health_url="http://127.0.0.1:10030/health",
        health_port=10030,
        dependencies=[],
        startup_priority=20,
        shutdown_priority=75,
    ),

    # ----------------------------------------------------
    # STT: QWEN3-ASR (SPEECH-TO-TEXT)
    # ----------------------------------------------------
    "stt-qwen": ServiceDef(
        id="stt-qwen",
        name="Qwen3-ASR (Speech-to-Text)",
        category="speech",
        description="CPU-based llama.cpp automatic speech recognition runtime for Basket voice input.",
        work_dir=str(BASKET_ROOT),
        command=[
            r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe",
            "-m", r"C:\Users\ADMIN\models\qwen3-asr-0.6b-q4\Qwen3-ASR-0.6B.Q4_K_M.gguf",
            "--mmproj", r"C:\Users\ADMIN\models\qwen3-asr-0.6b-q4\Qwen3-ASR-0.6B.mmproj-Q8_0.gguf",
            "--host", "127.0.0.1",
            "--port", "10040",
            "-ngl", "0",
            "--mmproj-device", "none",
            "-c", "4096"
        ],
        host="127.0.0.1",
        port=10040,
        match_exe_names=["llama-server.exe"],
        match_cmdline_contains=["10040", "qwen3-asr"],
        match_ports=[10040],
        health_type="http",
        health_url="http://127.0.0.1:10040/health",
        health_port=10040,
        dependencies=[],
        startup_priority=25,
        shutdown_priority=70,
    ),

    # ----------------------------------------------------
    # TTS: POCKET TTS (TEXT-TO-SPEECH)
    # ----------------------------------------------------
    "tts-pocket": ServiceDef(
        id="tts-pocket",
        name="Pocket TTS (Text-to-Speech)",
        category="speech",
        description="Lightweight local streaming text-to-speech server for Basket voice output.",
        work_dir=r"C:\pocket-tts",
        command=[r"C:\pocket-tts\.venv\Scripts\pocket-tts.exe", "serve", "--host", "127.0.0.1", "--port", "10050"],
        host="127.0.0.1",
        port=10050,
        match_exe_names=["pocket-tts.exe", "python.exe"],
        match_cmdline_contains=["pocket-tts"],
        match_ports=[10050],
        health_type="tcp",
        health_port=10050,
        dependencies=[],
        startup_priority=28,
        shutdown_priority=68,
    ),

    # ----------------------------------------------------
    # FRUIT: BANANA
    # ----------------------------------------------------
    "fruit-banana": ServiceDef(
        id="fruit-banana",
        name="Banana Media Utility Backend",
        category="fruit",
        fruit_id="banana",
        description="FastAPI media downloader, audio trimmer, and algorithmic music similarity engine.",
        work_dir=str(BASKET_ROOT / "fruits" / "banana" / "server"),
        command=[str(BASKET_ROOT / "fruits" / "banana" / "server" / ".venv" / "Scripts" / "python.exe"), "run.py", "--no-reload"],
        host="127.0.0.4",
        port=10000,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["fruits\\banana", "run.py"],
        match_ports=[10000],
        task_scheduler_task="Banana Backend",
        health_type="http",
        health_url="http://127.0.0.4:10000/api",
        health_port=10000,
        dependencies=[],
        startup_priority=40,
        shutdown_priority=50,
        is_fruit_component=True,
    ),

    # ----------------------------------------------------
    # FRUIT: KIWI
    # ----------------------------------------------------
    "fruit-kiwi": ServiceDef(
        id="fruit-kiwi",
        name="Kiwi File Converter Backend",
        category="fruit",
        fruit_id="kiwi",
        description="Offline-first document, image, audio, and archive format conversion engine.",
        work_dir=str(BASKET_ROOT / "fruits" / "kiwi" / "server"),
        command=[str(BASKET_ROOT / "fruits" / "kiwi" / "server" / ".venv" / "Scripts" / "python.exe"), "run.py"],
        host="127.0.0.3",
        port=10000,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["fruits\\kiwi", "run.py"],
        match_ports=[10000],
        task_scheduler_task="Kiwi Backend",
        health_type="http",
        health_url="http://127.0.0.3:10000/docs",
        health_port=10000,
        dependencies=[],
        startup_priority=42,
        shutdown_priority=48,
        is_fruit_component=True,
    ),

    # ----------------------------------------------------
    # FRUIT: PLUM BACKEND
    # ----------------------------------------------------
    "fruit-plum-backend": ServiceDef(
        id="fruit-plum-backend",
        name="Plum Email Assistant Server",
        category="fruit",
        fruit_id="plum",
        description="Node.js/Express server providing email synchronization, auth, and WebSocket chat.",
        work_dir=str(BASKET_ROOT / "fruits" / "plum" / "server"),
        command=["node", "dist/index.js"],
        host="127.0.0.2",
        port=10000,
        match_exe_names=["node.exe"],
        match_cmdline_contains=["fruits\\plum", "dist\\index.js"],
        match_ports=[10000, 10010],
        health_type="tcp",
        health_port=10000,
        dependencies=["mongodb", "basket-api"],
        startup_priority=44,
        shutdown_priority=46,
        is_fruit_component=True,
    ),

    # ----------------------------------------------------
    # FRUIT: QUINCE SERVER
    # ----------------------------------------------------
    "fruit-quince-server": ServiceDef(
        id="fruit-quince-server",
        name="Quince Voice Assistant Server",
        category="fruit",
        fruit_id="quince",
        description="Local push-to-talk voice companion and text runner connected to Basket Core.",
        work_dir=str(BASKET_ROOT / "fruits" / "quince"),
        command=[str(BASKET_ROOT / "fruits" / "quince" / ".venv" / "Scripts" / "python.exe"), "run.py", "--no-input"],
        host="127.0.0.5",
        port=10000,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["fruits\\quince", "run.py"],
        match_ports=[10000],
        health_type="http",
        health_url="http://127.0.0.5:10000/",
        health_port=10000,
        dependencies=["basket-api"],
        startup_priority=46,
        shutdown_priority=44,
        is_fruit_component=True,
    ),

    # ----------------------------------------------------
    # FRUIT: QUINCE MCP
    # ----------------------------------------------------
    "fruit-quince-mcp": ServiceDef(
        id="fruit-quince-mcp",
        name="Quince MCP Server",
        category="fruit",
        fruit_id="quince",
        description="Hierarchical Model Context Protocol server providing system controls and agentic bridge.",
        work_dir=str(BASKET_ROOT / "fruits" / "quince"),
        command=[str(BASKET_ROOT / "fruits" / "quince" / ".venv" / "Scripts" / "python.exe"), "run_mcp.py", "--host", "127.0.0.5", "--port", "10010"],
        host="127.0.0.5",
        port=10010,
        match_exe_names=["python.exe"],
        match_cmdline_contains=["fruits\\quince", "run_mcp.py"],
        match_ports=[10010],
        health_type="tcp",
        health_port=10010,
        dependencies=[],
        startup_priority=48,
        shutdown_priority=42,
        is_fruit_component=True,
    ),
}

# Fruits Metadata Directory
FRUITS: Dict[str, Dict[str, Any]] = {
    "banana": {
        "id": "banana",
        "name": "Banana",
        "tagline": "Fast, Private Media Utility & Music Discovery Engine",
        "icon": "/icons/banana-icon.svg",
        "category": "Media & Audio",
        "frontend_url": "https://banana.jam",
        "frontend_upstream": "fruits/banana/client/dist (Static Nginx)",
        "api_url": "https://api.banana.jam",
        "api_upstream": "http://127.0.0.4:10000",
        "ws_url": None,
        "is_redirector_enabled": True,
        "is_android_client": False,
        "components": ["fruit-banana"],
    },
    "plum": {
        "id": "plum",
        "name": "Plum",
        "tagline": "Personal Intelligent Email Assistant",
        "icon": "/icons/plum-icon.svg",
        "category": "Email & Productivity",
        "frontend_url": "https://plum.jam",
        "frontend_upstream": "fruits/plum/client/dist (Static Nginx)",
        "api_url": "https://api.plum.jam",
        "api_upstream": "http://127.0.0.2:10000",
        "ws_url": "wss://plum.jam/ws",
        "ws_upstream": "http://127.0.0.2:10010",
        "is_redirector_enabled": True,
        "is_android_client": False,
        "components": ["fruit-plum-backend"],
    },
    "kiwi": {
        "id": "kiwi",
        "name": "Kiwi",
        "tagline": "Offline-first File Conversion & Utility Workspace",
        "icon": "/icons/kiwi-icon.svg",
        "category": "Files & Format Tools",
        "frontend_url": "https://kiwi.jam",
        "frontend_upstream": "fruits/kiwi/client/dist (Static Nginx)",
        "api_url": "https://api.kiwi.jam",
        "api_upstream": "http://127.0.0.3:10000",
        "ws_url": None,
        "is_redirector_enabled": True,
        "is_android_client": False,
        "components": ["fruit-kiwi"],
    },
    "quince": {
        "id": "quince",
        "name": "Quince",
        "tagline": "Local Voice Assistant & Windows System MCP Server",
        "icon": None,
        "category": "System & Voice Runtime",
        "frontend_url": "https://quince.jam",
        "frontend_upstream": "fruits/quince/client/dist (Static Nginx)",
        "api_url": "https://api.quince.jam",
        "api_upstream": "http://127.0.0.5:10000",
        "mcp_url": "https://mcp.quince.jam",
        "mcp_upstream": "http://127.0.0.5:10010",
        "ws_url": None,
        "is_redirector_enabled": True,
        "is_android_client": False,
        "components": ["fruit-quince-server", "fruit-quince-mcp"],
    },
    "lemon": {
        "id": "lemon",
        "name": "Lemon",
        "tagline": "Quiet, Private Android Self-Control & Local DNS Workspace",
        "icon": "/icons/lemon-icon.svg",
        "category": "Mobile & Security",
        "frontend_url": "https://lemon.jam",
        "frontend_upstream": "fruits/lemon/client/dist (Static Nginx)",
        "api_url": "https://api.lemon.jam",
        "api_upstream": "http://127.0.0.6:10000",
        "ws_url": None,
        "is_redirector_enabled": True,
        "is_android_client": True,
        "components": [],
    },
    "cherry": {
        "id": "cherry",
        "name": "Cherry",
        "tagline": "Ecosystem Workspace Module",
        "icon": "/icons/basket-icon.svg",
        "category": "Modular Project",
        "frontend_url": "https://cherry.jam",
        "frontend_upstream": "fruits/cherry/client/dist (Static Nginx)",
        "api_url": "https://api.cherry.jam",
        "api_upstream": "http://127.0.0.7:10000",
        "ws_url": None,
        "is_redirector_enabled": True,
        "is_android_client": False,
        "components": [],
    },
}

