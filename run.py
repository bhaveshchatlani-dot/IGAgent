import uuid
from pathlib import Path
from rich import print

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)

from utils.io import load_json, save_json
from utils.validate import validate_or_die

from agents.market_data import fetch_market_snapshot
from agents.signals import generate_signals
from agents.truth_ledger import build_truth_ledger
from agents.creative_brief import build_creative_brief
from agents.gemini_image import generate_ig_image
from agents.post_package import build_post_package
from agents.outbox import build_outbox_item  # NEW

SCHEMAS = ROOT / "schemas"
CONFIGS = ROOT / "config"
RUNS = ROOT / "runs"
OUTBOX = ROOT / "outbox"  # NEW


def main():
    run_config_path = CONFIGS / "run_config.json"
    if not run_config_path.exists():
        raise FileNotFoundError(f"Missing config at: {run_config_path}")

    run_config = load_json(run_config_path)
    validate_or_die(SCHEMAS, "RunConfig", run_config)

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

    # Step 3: Truth Ledger (compliance hard gate)
    truth_ledger = build_truth_ledger(market_snapshot, signals, run_config)
    validate_or_die(SCHEMAS, "TruthLedger", truth_ledger)
    save_json(run_dir / "03_truth_ledger.json", truth_ledger)

    # Step 4: Creative brief (derived ONLY from TruthLedger)
    creative_brief = build_creative_brief(run_config, truth_ledger)
    validate_or_die(SCHEMAS, "CreativeBrief", creative_brief)
    save_json(run_dir / "04_creative_brief.json", creative_brief)

       # Step 5: Image (Template renderer OR Gemini)
    image_filename = generate_ig_image(
        run_dir,
        creative_brief,
        run_config=run_config,
        filename="05_image.png",
    )
    

    # Step 6: Post package (caption ONLY from TruthLedger)
    post_package = build_post_package(
        run_id=run_id,
        run_config=run_config,
        truth_ledger=truth_ledger,
        image_path=image_filename,
    )
    validate_or_die(SCHEMAS, "PostPackage", post_package)
    save_json(run_dir / "06_post_package.json", post_package)

    # Step 7: Outbox (manual approval gate)  NEW
    OUTBOX.mkdir(parents=True, exist_ok=True)
    outbox_item = build_outbox_item(
        run_id=run_id,
        post_package=post_package,
        run_dir=run_dir,
        platform="instagram",
        scheduled_for=None,
    )
    validate_or_die(SCHEMAS, "OutboxItem", outbox_item)

    outbox_path = OUTBOX / f"{run_id}.json"
    save_json(outbox_path, outbox_item)

    print("[bold green]✅ Run complete[/bold green]")
    print(f"Run ID: [bold]{run_id}[/bold]")
    print(f"Artifacts saved to: [bold]{run_dir}[/bold]")
    print(f"Outbox item created: [bold]{outbox_path}[/bold]")

    print("\nHeadline:")
    print(post_package["headline"])
    print("\nCaption:")
    print(post_package["caption"])


if __name__ == "__main__":
    main()