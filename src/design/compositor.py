"""Menggabungkan background hasil AI image generation dengan teks
(headline, poin ringkasan, atribusi sumber) via template HTML/CSS yang
di-render Playwright. Background AI hanya elemen visual — semua teks
tetap dari HTML/CSS supaya terbaca presisi."""

import logging
from pathlib import Path

from src.design.image_gen.image_gen_factory import get_image_gen
from src.design.image_prompt_builder import build_prompt
from src.design.template_renderer import render_infographic

logger = logging.getLogger(__name__)

TEMP_DIR = Path("tmp_design")


def build_infographic(summary: dict, source_attribution: str) -> str:
    """Pipeline lengkap: generate background AI -> render template dengan
    background itu + teks overlay -> return path gambar final."""

    TEMP_DIR.mkdir(exist_ok=True)
    category = summary.get("category", "general")

    # 1. Generate background AI (mock atau real, tergantung IMAGE_GEN_PROVIDER)
    image_gen = get_image_gen()
    prompt = build_prompt(category)
    background_path = TEMP_DIR / f"bg_{category}.jpg"
    image_gen.generate(prompt, str(background_path))

    # 2. Render template HTML/CSS dengan background itu + teks overlay
    final_path = render_infographic(
        headline=summary["headline"],
        points=summary["points"],
        category=category,
        background_image_path=str(background_path),
        source_attribution=source_attribution,
        watermark_text="Ilustrasi AI",  # transparansi wajib untuk konten berita
    )

    logger.info("Infografis final: %s", final_path)
    return final_path