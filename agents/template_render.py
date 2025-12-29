from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font_path: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    """
    Shrinks font size until text fits max_width.
    """
    size = start_size
    while size >= 10:
        font = _load_font(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            return font
        size -= 1
    return _load_font(font_path, 10)


def _paste_icon(base: Image.Image, icon_path: Path, box: Tuple[int, int, int, int]) -> None:
    """
    Pastes a transparent PNG icon into a bounding box (x1,y1,x2,y2) with aspect-preserving resize.
    """
    if not icon_path.exists():
        raise FileNotFoundError(f"Missing icon: {icon_path}")

    icon = Image.open(icon_path).convert("RGBA")
    x1, y1, x2, y2 = box
    bw, bh = (x2 - x1), (y2 - y1)

    # aspect-preserving fit
    iw, ih = icon.size
    scale = min(bw / iw, bh / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    icon = icon.resize((nw, nh), resample=Image.LANCZOS)

    px = x1 + (bw - nw) // 2
    py = y1 + (bh - nh) // 2
    base.alpha_composite(icon, (px, py))


def render_movers_losers_from_template(
    out_path: Path,
    creative_brief: Dict[str, Any],
    image_cfg: Dict[str, Any],
) -> None:
    """
    Deterministic renderer:
      - loads a master template PNG
      - places text + icons at fixed coordinates from a layout spec

    Required:
      image_cfg.template_path
      image_cfg.layout (inline dict) OR image_cfg.layout_path (json you load in your own code)
      image_cfg.font_regular, image_cfg.font_bold
      image_cfg.icons_dir

    creative_brief must contain:
      creative_brief["render_payload"] (dict of tickers/pcts/icon_keys)
    """
    template_path = Path(image_cfg["template_path"])
    if not template_path.exists():
        raise FileNotFoundError(f"Missing template at {template_path}")

    font_regular = image_cfg["font_regular"]
    font_bold = image_cfg["font_bold"]
    icons_dir = Path(image_cfg["icons_dir"])

    layout = image_cfg.get("layout")
    if not isinstance(layout, dict):
        raise RuntimeError("image_cfg.layout must be an inline dict for now (or extend to load from layout_path).")

    payload = creative_brief.get("render_payload")
    if not isinstance(payload, dict):
        raise RuntimeError("creative_brief.render_payload missing. Add it in build_creative_brief().")

    base = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    # --- helper to draw text ---
    def draw_text(key: str, text: str, color: Tuple[int, int, int], font_path: str, size: int, max_w: Optional[int] = None):
        spec = layout["text"][key]  # {"xy":[x,y], "max_w": 200, "size": 42}
        x, y = spec["xy"]
        mw = max_w if max_w is not None else spec.get("max_w")
        fs = spec.get("size", size)
        if mw:
            font = _fit_text(draw, text, font_path, mw, fs)
        else:
            font = _load_font(font_path, fs)
        draw.text((x, y), text, font=font, fill=color)

    # --- helper to paste icon ---
    def paste_icon(slot_key: str, icon_key: str):
        box = layout["icons"][slot_key]  # [x1,y1,x2,y2]
        icon_path = icons_dir / f"{icon_key}.png"
        _paste_icon(base, icon_path, tuple(box))

    # Colors (keep consistent)
    GREEN = tuple(image_cfg.get("green_rgb", [25, 77, 50]))
    RED = tuple(image_cfg.get("red_rgb", [176, 35, 35]))
    DARK = tuple(image_cfg.get("dark_rgb", [20, 20, 20]))

    # --- Example payload usage ---
    # gainers: [{ticker,pct,icon_key} x3]
    for i, row in enumerate(payload["gainers"], start=1):
        draw_text(f"g{i}_ticker", row["ticker"], DARK, font_bold, 40)
        draw_text(f"g{i}_pct", row["pct"], GREEN, font_bold, 34)
        paste_icon(f"g{i}_icon", row["icon_key"])

    bw = payload["biggest_winner"]
    draw_text("bw_ticker", bw["ticker"], (255, 255, 255), font_bold, 72)
    draw_text("bw_pct", bw["pct"], (255, 255, 255), font_bold, 64)
    paste_icon("bw_hero_icon", bw["icon_key"])

    bl = payload["biggest_loser"]
    draw_text("bl_ticker", bl["ticker"], (255, 255, 255), font_bold, 72)
    draw_text("bl_pct", bl["pct"], (255, 255, 255), font_bold, 64)
    paste_icon("bl_hero_icon", bl["icon_key"])

    for i, row in enumerate(payload["decliners"], start=1):
        draw_text(f"d{i}_ticker", row["ticker"], DARK, font_bold, 40)
        draw_text(f"d{i}_pct", row["pct"], RED, font_bold, 34)
        paste_icon(f"d{i}_icon", row["icon_key"])

    # optional header line (if you want it dynamic too)
    header = payload.get("header_line")
    if header:
        draw_text("header_line", header, DARK, font_regular, 26)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(out_path, format="PNG")