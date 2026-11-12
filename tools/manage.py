#!/usr/bin/env python3
"""
tools/manage.py
Project Aethelgard: Unified CLI Control Plane (`aethelgard` alias)
"""

import sys
import os
import json
import signal
import socket
import subprocess
import argparse
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

PID_FILE = WORKSPACE_ROOT / ".studio_pids.json"
LOG_DIR = WORKSPACE_ROOT / "build" / "logs"


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def kill_process_on_port(port: int):
    try:
        res = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        if res.stdout.strip():
            for pid_str in res.stdout.strip().split():
                os.kill(int(pid_str), signal.SIGKILL)
    except Exception:
        try:
            subprocess.run(
                ["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)
        except Exception:
            pass


def cmd_start(args):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pids = {}
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                pids = json.load(f)
        except Exception:
            pids = {}

    # 1. ChromaDB Vector Bus (Port 8000)
    if is_port_open(8000):
        print("[!] ChromaDB daemon is already listening on port 8000.")
    else:
        chroma_log = open(LOG_DIR / "chroma.log", "a", encoding="utf-8")
        chroma_data = WORKSPACE_ROOT / "build" / "chroma"
        chroma_data.mkdir(parents=True, exist_ok=True)
        try:
            chroma_proc = subprocess.Popen(
                [sys.executable, "-m", "chromadb.cli.cli", "run",
                    "--path", str(chroma_data), "--port", "8000"],
                stdout=chroma_log,
                stderr=chroma_log,
                cwd=WORKSPACE_ROOT
            )
            pids["chroma"] = chroma_proc.pid
            print(
                f"[+] Started ChromaDB Vector Bus (PID: {chroma_proc.pid}) on port 8000")
        except Exception as e:
            print(
                f"[!] Warning: Could not auto-start ChromaDB ({e}). Operating in local fallback mode.")

    # 2. WebSocket IPC State Server (Port 8765)
    if is_port_open(8765):
        print("[!] WebSocket IPC Server is already running on port 8765.")
    else:
        server_log = open(LOG_DIR / "server.log", "a", encoding="utf-8")
        server_proc = subprocess.Popen(
            [sys.executable, str(
                WORKSPACE_ROOT / "services" / "agent_runtime" / "src" / "server.py")],
            stdout=server_log,
            stderr=server_log,
            cwd=WORKSPACE_ROOT
        )
        pids["server"] = server_proc.pid
        print(
            f"[+] Started WebSocket Server (PID: {server_proc.pid}) on port 8765")

    # 3. Web Client HTTP Server (Port 3000)
    if is_port_open(3000):
        print("[!] Web Client Server is already running on port 3000.")
    else:
        client_log = open(LOG_DIR / "client.log", "a", encoding="utf-8")
        client_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000",
                "--directory", str(WORKSPACE_ROOT / "web_client")],
            stdout=client_log,
            stderr=client_log,
            cwd=WORKSPACE_ROOT
        )
        pids["client"] = client_proc.pid
        print(
            f"[+] Started Web Client HTTP Server (PID: {client_proc.pid}) on port 3000")

    with open(PID_FILE, "w", encoding="utf-8") as f:
        json.dump(pids, f, indent=2)

    print("\n[✓] Project Aethelgard services initialized.")


def cmd_stop(args):
    pids = {}
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                pids = json.load(f)
        except Exception:
            pids = {}

    for service, pid in pids.items():
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[-] Terminated {service} (PID: {pid})")
        except Exception:
            pass

    PID_FILE.unlink(missing_ok=True)
    kill_process_on_port(8765)
    kill_process_on_port(3000)
    kill_process_on_port(8000)
    print("[✓] All services halted and ports cleared.")


def cmd_restart(args):
    cmd_stop(args)
    cmd_start(args)


def cmd_status(args):
    print("\n[Project Aethelgard Studio Status]")
    print("=" * 60)
    print(
        f" - Web Client (Port 3000):   {'ACTIVE (ONLINE)' if is_port_open(3000) else 'STOPPED (OFFLINE)'}")
    print(
        f" - State Server (Port 8765): {'ACTIVE (ONLINE)' if is_port_open(8765) else 'STOPPED (OFFLINE)'}")
    print(
        f" - ChromaDB Bus (Port 8000): {'ACTIVE (ONLINE)' if is_port_open(8000) else 'STOPPED (OFFLINE)'}")
    print("=" * 60)


