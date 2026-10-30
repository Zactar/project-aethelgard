#!/usr/bin/env python3
"""
PROJECT AETHELGARD: RFC AUTOMATED PIPELINE CLI
Submits, reviews, and automatically deploys change requests live to the game client.
"""

from services.agent_runtime.src.change_request_engine import StudioReviewBoardEngine
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus
from schemas.studio_contracts import (
    FeatureChangeRequest, RFCChangeType, RFCStatus, GameRuntimeManifest
)
import time
import json
import asyncio
import argparse
import sys
from pathlib import Path

# Inject repository root into sys.path before local package imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


MANIFEST_PATH = ROOT_DIR / "web_client" / "game_runtime_manifest.json"


def trigger_live_hot_reload(manifest: dict):
    try:
        import websockets

        async def _notify():
            async with websockets.connect("ws://127.0.0.1:8765") as ws:
                await ws.send(json.dumps({
                    "type": "HOT_RELOAD_TRIGGER",
                    "manifest": manifest
                }))

        asyncio.run(_notify())
        print(
            "  [LIVE BROADCAST]: Pushed hot-reload update to open browser sessions.")
    except Exception as e:
        print(
            f"  [NOTE]: Client broadcast skipped (server offline or no active clients): {e}")


def load_manifest() -> GameRuntimeManifest:
    if not MANIFEST_PATH.exists():
        print(
            f"[ERROR]: {MANIFEST_PATH} not found. Run a generation cycle first.")
        sys.exit(1)
    return GameRuntimeManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))


def process_single_rfc(file_path: Path):
    board = StudioReviewBoardEngine(StudioSharedMemoryBus())
    manifest = load_manifest()

    rfc = FeatureChangeRequest.model_validate_json(
        file_path.read_text(encoding="utf-8"))
    print("\n" + "=" * 70)
    print(f" >>> [REVIEW BOARD CONVENED]: {rfc.rfc_id} ('{rfc.title}') <<<")
    print("=" * 70)

    evaluated_rfc = board.review_request(rfc, manifest)

    for vote in evaluated_rfc.review_votes:
        status_sym = "APPROVED" if vote.approved else "REJECTED"
        print(
            f"  * [{status_sym}] {vote.agent_id} (Score: {vote.score:.2f}) -> {vote.comments}")

    if evaluated_rfc.status == RFCStatus.APPROVED:
        print("\n>>> RESULT: APPROVED BY QUORUM. Executing automated deployment...")
        updated_manifest = board.apply_approved_change(evaluated_rfc, manifest)

        # Write to web client runtime manifest
        MANIFEST_PATH.write_text(
            updated_manifest.model_dump_json(indent=2), encoding="utf-8")
        print(f"  [DEPLOYED]: Updated {MANIFEST_PATH}")

        # Trigger live websocket broadcast to open browser clients
        trigger_live_hot_reload(updated_manifest.model_dump())

        # Move to approved
        target = board.approved_dir / file_path.name
        file_path.unlink()
        target.write_text(evaluated_rfc.model_dump_json(
            indent=2), encoding="utf-8")
    else:
        print("\n>>> RESULT: REJECTED. Flagged risks:")
        for r in evaluated_rfc.rejection_reasons:
            print(f"    - {r}")
        target = board.rejected_dir / file_path.name
        file_path.unlink()
        target.write_text(evaluated_rfc.model_dump_json(
            indent=2), encoding="utf-8")
    print("=" * 70 + "\n")


def cmd_submit(args):
    board = StudioReviewBoardEngine(StudioSharedMemoryBus())
    payload = json.loads(args.diff)

    rfc = FeatureChangeRequest(
        rfc_id=f"RFC-{int(time.time())}",
        title=args.title,
        description=args.desc,
        submitted_by=args.author,
        change_type=RFCChangeType(args.type),
        payload_diff=payload
    )

    out_file = board.pending_dir / f"{rfc.rfc_id}.json"
    out_file.write_text(rfc.model_dump_json(indent=2), encoding="utf-8")
    print(
        f"\n[RFC SUBMITTED]: {rfc.rfc_id} - '{rfc.title}' saved to {out_file}")

    if args.auto_review:
        process_single_rfc(out_file)


def cmd_review_pending(args):
    board = StudioReviewBoardEngine(StudioSharedMemoryBus())
    pending_files = list(board.pending_dir.glob("*.json"))
    if not pending_files:
        print("[REVIEW BOARD]: No pending RFCs in queue.")
        return
    for f in pending_files:
        process_single_rfc(f)


def main():
    parser = argparse.ArgumentParser(
        description="Aethelgard RFC & Feature Deployment Engine")
    sub = parser.add_subparsers(dest="cmd")

    sub_submit = sub.add_parser(
        "submit", help="Submit a new feature or change request")
    sub_submit.add_argument("--title", required=True,
                            help="Short title of the change")
    sub_submit.add_argument("--desc", default="",
                            help="Description and reasoning")
    sub_submit.add_argument("--author", default="Lead_Dev",
                            help="Submitting agent or human username")
    sub_submit.add_argument(
        "--type", required=True, choices=[e.value for e in RFCChangeType], help="Change discipline")
    sub_submit.add_argument("--diff", required=True,
                            help="JSON string representing the diff payload")
    sub_submit.add_argument(
        "--auto-review", action="store_true", help="Immediately run the review board")

    sub_review = sub.add_parser(
        "review", help="Review and process all pending RFCs")

    args = parser.parse_args()
    if args.cmd == "submit":
        cmd_submit(args)
    elif args.cmd == "review":
        cmd_review_pending(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
