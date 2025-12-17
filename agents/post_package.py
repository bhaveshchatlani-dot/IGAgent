from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def build_post_package(run_id: str, run_config: dict, market_snapshot: dict, signals: dict) -> dict:
    created_at = now_iso()
    headline = f"Daily Snapshot: {', '.join(run_config['tickers'])}"

    close = market_snapshot.get("close", {})
    pct = signals.get("pct_change_1d", {})
    direction = signals.get("direction_1d", {})

    def fmt_price(x):
        return f"{x:.2f}" if isinstance(x, (int, float)) else "N/A"

    def fmt_pct(x):
        return f"{x:+.2f}%" if isinstance(x, (int, float)) else "N/A"

    def arrow(dir_val):
        return {"UP": "↑", "DOWN": "↓", "FLAT": "→"}.get(dir_val, "")

    lines = []
    for t in run_config["tickers"]:
        a = arrow(direction.get(t))
        lines.append(f"- {t}: {fmt_price(close.get(t))} {a} ({fmt_pct(pct.get(t))})")
    summary_lines = "\n".join(lines)

    claims = [
        f"Pulled latest close prices for {', '.join(run_config['tickers'])}.",
        "Computed 1D % change vs previous close."
    ]

    evidence = [
        {"claim": claims[0], "source": market_snapshot.get("note", "market_snapshot")},
        {"claim": claims[1], "source": signals.get("note", "signals")}
    ]

    caption = (
        f"{headline}\n\n"
        f"- Market: {run_config['market']}\n"
        f"- Timeframe: {run_config['timeframe']}\n\n"
        "Close (1D %):\n"
        f"{summary_lines}\n\n"
        "Educational only. Not financial advice."
    )

    return {
        "run_id": run_id,
        "created_at": created_at,
        "headline": headline,
        "caption": caption,
        "claims": claims,
        "evidence": evidence
    }