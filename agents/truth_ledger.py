from __future__ import annotations

from typing import Any, Dict, List, Optional


def _fmt_close(x: Optional[float]) -> str:
    # strict gate: caller should not pass None
    s = f"{x:,.2f}"
    s = s.rstrip("0").rstrip(".")
    return s


def _fmt_pct(x: Optional[float]) -> str:
    # strict gate: caller should not pass None
    # NOTE: assumes x is already in percent units (e.g., 1.23 == 1.23%)
    s = f"{x:+.2f}%"
    if s.startswith("-0.00"):
        s = "+0.00%"
    return s


def _arrow(direction: str) -> str:
    return {"UP": "↑", "DOWN": "↓", "FLAT": "→"}[direction]


def build_truth_ledger(
    market_snapshot: Dict[str, Any],
    signals: Dict[str, Any],
    run_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Outputs:
      - exact displayed rows: (ticker, close_str, pct_str, direction)
      - caption lines allowed (ONLY derived from row fields)
      - sources (market_snapshot.note, signals.note)
    Hard gate: if any required field is missing, raise.
    """
    tickers: List[str] = run_config["tickers"]

    rows: List[Dict[str, Any]] = []
    caption_lines_allowed: List[str] = []

    for t in tickers:
        close = market_snapshot["close"].get(t)
        pct = signals["pct_change_1d"].get(t)
        direction = signals["direction_1d"].get(t)

        if close is None or pct is None or direction is None:
            raise ValueError(
                f"TruthLedger cannot be built for {t}: "
                f"close={close}, pct_change_1d={pct}, direction_1d={direction}"
            )

        close_str = _fmt_close(close)
        pct_str = _fmt_pct(pct)

        row = {
            "ticker": t,
            "close_str": close_str,
            "pct_str": pct_str,
            "direction": direction,
        }
        rows.append(row)

        caption_lines_allowed.append(
            f"{t}: {close_str} {_arrow(direction)} {pct_str}"
        )

    truth_ledger = {
        "as_of": market_snapshot["as_of"],
        "rows": rows,
        "caption_lines_allowed": caption_lines_allowed,
        "sources": {
            "market_snapshot_note": market_snapshot.get("note", ""),
            "signals_note": signals.get("note", ""),
        },
    }

    return truth_ledger