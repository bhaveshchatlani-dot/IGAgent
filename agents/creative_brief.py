from __future__ import annotations

from typing import Any, Dict, List


def _arrow(direction: str) -> str:
    return {"UP": "↑", "DOWN": "↓", "FLAT": "→"}[direction]


def build_creative_brief(run_config: Dict[str, Any], truth_ledger: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hard rule: CreativeBrief must be derived ONLY from TruthLedger + RunConfig fields.
    (RunConfig is allowed because it's config, not market interpretation.)
    """
    timeframe = run_config["timeframe"]
    market = run_config.get("market", "").strip() or "US"
    tickers = run_config["tickers"]

    rows_in: List[Dict[str, Any]] = truth_ledger["rows"]
    rows: List[Dict[str, Any]] = []

    for r in rows_in:
        direction = r["direction"]
        rows.append(
            {
                "ticker": r["ticker"],
                "close_str": r["close_str"],
                "pct_str": r["pct_str"],
                "direction": direction,
                "arrow": _arrow(direction),
            }
        )

    # Whitelisted “extra text” (not claims): market/timeframe/tickers + disclaimer
    context_line = f"{market} • {timeframe} • {', '.join(tickers)}"
    footer_disclaimer = "Educational only. Not financial advice."

    # Prompt: allow aesthetics, but lock all text to an explicit whitelist
    allowed_rows = [f"{r['ticker']}  {r['close_str']}  {r['arrow']} {r['pct_str']}" for r in rows]

    lines: List[str] = []
    lines.append("Design a premium Instagram finance snapshot graphic.")
    lines.append("Canvas: 1080x1080 (1:1).")
    lines.append("")
    lines.append("Style (allowed, decorative only):")
    lines.append("- Dark modern background with subtle diagonal lines / gradient texture (no charts).")
    lines.append("- Clean grid/table layout, thin dividers, soft glow accents.")
    lines.append("- Use a blue accent for positive and red accent for negative.")
    lines.append("- Use small up/down triangle icons if desired (decorative).")
    lines.append("")
    lines.append("TEXT MUST MATCH EXACTLY (do not add ANY other text):")
    lines.append(f"1) Title: Daily Snapshot ({timeframe})")
    lines.append(f"2) Context line: {context_line}")
    lines.append(f"3) As-of line: As of {truth_ledger['as_of']}")
    lines.append("4) Table rows (exactly these, exactly as written):")
    for row_line in allowed_rows:
        lines.append(f"   - {row_line}")
    lines.append(f"5) Footer: {footer_disclaimer}")
    lines.append("")
    lines.append("Hard rules:")
    lines.append("- Do NOT add tickers, prices, percentages, commentary, advice, predictions, or news.")
    lines.append("- Do NOT add any extra labels (e.g., 'close', 'change', 'USD') unless included above.")
    lines.append("- Only decorative shapes/background are allowed beyond the exact text whitelist.")

    image_prompt = "\n".join(lines)

    return {
        "template": run_config["template"],
        "timeframe": timeframe,
        "as_of": truth_ledger["as_of"],
        "aspect_ratio": "1:1",
        "context_line": context_line,
        "footer_disclaimer": footer_disclaimer,
        "rows": rows,
        "image_prompt": image_prompt,
    }