def cmd_reset(args):
    staging_dirs = [
        WORKSPACE_ROOT / "build" / "staging" / "rfcs",
        WORKSPACE_ROOT / "build" / "staging" / "meetings"
    ]
    for sdir in staging_dirs:
        if sdir.exists():
            for f in sdir.glob("*.json"):
                f.unlink()
    print("[✓] Staging buffers cleared.")


def cmd_roadmap(args):
    from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
    engine = StudioRoadmapEngine(workspace_root=WORKSPACE_ROOT)

    if getattr(args, "audit", False):
        res = engine.audit_active_milestone()
        print(f"\n[Project Milestone Audit]")
        print("=" * 65)
        print(
            f" Active Version: {res.get('version', 'v0.1.0')} ({res.get('codename', 'Project Milestone')})")
        print(f" Status:         {res.get('status', 'PLANNED')}")
        print(
            f" Burndown:       {res.get('completion_percentage', 0.0)}% [{res.get('verified_deliverables', '0/0')}]")
        print("-" * 65)
        for d in res.get("deliverables", []):
            status_symbol = "[✓]" if d.get("status") == "VERIFIED" else "[ ]"
            print(
                f" {status_symbol} [{d.get('discipline', ''):<10}] {d.get('title')}")
            if d.get("verified_artifact"):
                print(f"      Artifact: {d['verified_artifact']}")
        print("=" * 65)


def cmd_project(args):
    from services.agent_runtime.src.blueprint_planner import BlueprintPlanner
    planner = BlueprintPlanner(workspace_root=WORKSPACE_ROOT)

    if args.subcommand == "status":
        active = planner.get_active_project()
        print("\n[Universal Game Dev Studio - Active Project Status]")
        print("=" * 65)
        if active:
            print(f" Title:        {active.get('title')}")
            print(f" Genre:        {active.get('genre')}")
            print(f" Engine Type:  {active.get('engine_type')}")
            print(f" Project ID:   {active.get('project_id')}")
            print(f" GDD Hash:     {active.get('raw_hash')}")
        else:
            print(" No active project registered.")
        print("=" * 65)

    elif args.subcommand in ("check", "bootstrap"):
        force = getattr(args, "force", False)
        res = planner.check_inbox_and_bootstrap(force=force)
        if res:
            print(f"\n[✓] Bootstrapped project from inbox: '{res.title}' ({res.engine_type})")
        else:
            print("\n[*] No new GDD detected in projects/inbox/GDD.md. (Use --force to re-bootstrap)")


def cmd_auto(args):
    pass  # engine_importer retired
    importer = None
    pass

    runner_script = WORKSPACE_ROOT / "tools" / "autonomous_runner.py"
    if runner_script.exists():
        subprocess.run([sys.executable, str(runner_script),
                       str(args.cycles)], cwd=WORKSPACE_ROOT)


def cmd_retro(args):
    return cmd_retro_and_train(args)


def cmd_project(args):
    """Manages universal project intake and blueprint inspection."""
    from services.agent_runtime.src.blueprint_planner import BlueprintPlanner
    planner = BlueprintPlanner(workspace_root=WORKSPACE_ROOT)

    if args.subcommand == "status":
        active = planner.get_active_project()
        print("\n[Universal Game Dev Studio - Active Project Status]")
        print("=" * 65)
        if active:
            print(f" Title:        {active.get('title')}")
            print(f" Genre:        {active.get('genre')}")
            print(f" Engine Type:  {active.get('engine_type')}")
            print(f" Project ID:   {active.get('project_id')}")
            print(f" GDD Hash:     {active.get('raw_hash')}")
        else:
            print(" No active project registered.")
        print("=" * 65)

    elif args.subcommand == "check":
        res = planner.check_inbox_and_bootstrap()
        if res:
            print(
                f"\n[✓] Bootstrapped NEW project from inbox: '{res.title}' ({res.engine_type})")
        else:
            print("\n[*] No new GDD detected in projects/inbox/GDD.md.")


def cmd_train(args):
    return cmd_retro_and_train(args)


