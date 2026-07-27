"""Render HTML+CSS template menjadi PNG/JPEG pakai Playwright.

Isi data dinamis ke template (headline, poin, kategori, background AI,
source attribution, watermark). Fungsi utama: render_infographic().
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("tmp_design")
OUTPUT_DIR.mkdir(exist_ok=True)

# Load base HTML template
TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(category: str) -> str:
    """Load variant template HTML."""
    variant_file = TEMPLATE_DIR / "variants" / f"{category}.html"
    if variant_file.exists():
        return variant_file.read_text(encoding="utf-8")
    # Fallback to general
    fallback = TEMPLATE_DIR / "variants" / "general.html"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")
    # Minimal inline template
    return """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: 1080px; height: 1080px;
            font-family: 'Inter', -apple-system, sans-serif;
            background-size: cover;
            background-position: center;
            background-image: url('{{background_image}}');
            position: relative;
            color: white;
            display: flex; flex-direction: column; justify-content: center;
            padding: 80px;
        }
        .overlay { background: rgba(0,0,0,0.5); border-radius: 20px; padding: 40px; }
        h1 { font-size: 48px; font-weight: 800; line-height: 1.2; margin-bottom: 24px; }
        ul { list-style: none; }
        li { font-size: 28px; line-height: 1.6; margin-bottom: 16px; position: relative; padding-left: 40px; }
        li::before { content: "•"; position: absolute; left: 0; font-size: 32px; color: #ffd700; }
        .source { margin-top: 32px; font-size: 18px; opacity: 0.8; }
        .watermark { position: absolute; bottom: 20px; right: 20px; font-size: 14px; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="overlay">
        <h1>{{headline}}</h1>
        <ul>{{points}}</ul>
        <div class="source">{{source_attribution}}</div>
    </div>
    <div class="watermark">{{watermark_text}}</div>
</body>
</html>
"""


def render_infographic(
    headline: str,
    points: list[str],
    category: str,
    background_image_path: str,
    source_attribution: str,
    watermark_text: str = "Ilustrasi AI",
    output_path: Optional[str] = None,
) -> str:
    """Render template HTML (variants/{category}.html) menjadi JPEG,
    dengan background_image_path sebagai background-image, dan overlay
    headline/points/source_attribution/watermark_text sebagai teks HTML.
    Return path file JPEG hasil render (untuk dipakai compositor.py)."""

    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Load template
    template_html = _load_template(category)

    # 2. Prepare data
    points_html = "".join(f"<li>{p}</li>" for p in points)

    # Convert local image path to file:// URI for CSS background-image
    bg_uri = Path(background_image_path).resolve().as_uri()

    # 3. Replace placeholders
    template_html = template_html.replace("{{headline}}", headline)
    template_html = template_html.replace("{{points}}", points_html)
    template_html = template_html.replace("{{source_attribution}}", source_attribution)
    template_html = template_html.replace("{{watermark_text}}", watermark_text)
    template_html = template_html.replace("{{background_image}}", bg_uri)
    template_html = template_html.replace("{{category}}", category)

    # 4. Write temp HTML
    if output_path is None:
        safe_headline = "".join(c for c in headline if c.isalnum() or c in " -_")[:30]
        output_path = str(OUTPUT_DIR / f"infographic_{category}_{safe_headline}.jpg")
    else:
        output_path = str(Path(output_path).with_suffix(".jpg"))

    temp_html = OUTPUT_DIR / f"temp_{Path(output_path).stem}.html"
    temp_html.write_text(template_html, encoding="utf-8")

    # 5. Render with Playwright
    async def _render():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.goto(temp_html.resolve().as_uri())
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=output_path, type="jpeg", quality=90)
            await browser.close()

    asyncio.run(_render())

    # 6. Cleanup temp HTML
    temp_html.unlink(missing_ok=True)

    logger.info("Rendered infographic: %s", output_path)
    return output_path


# Backwards compatibility wrapper
def render_template(
    template_name: str,
    data: dict,
    output_path: Optional[str] = None,
    variant: Optional[str] = None,
) -> str:
    """Legacy function signature - wraps render_infographic."""
    return render_infographic(
        headline=data.get("headline", ""),
        points=data.get("key_points", data.get("points", [])),
        category=data.get("category", "general"),
        background_image_path=data.get("background_image_path", ""),
        source_attribution=data.get("source_attribution", ""),
        watermark_text=data.get("watermark_text", "Ilustrasi AI"),
        output_path=output_path,
    )