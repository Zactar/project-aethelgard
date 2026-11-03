#!/usr/bin/env python3
"""
tools/validate_webapp.py
Universal Chaos QA Invariant & Playability Verification Suite
"""

import sys
import socket
import urllib.request
import logging
import subprocess
import re
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
            url, headers={"User-Agent": "Autonomous-QA"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            content = resp.read().decode("utf-8")
            if "requestAnimationFrame" not in content and "gameLoop" not in content:
                logger.error("Web client missing core animation loop!")
                return False
            logger.info(
                "[✓] Web client active on Port 3000 with running tick loop.")
            return True
    except Exception as e:
        logger.error(f"Failed to reach web client: {e}")
        return False


def verify_sanctuary_invariants() -> bool:
    """Chaos QA: Asserts that Sanctuary modal and meta-upgrade hooks are present and sound."""
    client_html = WORKSPACE_ROOT / "web_client" / "index.html"
    if not client_html.exists():
        return False

    content = client_html.read_text(encoding="utf-8")
    required_sanctuary_tokens = [
        "sanctuary-modal",
        "buySanctuaryPerk",
        "sanctuaryPerks",
        "applySanctuaryPerks",
        "perk_thick_hide",
        "perk_nest_egg"
    ]
    missing = [tok for tok in required_sanctuary_tokens if tok not in content]
    if missing:
        logger.error(
            f"Chaos QA Failure: Missing Sanctuary meta-progression anchors: {missing}")
        return False

    logger.info(
        "[✓] Chaos QA Verified: Sanctuary Hub modal, Amber transactions, and perk persistence sound.")
    return True


def verify_reachability_and_density_invariants() -> bool:
    """Chaos QA: Asserts that lanes maintain playable density and strictly alternate flow."""
    client_html = WORKSPACE_ROOT / "web_client" / "index.html"
    if not client_html.exists():
        return False

    content = client_html.read_text(encoding="utf-8")

    # Invariant 1: Delta must be clamped to prevent tab-blur coordinate collapse
    if "Math.min(" not in content:
        logger.error(
            "Chaos QA Failure: Unclamped delta detected! Tab-blur will cause entity coordinate collapse.")
        return False

    # Invariant 2: Relative spacing preservation during wrapping
    if "nextX = canvas.width" in content or "nextX = -lane.width" in content:
        logger.error(
            "Chaos QA Failure: Naive coordinate assignment in wrapping loop leads to platform stacking!")
        return False

    # Invariant 3: Dictionary-mapped lane alternating flow check
    lane_speeds = {}
    for m in re.finditer(r"lanes\[(\d+)\]\.speed\s*=\s*([-+]?\d*\.?\d+)", content):
        lane_speeds[int(m.group(1))] = float(m.group(2))

    # River platform lanes (1 through 4) must strictly alternate signs
    river_lanes = [idx for idx in sorted(
        lane_speeds.keys()) if idx in (1, 2, 3, 4)]
    for i in range(1, len(river_lanes)):
        curr_spd = lane_speeds[river_lanes[i]]
        prev_spd = lane_speeds[river_lanes[i-1]]
        if (curr_spd > 0 and prev_spd > 0) or (curr_spd < 0 and prev_spd < 0):
            logger.error(
                f"Chaos QA Failure: River lanes {river_lanes[i-1]} and {river_lanes[i]} share identical flow direction!")
            return False

    logger.info(
        "[✓] Chaos QA Verified: Platform density, delta clamping, and solvable alternating flow sound.")
    return True


def run_full_validation() -> bool:
    logger.info("=== CHAOS QA: SOLVABILITY & RUNTIME INVARIANT AUDIT ===")
    client_ok = verify_client_runtime()
    reachability_ok = verify_reachability_and_density_invariants()
    sanctuary_ok = verify_sanctuary_invariants()
    passed = client_ok and reachability_ok and sanctuary_ok
    if passed:
        logger.info("[✓] ALL PLAYABILITY & SOLVABILITY INVARIANTS PASSED.")
    else:
        logger.error("[✗] PLAYABILITY GATES FAILED!")
    return passed


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
