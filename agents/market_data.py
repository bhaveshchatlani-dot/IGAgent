from datetime import datetime, timezone
import yfinance as yf

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def fetch_market_snapshot(run_config: dict) -> dict:
    tickers = run_config["tickers"]

    close = {}
    prev_close = {}

    close_date = {}
    prev_close_date = {}

    for t in tickers:
        # Grab last 5 days so we can safely get "previous close" even around weekends/holidays
        hist = yf.Ticker(t).history(period="5d")

        if hist is None or hist.empty:
            close[t] = None
            prev_close[t] = None
            close_date[t] = None
            prev_close_date[t] = None
            continue

        closes = hist["Close"].dropna()

        if len(closes) == 0:
            close[t] = None
            prev_close[t] = None
            close_date[t] = None
            prev_close_date[t] = None

        elif len(closes) == 1:
            close[t] = float(closes.iloc[-1])
            prev_close[t] = None
            close_date[t] = str(closes.index[-1].date())
            prev_close_date[t] = None

        else:
            close[t] = float(closes.iloc[-1])
            prev_close[t] = float(closes.iloc[-2])
            close_date[t] = str(closes.index[-1].date())
            prev_close_date[t] = str(closes.index[-2].date())

    return {
        "tickers": tickers,
        "as_of": now_iso(),
        "close": close,
        "prev_close": prev_close,
        "close_date": close_date,
        "prev_close_date": prev_close_date,
        "note": "yfinance_close_prevclose"
    }