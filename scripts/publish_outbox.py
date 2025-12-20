from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

from utils.io import load_json, save_json


ROOT = Path(__file__).resolve().parents[1]
OUTBOX_DIR = ROOT / "outbox"


def now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now().isoformat()


def parse_dt(dt_str: str) -> datetime:
    # handles "2025-12-20T10:00:00+00:00" and "...Z"
    s = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def publish_one(outbox_path: Path) -> int:
    item = load_json(outbox_path)

    # normalize optional fields
    item.setdefault("attempts", 0)
    item.setdefault("last_error", None)
    item.setdefault("scheduled_for", None)
    item.setdefault("published_at", None)

    status = item.get("status")
    if status != "APPROVED":
        print(f"Skipping (status={status}): {outbox_path.name}")
        return 0

    scheduled_for = item.get("scheduled_for")
    if scheduled_for:
        try:
            if parse_dt(scheduled_for) > now():
                print(f"Skipping (scheduled_for={scheduled_for}): {outbox_path.name}")
                return 0
        except Exception:
            # if scheduled_for is malformed, fail safely
            item["status"] = "FAILED"
            item["attempts"] = int(item["attempts"]) + 1
            item["last_error"] = f"Invalid scheduled_for datetime: {scheduled_for}"
            save_json(outbox_path, item)
            print(f"❌ Failed (bad scheduled_for): {outbox_path.name}")
            return 1

    asset_path = Path(item["asset_path"])
    if not asset_path.exists():
        item["status"] = "FAILED"
        item["attempts"] = int(item["attempts"]) + 1
        item["last_error"] = f"Asset not found: {asset_path}"
        save_json(outbox_path, item)
        print(f"❌ Failed (missing asset): {outbox_path.name}")
        return 1

    # TODO: Replace this stub with real Instagram publishing.
    item["status"] = "PUBLISHED"
    item["attempts"] = int(item["attempts"]) + 1
    item["last_error"] = None
    item["published_at"] = now_iso()

    save_json(outbox_path, item)
    print(f"✅ Published (stub): {outbox_path.name}")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/publish_outbox.py <outbox_item.json>")
        print("  python scripts/publish_outbox.py --all")
        raise SystemExit(2)

    arg = sys.argv[1]

    if arg == "--all":
        if not OUTBOX_DIR.exists():
            print("No outbox directory found.")
            raise SystemExit(1)

        failures = 0
        for p in sorted(OUTBOX_DIR.glob("*.json")):
            failures += publish_one(p)
        raise SystemExit(1 if failures else 0)

    outbox_path = Path(arg).resolve()
    if not outbox_path.exists():
        print(f"Outbox item not found: {outbox_path}")
        raise SystemExit(1)

    failures = publish_one(outbox_path)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()