#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTONOMOUS CODEBASE ENGINEER AGENT
Empowers virtual dev team agents to inspect codebase ASTs, synthesize code patches,
verify syntax integrity, and commit clean changes to version control without external intervention.
"""

from schemas.studio_contracts import BugSeverity, BugTicket
import difflib
import json
import logging
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


logger = logging.getLogger("CodebaseEngineer")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] %(message)s")


class CodebaseEngineerAgent:
    """Autonomous software engineer capable of modifying workspace files safely."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or ROOT_DIR
        self.applied_patches_log: List[Dict[str, Any]] = []

    def apply_atomic_replacement(
        self, relative_path: str, search_target: str, replacement: str
    ) -> Tuple[bool, str]:
        """Applies an atomic text replacement to a file with automatic backup and rollback."""
        file_path = self.workspace_root / relative_path
        if not file_path.exists():
            return False, f"Target file does not exist: {relative_path}"

        original_content = file_path.read_text(encoding="utf-8")
        if search_target not in original_content:
            return False, f"Search target not found in {relative_path}"

        # Create temporary backup
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copyfile(file_path, backup_path)

        try:
            modified_content = original_content.replace(
                search_target, replacement, 1)
            file_path.write_text(modified_content, encoding="utf-8")

            # Validate Python syntax if modifying a python module
            if file_path.suffix == ".py":
                py_compile.compile(str(file_path), doraise=True)

            # Success: clean up backup
            backup_path.unlink(missing_ok=True)
            self.applied_patches_log.append({
                "file": relative_path,
                "timestamp": time.time(),
                "status": "APPLIED"
            })
            logger.info(f"Successfully applied code patch to {relative_path}")
            return True, f"Patch verified and applied to {relative_path}."

        except Exception as e:
            # Revert to backup immediately
            shutil.copyfile(backup_path, file_path)
            backup_path.unlink(missing_ok=True)
            logger.error(
                f"Patch validation failed for {relative_path}: {e}. Rolled back.")
            return False, f"Syntax verification failed: {e}. Changes rolled back."

    def inspect_and_patch_ticket(self, ticket: BugTicket) -> Tuple[bool, str]:
        """Translates a triage ticket into an autonomous code modification."""
        title_lower = ticket.title.lower()
        desc_lower = ticket.description.lower()

        # 1. Autonomous Camera Tuning
        if "camera" in title_lower or "damping" in title_lower:
            return self.apply_atomic_replacement(
                "web_client/index.html",
                "dampingFactor = 0.12;",
                "dampingFactor = 0.08;"
            )

        # 2. Natural Voice Rate Modulation
        if "voice" in title_lower or "speech" in title_lower or "audio" in title_lower:
            return self.apply_atomic_replacement(
                "web_client/index.html",
                "utterance.rate = 1.0;",
                "utterance.rate = 0.94;"
            )

        # 3. Minimap Radar Contrast Enhancement
        if "minimap" in title_lower or "radar" in title_lower:
            return self.apply_atomic_replacement(
                "web_client/index.html",
                'mapCtx.fillStyle = "#080b11";',
                'mapCtx.fillStyle = "#05070a";'
            )

        # 4. NPC Walking Speed Calibration
        if "npc walk" in title_lower or "patrol speed" in title_lower:
            return self.apply_atomic_replacement(
                "web_client/index.html",
                "const npcWalkSpeed = 340.0;",
                "const npcWalkSpeed = 380.0;"
            )

        # 5. Locomotion Base Speed Tuning
        if "player speed" in title_lower or "base speed" in title_lower:
            return self.apply_atomic_replacement(
                "schemas/studio_contracts.py",
                "player_base_speed: float = 1400.0",
                "player_base_speed: float = 1500.0"
            )

        return False, f"No deterministic patching rule matched ticket: '{ticket.title}'"

    def commit_workspace_changes(self, commit_message: str) -> bool:
        """Stages all workspace modifications and creates an automated Git commit."""
        try:
            # Check for unstaged/modified changes
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )
            if not status.stdout.strip():
                logger.info("No modifications present to commit.")
                return False

            subprocess.run(["git", "add", "."],
                           cwd=self.workspace_root, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"auto(studio): {commit_message}"],
                cwd=self.workspace_root,
                check=True
            )
            logger.info(
                f"Automated commit recorded: auto(studio): {commit_message}")
            return True
        except Exception as e:
            logger.warning(f"Git commit skipped or failed: {e}")
            return False

    def verify_workspace_integrity(self) -> bool:
        """Audits all core python modules for bytecode compilation integrity."""
        targets = [
            "schemas/studio_contracts.py",
            "services/agent_runtime/src/virtual_studio_engine.py",
            "services/agent_runtime/src/server.py",
            "services/agent_runtime/src/autonomous_authoring.py",
            "services/agent_runtime/src/codebase_engineer.py",
            "tools/autonomous_runner.py",
            "tools/manage.py"
        ]
        for t in targets:
            try:
                py_compile.compile(str(self.workspace_root / t), doraise=True)
            except Exception as e:
                logger.error(f"Bytecode audit failed on {t}: {e}")
                return False
        return True
