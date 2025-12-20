from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def build_outbox_item(
    run_id: str,
    post_package: Dict[str, Any],
    run_dir: Path,
    platform: str = "instagram",
    scheduled_for: Optional[str] = None,
) -> Dict[str, Any]:
    assets = post_package.get("assets", [])
    if not assets:
        raise ValueError("PostPackage has no assets.")
    if assets[0].get("type") != "image":
        raise ValueError("PostPackage first asset is not an image.")

    asset_path_str = assets[0]["path"]
    asset_path = Path(asset_path_str)

    # If relative (e.g. "05_image.png"), resolve relative to run_dir
    if not asset_path.is_absolute():
        asset_path = (run_dir / asset_path).resolve()

    if not asset_path.exists():
        raise FileNotFoundError(f"Image asset not found: {asset_path}")

    return {
        "run_id": run_id,
        "created_at": post_package["created_at"],
        "status": "READY_FOR_REVIEW",
        "platform": platform,
        "asset_path": str(asset_path),
        "caption": post_package["caption"],
        "claims": post_package.get("claims", []),
        "evidence": post_package.get("evidence", []),
        "scheduled_for": scheduled_for,
        "attempts": 0,
        "last_error": None,
    }