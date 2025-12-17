def generate_signals(market_snapshot: dict) -> dict:
    tickers = market_snapshot["tickers"]
    close = market_snapshot.get("close", {})
    prev = market_snapshot.get("prev_close", {})

    changes = {}
    direction = {}

    for t in tickers:
        c = close.get(t)
        p = prev.get(t)

        if isinstance(c, (int, float)) and isinstance(p, (int, float)) and p != 0:
            changes[t] = (c - p) / p * 100.0
        else:
            changes[t] = None

        if isinstance(changes[t], (int, float)):
            direction[t] = "UP" if changes[t] > 0 else ("DOWN" if changes[t] < 0 else "FLAT")
        else:
            direction[t] = None

    return {
        "as_of": market_snapshot.get("as_of"),
        "pct_change_1d": changes,
        "direction_1d": direction,
        "note": "close_vs_prev_close"
    }