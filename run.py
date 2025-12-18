import uuid
from pathlib import Path
from rich import print

# Optional: load .env here too (so ALL agents have it)
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)

from utils.io import load_json, save_json
from utils.validate import validate_or_die

from agents.market_data import fetch_market_snapshot
from agents.signals import generate_signals
from agents.post_package import build_post_package
from agents.creative_brief import build_creative_brief
from agents.gemini_image import generate_ig_image

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

    # Step 1: Market data
    market_snapshot = fetch_market_snapshot(run_config)
    validate_or_die(SCHEMAS, "MarketSnapshot", market_snapshot)
    save_json(run_dir / "01_market_snapshot.json", market_snapshot)

    # Step 2: Signals
    signals = generate_signals(market_snapshot)
    validate_or_die(SCHEMAS, "Signals", signals)
    save_json(run_dir / "02_signals.json", signals)

    # Step 3: Creative brief (deterministic)
    creative_brief = build_creative_brief(run_config, market_snapshot, signals)
    save_json(run_dir / "03_creative_brief.json", creative_brief)

    # Step 4: Image (Gemini)
    image_path = generate_ig_image(run_dir, creative_brief)  # -> "04_image.png"

    # Step 5: Post package
    post_package = build_post_package(
        run_id, run_config, market_snapshot, signals, image_path=image_path
    )
    validate_or_die(SCHEMAS, "PostPackage", post_package)
    save_json(run_dir / "05_post_package.json", post_package)

    print("[bold green]✅ Run complete[/bold green]")
    print(f"Run ID: [bold]{run_id}[/bold]")
    print(f"Artifacts saved to: [bold]{run_dir}[/bold]")
    print("\nHeadline:")
    print(post_package["headline"])
    print("\nCaption:")
    print(post_package["caption"])


if __name__ == "__main__":
    main()