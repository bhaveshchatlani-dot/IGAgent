from __future__ import annotations

from typing import Any, Dict, List


def _arrow(direction: str) -> str:
    return {"UP": "↑", "DOWN": "↓", "FLAT": "→"}[direction]


def _sign_pct(direction: str, pct_str: str) -> str:
    """
    Ensures pct includes a sign when appropriate.
    Assumes pct_str already contains % and value (e.g. '0.6%').
    If pct_str already starts with + or -, leave it.
    """
    s = pct_str.strip()
    if not s:
        return s
    if s[0] in {"+", "-"}:
        return s
    if direction == "UP":
        return f"+{s}"
    if direction == "DOWN":
        return f"-{s}"
    return s


def build_creative_brief(run_config: Dict[str, Any], truth_ledger: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hard rule: CreativeBrief must be derived ONLY from TruthLedger + RunConfig fields.
    """
    timeframe = run_config["timeframe"]
    market = run_config.get("market", "").strip() or "US"
    tickers = run_config["tickers"]

    image_cfg = (run_config.get("image") or {})
    image_mode = (image_cfg.get("mode") or "gemini").lower()

    # Choose aspect ratio: template design is typically 4:5 (1080x1350)
    # Gemini snapshot prompt previously used 1:1. Keep both supported.
    aspect_ratio = "4:5" if image_mode == "template" else "1:1"

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

    # -----------------------------
    # Gemini prompt (keep as-is)
    # -----------------------------
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

    # -----------------------------
    # Template render payload (NEW)
    # -----------------------------
    # Expect TruthLedger to contain these in a structured way.
    # If not present yet, you can populate these from Signals later.
    # For now, we use whatever is already in TruthLedger (hard rule compliant).

    # You will likely evolve TruthLedger to provide movers/losers structure.
    # For a safe v0: reuse top rows to fill slots deterministically.
    def pick_n(src: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        return (src[:n] + [src[-1]] * n)[:n]  # guard, never crash if short

    top3 = pick_n(rows_in, 3)

    # Minimal icon mapping (deterministic). You can replace with a proper mapping table later.
    # IMPORTANT: do not guess "official logos". Use silhouette icon keys you actually have in assets/icons.
    icon_map = (image_cfg.get("icon_map") or {})  # optional: {"AAPL":"apple", ...}
    def icon_key_for(ticker: str) -> str:
        return icon_map.get(ticker, "generic")  # ensure assets/icons/generic.png exists

    # Use directions to add +/- signs if your pct_str lacks them.
    def pct_for(r: Dict[str, Any]) -> str:
        return _sign_pct(r["direction"], r["pct_str"])

    render_payload = {
        # This is the header line that appears under the title in your template design.
        # Keep it truth-only: market + timeframe + as_of (or add indices later via TruthLedger allowed claims).
        "header_line": f"{market} | Close | {timeframe} | As of {truth_ledger['as_of']}",
        "gainers": [
            {"ticker": top3[0]["ticker"], "pct": pct_for(top3[0]), "icon_key": icon_key_for(top3[0]["ticker"])},
            {"ticker": top3[1]["ticker"], "pct": pct_for(top3[1]), "icon_key": icon_key_for(top3[1]["ticker"])},
            {"ticker": top3[2]["ticker"], "pct": pct_for(top3[2]), "icon_key": icon_key_for(top3[2]["ticker"])},
        ],
        "biggest_winner": {
            "ticker": top3[0]["ticker"],
            "pct": pct_for(top3[0]),
            "icon_key": icon_key_for(top3[0]["ticker"]),
        },
        "biggest_loser": {
            "ticker": top3[-1]["ticker"],
            "pct": pct_for(top3[-1]),
            "icon_key": icon_key_for(top3[-1]["ticker"]),
        },
        "decliners": [
            {"ticker": top3[0]["ticker"], "pct": pct_for(top3[0]), "icon_key": icon_key_for(top3[0]["ticker"])},
            {"ticker": top3[1]["ticker"], "pct": pct_for(top3[1]), "icon_key": icon_key_for(top3[1]["ticker"])},
            {"ticker": top3[2]["ticker"], "pct": pct_for(top3[2]), "icon_key": icon_key_for(top3[2]["ticker"])},
        ],
    }

    return {
        "template": run_config["template"],
        "timeframe": timeframe,
        "as_of": truth_ledger["as_of"],
        "aspect_ratio": aspect_ratio,
        "context_line": context_line,
        "footer_disclaimer": footer_disclaimer,
        "rows": rows,
        "image_prompt": image_prompt,
        "render_payload": render_payload,  # NEW
    }