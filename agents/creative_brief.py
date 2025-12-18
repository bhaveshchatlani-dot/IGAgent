from __future__ import annotations
from typing import Dict, Any, List

def _fmt_price(x):
    return f"{x:.2f}" if isinstance(x, (int, float)) else "N/A"

def _fmt_pct(x):
    return f"{x:+.2f}%" if isinstance(x, (int, float)) else "N/A"

def build_creative_brief(run_config: Dict[str, Any], market_snapshot: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    tickers: List[str] = run_config["tickers"]

    close = market_snapshot.get("close", {})
    pct = signals.get("pct_change_1d", {})
    direction = signals.get("direction_1d", {})

    title = "Daily Snapshot"
    subtitle = f"{run_config.get('market','US')} • {run_config.get('timeframe','1D')} • {', '.join(tickers)}"

    rows = []
    for t in tickers:
        rows.append({
            "ticker": t,
            "close_str": _fmt_price(close.get(t)),
            "pct_str": _fmt_pct(pct.get(t)),
            "direction": direction.get(t) or "FLAT"
        })

    footer = "Educational only. Not financial advice."

    # One strict prompt template (consistency guardrail)
    image_prompt = (
        "Create a clean, premium, dark fintech Instagram infographic card (1080x1350, 4:5).\n"
        "IMPORTANT RULES:\n"
        "- Use EXACTLY the text provided below. Do not change numbers, tickers, punctuation, or spacing.\n"
        "- Do not add extra tickers, extra numbers, or extra sentences.\n"
        "- Layout: Header (title), subheader (subtitle), table rows, small footer.\n"
        "- Background: dark. Minimal accents. High contrast text. No charts.\n"
        "- For direction icons, use ONLY: UP=🔺, DOWN=🔻, FLAT=➖.\n\n"
        f"TITLE: {title}\n"
        f"SUBTITLE: {subtitle}\n\n"
        "ROWS (render each row as: TICKER | CLOSE | 1D% | ICON):\n"
        + "\n".join([f"{r['ticker']} | {r['close_str']} | {r['pct_str']} | { {'UP':'🔺','DOWN':'🔻','FLAT':'➖'}.get(r['direction'],'➖') }" for r in rows]) +
        f"\n\nFOOTER: {footer}\n"
    )

    return {
        "aspect_ratio": "4:5",
        "title": title,
        "subtitle": subtitle,
        "rows": rows,
        "footer_note": footer,
        "image_prompt": image_prompt,
        "note": "deterministic_brief_v1"
    }