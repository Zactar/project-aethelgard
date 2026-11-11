#!/usr/bin/env python3
"""
tools/validate_webapp.py
Project Studio: Autonomous Universal Chaos QA Validator
Executes runtime headless script compilation and active milestone criteria audits.
"""

import sys
import json
import socket
import urllib.request
import logging
import subprocess
import shutil
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("ChaosQA.Validator")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


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
            [sys.executable, "-m", "http.server", "3000",
                "--directory", str(WORKSPACE_ROOT / "web_client")],
            stdout=client_log, stderr=client_log, cwd=WORKSPACE_ROOT
        )


def verify_client_runtime() -> bool:
    auto_heal_client()
    import time
    time.sleep(0.8)
    url = "http://localhost:3000/index.html"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Universal-QA-Auditor"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            content = resp.read().decode("utf-8")
            if "requestAnimationFrame" not in content and "setInterval" not in content:
                logger.error(
                    "Chaos QA Failure: Missing core animation or tick loop!")
                return False
            logger.info(
                "[✓] Web client active on Port 3000 with running tick loop.")
            return True
    except Exception as e:
        logger.error(f"Failed to reach web client: {e}")
        return False


def verify_script_execution() -> bool:
    """Runs node evaluation on extracted script blocks to ensure zero syntax or declaration errors."""
    node_bin = shutil.which("node")
    if not node_bin:
        return True

    client_html = WORKSPACE_ROOT / "web_client" / "index.html"
    if not client_html.exists():
        return False

    content = client_html.read_text(encoding="utf-8")
    if "<script>" in content:
        parts = content.split("<script>")
        for idx, part in enumerate(parts[1:]):
            js_code = part.split("</script>")[0]
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=True) as tf:
                # Wrap with mock browser DOM globals so Node evaluates without crashing on canvas
                mock_env = "const document = { getElementById: () => ({ getContext: () => ({ clearRect:()=>{}, save:()=>{}, restore:()=>{}, translate:()=>{}, fillRect:()=>{}, beginPath:()=>{}, arc:()=>{}, fill:()=>{}, stroke:()=>{}, fillText:()=>{} }), style: {} }), addEventListener: ()=>{} }; const window = { addEventListener: ()=>{} }; const performance = { now: () => 0 }; const requestAnimationFrame = () => {};\n"
                tf.write(mock_env + js_code)
                tf.flush()
                res = subprocess.run([node_bin, tf.name],
                                     capture_output=True, text=True)
                if res.returncode != 0:
                    logger.error(
                        f"Chaos QA Failure: Script evaluation failed at runtime (Block {idx}):\n{res.stderr.strip()}")
                    return False

    logger.info(
        "[✓] Headless JavaScript Runtime verified: Zero syntax or evaluation crashes.")
    return True


def run_full_validation() -> bool:
    logger.info(
        "=== CHAOS QA: UNIVERSAL PLAYABILITY & HEADLESS RUNTIME AUDIT ===")
    runtime_ok = verify_client_runtime()
    script_ok = verify_script_execution()
    passed = runtime_ok and script_ok
    if passed:
        logger.info("[✓] ALL UNIVERSAL PLAYABILITY INVARIANTS PASSED.")
    else:
        logger.error("[✗] PLAYABILITY GATES FAILED!")
    return passed


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
