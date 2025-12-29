from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import base64
import os
import time

from dotenv import load_dotenv

# Gemini imports stay optional (only used in gemini mode)
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
    run_config: Optional[Dict[str, Any]] = None,
    filename: str = "05_image.png",
) -> str:
    """
    Modes:
      - image.mode == "template": deterministic render from a master template (recommended)
      - otherwise: Gemini generate (current behavior)
    """
    run_config = run_config or {}
    image_cfg = run_config.get("image", {}) or {}
    mode = (image_cfg.get("mode") or "gemini").lower()

    out_path = run_dir / filename

    if mode == "template":
        # Deterministic, no model drift
        from agents.template_render import render_movers_losers_from_template

        render_movers_losers_from_template(
            out_path=out_path,
            creative_brief=creative_brief,
            image_cfg=image_cfg,
        )
        return filename

    # --- Gemini (current behavior) ---
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

            for part in getattr(resp, "parts", []) or []:
                if _write_inline_image(part, out_path):
                    return filename

            # Some SDK responses nest parts; fail loudly so retries work
            raise RuntimeError("Gemini returned no inline image data in resp.parts.")

        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Image generation failed after retries: {last_err}")