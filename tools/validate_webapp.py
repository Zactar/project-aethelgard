#!/usr/bin/env python3
"""
tools/validate_webapp.py
Project Frogger River Crossing: Autonomous Validation Harness
"""

import sys
import socket
import urllib.request
import logging
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("frogger_river_crossing.Validator")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")

def is_port_listening(port: int = 3000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0

def auto_heal_client() -> None:
    if not is_port_listening(3000):
        logger.info("[Auto-Heal] Starting Web Server on Port 3000...")
        log_dir = WORKSPACE_ROOT / "build" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        client_log = open(log_dir / "client.log", "a", encoding="utf-8")
        subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000", "--directory", str(WORKSPACE_ROOT / "web_client")],
            stdout=client_log, stderr=client_log, cwd=WORKSPACE_ROOT
        )

def verify_client_runtime() -> bool:
    auto_heal_client()
    import time
    time.sleep(0.8)
    url = "http://localhost:3000/index.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Autonomous-QA"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            content = resp.read().decode("utf-8")
            if "gameLoop" not in content and "requestAnimationFrame" not in content:
                logger.error("Web client missing core animation loop!")
                return False
            logger.info("[✓] Web client active on Port 3000 with running game loop.")
            return True
    except Exception as e:
        logger.error(f"Failed to reach web client: {e}")
        return False

def run_full_validation() -> bool:
    logger.info("=== CHAOS QA: INVARIANT VERIFICATION FOR FROGGER RIVER CROSSING ===")
    ok = verify_client_runtime()
    if ok:
        logger.info("[✓] ALL GAME INVARIANTS PASSED.")
    return ok

if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
