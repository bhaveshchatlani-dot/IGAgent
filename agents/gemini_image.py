from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import base64
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


def _write_inline_image(part, out_path: Path) -> bool:
    inline = getattr(part, "inline_data", None)
    if not inline:
        return False

    data = getattr(inline, "data", None)
    if data is None:
        return False

    if isinstance(data, bytes):
        out_path.write_bytes(data)
        return True

    if isinstance(data, str):
        out_path.write_bytes(base64.b64decode(data))
        return True

    return False


def generate_ig_image(
    run_dir: Path,
    creative_brief: Dict[str, Any],
    filename: str = "04_image.png",
) -> str:
    # Load .env from repo root (run_dir is runs/<run_id>)
    repo_root = run_dir.parent.parent
    load_dotenv(dotenv_path=repo_root / ".env", override=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Create a .env file in repo root containing:\n"
            "GEMINI_API_KEY=YOUR_KEY"
        )

    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    seed = int(os.getenv("GEMINI_SEED", "7"))
    retries = int(os.getenv("GEMINI_RETRIES", "2"))

    client = genai.Client(api_key=api_key)
    out_path = run_dir / filename

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=creative_brief["image_prompt"],
                config=types.GenerateContentConfig(
                    temperature=0,
                    seed=seed,
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=creative_brief.get("aspect_ratio", "4:5"),
                    ),
                ),
            )

            for part in resp.parts:
                if _write_inline_image(part, out_path):
                    return filename

            raise RuntimeError("Gemini returned no inline image data.")

        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Image generation failed after retries: {last_err}")