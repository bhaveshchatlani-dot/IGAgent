import uuid
from pathlib import Path
from rich import print

from utils.io import load_json, save_json
from utils.validate import validate_or_die

from agents.market_data import fetch_market_snapshot
from agents.signals import generate_signals
from agents.post_package import build_post_package

ROOT = Path(__file__).parent
SCHEMAS = ROOT / "schemas"
CONFIGS = ROOT / "config"
RUNS = ROOT / "runs"

def main():
    # Load config (config/run_config.json)
    run_config_path = CONFIGS / "run_config.json"
    if not run_config_path.exists():
        raise FileNotFoundError(f"Missing config at: {run_config_path}")

    run_config = load_json(run_config_path)

    # Validate config
    validate_or_die(SCHEMAS, "RunConfig", run_config)

    # Create run folder
    run_id = uuid.uuid4().hex[:12]
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    save_json(run_dir / "00_run_config.json", run_config)

    # Step 1: Market data (now returns close + prev_close)
    market_snapshot = fetch_market_snapshot(run_config)
    save_json(run_dir / "01_market_snapshot.json", market_snapshot)

    # Step 2: Signals (now returns pct_change_1d)
    signals = generate_signals(market_snapshot)
    save_json(run_dir / "02_signals.json", signals)

    # Step 3: Post package (now prints close + % change)
    post_package = build_post_package(run_id, run_config, market_snapshot, signals)

    # Validate final output
    validate_or_die(SCHEMAS, "PostPackage", post_package)

    save_json(run_dir / "03_post_package.json", post_package)

    print("[bold green]✅ Run complete[/bold green]")
    print(f"Run ID: [bold]{run_id}[/bold]")
    print(f"Artifacts saved to: [bold]{run_dir}[/bold]")
    print("\nHeadline:")
    print(post_package["headline"])
    print("\nCaption:")
    print(post_package["caption"])

if __name__ == "__main__":
    main()