def cmd_budget(args):
    """Displays cumulative Gemini API token usage and spend ledger."""
    ledger_file = WORKSPACE_ROOT / "build" / "staging" / "spend_ledger.json"
    if getattr(args, "reset", False) and ledger_file.exists():
        ledger_file.unlink()
        print("[✓] Reset cumulative spend ledger to $0.00.")
        return
    if not ledger_file.exists():
        print("[Studio Budget] $0.0000 spent (No paid API calls recorded yet).")
        return
    data = json.loads(ledger_file.read_text(encoding="utf-8"))
    print("\n[Aethelgard Virtual Studio - API Spend & Token Ledger]")
    print("=================================================================")
    print(f" Active Model:      {data.get('model', 'gemini-flash-latest')}")
    print(f" Total API Calls:   {data.get('total_calls', 0)} (Disk Cache Hits: {data.get('cache_hits', 0)})")
    print(f" Input Tokens:      {data.get('total_input_tokens', 0):,}")
    print(f" Output Tokens:     {data.get('total_output_tokens', 0):,}")
    print(f" Cumulative Spend:  ${data.get('total_spend_usd', 0.0):.4f} / ${data.get('budget_cap_usd', 1.00):.2f} Hard Cap")
    print("=================================================================\n")


def cmd_retro_and_train(args):
    """Conducts an End-of-Project Post-Mortem & Role Training cycle, updating projects/studio_skill_cards.json."""
    from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
    mem = StudioRetrospectiveMemory(workspace_root=WORKSPACE_ROOT)
    cards = mem.conduct_project_retrospective(use_llm=True)
    print("\n=================================================================")
    print(f" AETHELGARD VIRTUAL STUDIO - POST-MORTEM & ROLE TRAINING (v{cards.get('version', 1)})")
    print("=================================================================")
    history = cards.get("postmortem_history", [])
    if history:
        latest = history[-1]
        print(f" Project Audited:  {latest.get('project')}")
        print(f" Critique:         {latest.get('summary')}")
        print(" Mistakes Fixed:")
        for m in latest.get("mistakes_corrected", []):
            print(f"   * {m}")
    print("-----------------------------------------------------------------")
    print(" Active Discipline Skill Cards (Injected into Next Game):")
    for role, directive in cards.get("role_skill_cards", {}).items():
        print(f"   [{role}]: {directive}")
    print("=================================================================\n")

def main():
    parser = argparse.ArgumentParser(
        description="Project Aethelgard Studio Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)
    p_budget = subparsers.add_parser("budget", help="View or reset LLM API spend ledger")
    p_budget.add_argument("--reset", action="store_true", help="Reset spend ledger to $0.00")
    p_budget.set_defaults(func=cmd_budget)

    p_start = subparsers.add_parser(
        "start", help="Start background runtime services")
    p_start.set_defaults(func=cmd_start)

    p_stop = subparsers.add_parser("stop", help="Stop running services")
    p_stop.set_defaults(func=cmd_stop)

    p_restart = subparsers.add_parser(
        "restart", help="Restart runtime services")
    p_restart.set_defaults(func=cmd_restart)

    p_status = subparsers.add_parser(
        "status", help="Check status of services, ports, and memory")
    p_status.set_defaults(func=cmd_status)

    p_reset = subparsers.add_parser("reset", help="Reset staging buffers")
    p_reset.set_defaults(func=cmd_reset)

    p_roadmap = subparsers.add_parser(
        "roadmap", help="Check studio roadmap status")
    p_roadmap.add_argument("--audit", action="store_true",
                           help="Audit active milestone burndown")
    p_roadmap.add_argument("--advance", action="store_true",
                           help="Evolve to next milestone")
    p_roadmap.set_defaults(func=cmd_roadmap)

    p_auto = subparsers.add_parser(
        "auto", help="Trigger autonomous production cycles")
    p_auto.add_argument("cycles", type=int, nargs="?",
                        default=1, help="Cycle count")
    p_auto.set_defaults(func=cmd_auto)

    p_retro = subparsers.add_parser(
        "retro", help="Inspect retrospective memory ledger")
    p_retro.add_argument("subcommand", nargs="?", default="competency", choices=[
                         "competency", "incidents"])
    p_retro.add_argument("--limit", type=int, default=5,
                         help="Number of records to display")
    p_retro.set_defaults(func=cmd_retro)

    p_train = subparsers.add_parser(
        "train", help="Execute team training cycle across curricula")
    p_train.set_defaults(func=cmd_train)

    p_proj = subparsers.add_parser(
        "project", help="Manage project intake and blueprints")
    p_proj.add_argument("subcommand", choices=[
                        "status", "check", "bootstrap"], default="status", nargs="?")
    p_proj.add_argument("--force", action="store_true",
                        help="Force re-bootstrap from GDD.md")
    p_proj.set_defaults(func=cmd_project)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
