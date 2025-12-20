from __future__ import annotations

from typing import Any, Dict, List, Optional


def _build_source_string(truth_ledger: Dict[str, Any]) -> str:
    ms = (truth_ledger.get("sources", {}) or {}).get("market_snapshot_note", "").strip()
    sg = (truth_ledger.get("sources", {}) or {}).get("signals_note", "").strip()

    parts = []
    if ms:
        parts.append(ms)
    if sg:
        parts.append(sg)

    return " | ".join(parts) if parts else "Derived from MarketSnapshot + Signals"


def _build_caption_from_truth_ledger(truth_ledger: Dict[str, Any]) -> str:
    lines: List[str] = list(truth_ledger["caption_lines_allowed"])
    lines.append(f"As of: {truth_ledger['as_of']}")
    return "\n".join(lines)


def build_post_package(
    run_id: str,
    run_config: Dict[str, Any],
    truth_ledger: Dict[str, Any],
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Hard rule: caption + claims must be derived ONLY from TruthLedger fields.
    """
    headline = f"Daily Snapshot ({run_config['timeframe']})"

    caption = _build_caption_from_truth_ledger(truth_ledger)

    claims: List[str] = list(truth_ledger["caption_lines_allowed"]) + [f"As of: {truth_ledger['as_of']}"]
    source_str = _build_source_string(truth_ledger)

    evidence = [{"claim": c, "source": source_str} for c in claims]

    post_package: Dict[str, Any] = {
        "run_id": run_id,
        "created_at": truth_ledger["as_of"],  # consistent + already validated as date-time
        "headline": headline,
        "caption": caption,
        "claims": claims,
        "evidence": evidence,
    }

    if image_path:
        post_package["assets"] = [{"type": "image", "path": str(image_path)}]

    return post_package