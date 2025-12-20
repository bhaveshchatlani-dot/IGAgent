from __future__ import annotations

import sys
from pathlib import Path

from utils.io import load_json, save_json

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / "outbox"


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/approve_outbox.py <outbox_item.json>")
        raise SystemExit(2)

    path = Path(sys.argv[1]).resolve()
    item = load_json(path)

    if item.get("status") != "READY_FOR_REVIEW":
        print(f"Not approving because status is {item.get('status')}")
        raise SystemExit(1)

    item["status"] = "APPROVED"
    save_json(path, item)
    print(f"✅ Approved: {path}")


if __name__ == "__main__":
    main()