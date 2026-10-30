#!/usr/bin/env python3
"""
PROJECT AETHELGARD: UNIFIED STUDIO & RUNTIME PROCESS MANAGER
Handles automated daemon startup, shutdown, health monitoring, workspace resets,
sprint dispatch, RFC deployment pipelines, roadmap tracking, and release packaging.
"""

import argparse
import json
import os
from pathlib import Path
import py_compile
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
PID_FILE = ROOT_DIR / ".studio_pids.json"
STAGING_DIR = ROOT_DIR / "build" / "staging"
WEB_DIR = ROOT_DIR / "web_client"

PORTS = {
    "chromadb": 8000,
    "state_ipc": 8765,
    "web_client": 3000
}


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def load_pids() -> dict:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_pids(pids: dict):
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def kill_port_owner(port: int):
    subprocess.run(
        f"fuser -k -9 {port}/tcp 2>/dev/null || true",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    subprocess.run(
        f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.3)


def check_chroma_health() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v2/heartbeat")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def check_client_health() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:3000/")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


# ==============================================================================
# ACTIONS
# ==============================================================================

def cmd_status():
    print("\n" + "=" * 65)
    print("        PROJECT AETHELGARD: SERVICE HEALTH & RUNTIME STATUS        ")
    print("=" * 65)

    chroma_ok = check_chroma_health()
    ipc_ok = is_port_open(PORTS["state_ipc"])
    client_ok = check_client_health()
    pids = load_pids()

    print(f"{'Service':<22} | {'Port':<6} | {'Status':<12} | {'Details'}")
    print("-" * 65)

    status_chroma = "HEALTHY" if chroma_ok else "OFFLINE"
    print(
        f"{'ChromaDB Vector Store':<22} | {PORTS['chromadb']:<6} | {status_chroma:<12} | Docker container: aethelgard-chroma")

    status_ipc = "ONLINE" if ipc_ok else "OFFLINE"
    pid_ipc = pids.get("state_ipc", "N/A")
    print(
        f"{'WebSocket State Server':<22} | {PORTS['state_ipc']:<6} | {status_ipc:<12} | PID: {pid_ipc} (ws://0.0.0.0:8765)")

    status_client = "ONLINE" if client_ok else "OFFLINE"
    pid_client = pids.get("web_client", "N/A")
    print(
        f"{'Three.js Client Host':<22} | {PORTS['web_client']:<6} | {status_client:<12} | PID: {pid_client} (http://localhost:3000)")

    print("=" * 65)

    manifest_file = WEB_DIR / "game_runtime_manifest.json"
    manifest_state = "DEPLOYED" if manifest_file.exists() else "MISSING"
    print(f"Game Runtime Manifest  : {manifest_state} ({manifest_file})")

    staged_count = len(list(STAGING_DIR.glob("*.json"))
                       ) if STAGING_DIR.exists() else 0
    print(f"Staged Studio Artifacts: {staged_count} pending ingestion")
    print("=" * 65 + "\n")


def cmd_stop():
    print("[STOP]: Terminating running Aethelgard studio services...")
    pids = load_pids()

    for name, pid in pids.items():
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"  [STOPPED] {name} (PID: {pid})")
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"  [WARNING] Could not kill {name} ({pid}): {e}")

    for name, port in PORTS.items():
        if name != "chromadb":
            kill_port_owner(port)

    PID_FILE.unlink(missing_ok=True)
    print("[STOP]: State IPC server and HTTP client stopped.")


def cmd_start():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pids = {}

    print("[START]: Launching studio infrastructure...")

    if not check_chroma_health():
        print("  [DOCKER]: Starting ChromaDB vector database...")
        subprocess.run(["docker", "compose", "up", "-d"],
                       cwd=ROOT_DIR, check=True)
        for _ in range(12):
            if check_chroma_health():
                break
            time.sleep(0.5)

    if check_chroma_health():
        print("  [OK] ChromaDB v2 ready on port 8000.")
    else:
        print("  [WARNING] ChromaDB did not reply on /api/v2/heartbeat in time.")

    kill_port_owner(PORTS["state_ipc"])
    kill_port_owner(PORTS["web_client"])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        ROOT_DIR) + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")

    server_script = ROOT_DIR / "services" / "agent_runtime" / "src" / "server.py"
    server_log = open(LOG_DIR / "server.log", "w", encoding="utf-8")
    server_proc = subprocess.Popen(
        [sys.executable, "-u", str(server_script)],
        cwd=ROOT_DIR,
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT
    )
    pids["state_ipc"] = server_proc.pid

    client_log = open(LOG_DIR / "client.log", "w", encoding="utf-8")
    client_proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "http.server",
            "3000", "--directory", "web_client"],
        cwd=ROOT_DIR,
        env=env,
        stdout=client_log,
        stderr=subprocess.STDOUT
    )
    pids["web_client"] = client_proc.pid

    save_pids(pids)

    ipc_ready = False
    client_ready = False
    for _ in range(20):
        if not ipc_ready and is_port_open(PORTS["state_ipc"]):
            ipc_ready = True
        if not client_ready and is_port_open(PORTS["web_client"]):
            client_ready = True
        if ipc_ready and client_ready:
            break
        if server_proc.poll() is not None:
            break
        time.sleep(0.3)

    if server_proc.poll() is not None or not ipc_ready:
        print(
            f"  [ERROR]: State Server (port 8765) failed to start! (Exit code: {server_proc.poll()})")
        server_log.flush()
        err_text = (
            LOG_DIR / "server.log").read_text(encoding="utf-8", errors="replace")
        print(
            f"--- [logs/server.log] ---\n{err_text.strip()}\n-------------------------")
    else:
        print("  [OK] State Server active on port 8765 (PID: %d)" %
              server_proc.pid)

    if client_proc.poll() is not None or not client_ready:
        print(
            f"  [ERROR]: Web Client (port 3000) failed to start! (Exit code: {client_proc.poll()})")
        client_log.flush()
        err_text = (
            LOG_DIR / "client.log").read_text(encoding="utf-8", errors="replace")
        print(
            f"--- [logs/client.log] ---\n{err_text.strip()}\n-------------------------")
    else:
        print("  [OK] Web Client active on port 3000 (PID: %d)" %
              client_proc.pid)

    cmd_status()


