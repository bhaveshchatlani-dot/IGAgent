from dotenv import load_dotenv
load_dotenv()

import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

from pathlib import Path
from google import genai
from google.genai import types

OUT = Path("runs/_manual_test")
OUT.mkdir(parents=True, exist_ok=True)

client = genai.Client()

prompt = (
    "Create a clean, premium, dark fintech Instagram card.\n"
    "Exact size: 1080x1350 (4:5). Minimal style.\n"
    "Render this text exactly:\n"
    "TITLE: Daily Snapshot\n"
    "SUBTITLE: US • 1D • AAPL, MSFT\n"
    "ROWS:\n"
    "AAPL | 222.10 | +0.42% | 🔺\n"
    "MSFT | 440.55 | -0.18% | 🔻\n"
    "FOOTER: Educational only. Not financial advice.\n"
    "Do not add any extra tickers or numbers."
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="4:5",
            image_size="2K",
        ),
    ),
)

saved = False
for part in response.parts:
    if part.inline_data is not None:
        img = part.as_image()     # requires pillow
        img.save(OUT / "test_04_image.png")
        saved = True
        break

if not saved:
    raise RuntimeError("No image returned. Check model access / billing / quota.")

print(f"Saved: {OUT / 'test_04_image.png'}")