def cmd_reset():
    print("[RESET]: Performing full workspace reset...")
    cmd_stop()

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        print("  [CLEANED]: build/staging/ cleared.")

    for log_file in LOG_DIR.glob("*.log"):
        log_file.unlink()
    print("  [CLEANED]: logs/ cleared.")

    targets = [
        "schemas/studio_contracts.py",
        "services/agent_runtime/src/virtual_studio_engine.py",
        "services/agent_runtime/src/team_sync.py",
        "services/agent_runtime/src/change_request_engine.py",
        "services/agent_runtime/src/autonomous_authoring.py",
        "services/agent_runtime/src/roadmap_engine.py",
        "services/agent_runtime/src/optimization_engine.py",
        "services/agent_runtime/src/server.py",
        "tools/engine_importer.py",
        "tools/release_packager.py",
        "tools/rfc_pipeline.py",
        "tools/autonomous_runner.py",
        "tools/manage.py"
    ]
    print("\n[VERIFIER]: Compiling bytecode across all production files...")
    for t in targets:
        py_compile.compile(str(ROOT_DIR / t), doraise=True)
        print(f"  [BYTECODE VERIFIED]: {t}")

    print("\n[SEEDING]: Generating clean baseline runtime manifest...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        ROOT_DIR) + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")
    subprocess.run(
        [sys.executable, "tools/autonomous_runner.py",
            "--cycles", "1", "--delay", "0"],
        cwd=ROOT_DIR,
        env=env,
        check=True
    )

    cmd_start()


def cmd_rfc(extra_args: list):
    rfc_script = ROOT_DIR / "tools" / "rfc_pipeline.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        ROOT_DIR) + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")
    subprocess.run([sys.executable, str(rfc_script)] +
                   extra_args, cwd=ROOT_DIR, env=env)


def cmd_sprint(extra_args: list):
    runner_script = ROOT_DIR / "tools" / "autonomous_runner.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        ROOT_DIR) + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")
    cmd = [sys.executable, str(runner_script)]
    if not extra_args:
        cmd += ["--cycles", "3", "--cadence", "2", "--delay", "0.05"]
    else:
        cmd += extra_args
    print(f"[SPRINT]: Launching autonomous development sprint...")
    subprocess.run(cmd, cwd=ROOT_DIR, env=env)


def cmd_roadmap():
    from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
    engine = StudioRoadmapEngine()
    milestones = engine.load_roadmap()

    print("\n" + "=" * 70)
    print("             PROJECT AETHELGARD: ACTIVE STUDIO ROADMAP              ")
    print("=" * 70)
    for m in milestones:
        status_val = m.status.value if hasattr(
            m.status, "value") else str(m.status)
        print(f"▶ Milestone {m.version_tag}: {m.theme} [{status_val}]")
        for epic in m.epics:
            chk = "[x]" if epic.is_completed else "[ ]"
            biome_val = epic.target_biome.value if hasattr(
                epic.target_biome, "value") else str(epic.target_biome)
            print(f"    {chk} {epic.title} ({biome_val})")
    print("=" * 70 + "\n")


def cmd_release():
    release_script = ROOT_DIR / "tools" / "release_packager.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        ROOT_DIR) + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")
    subprocess.run([sys.executable, str(release_script)],
                   cwd=ROOT_DIR, env=env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Project Aethelgard Studio Process Manager")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status",
                 "reset", "rfc", "sprint", "roadmap", "release"],
        help="Action to execute"
    )
    parser.add_argument("extra_args", nargs=argparse.REMAINDER,
                        help="Arguments passed to sub-tools")
    args = parser.parse_args()

    if args.action == "start":
        cmd_start()
    elif args.action == "stop":
        cmd_stop()
    elif args.action == "restart":
        cmd_stop()
        time.sleep(1.0)
        cmd_start()
    elif args.action == "status":
        cmd_status()
    elif args.action == "reset":
        cmd_reset()
    elif args.action == "rfc":
        cmd_rfc(args.extra_args)
    elif args.action == "sprint":
        cmd_sprint(args.extra_args)
    elif args.action == "roadmap":
        cmd_roadmap()
    elif args.action == "release":
        cmd_release()
