"""Image generator untuk testing lokal. Tidak memanggil API generation
apapun (menghindari biaya saat development) — cukup bikin gradient/warna
solid sesuai kategori, supaya pipeline bisa ditest end-to-end dulu."""

import logging

from PIL import Image, ImageDraw

from src.design.image_gen.base_image_gen import BaseImageGen

logger = logging.getLogger(__name__)

CATEGORY_COLORS = {
    "breaking_news": [(178, 34, 34), (60, 10, 10)],
    "entertainment": [(255, 183, 77), (255, 87, 34)],
    "general": [(69, 90, 100), (33, 33, 33)],
    "tech": [(0, 188, 212), (0, 96, 100)],
    "sports": [(76, 175, 80), (27, 94, 32)],
    "health": [(0, 150, 136), (0, 77, 64)],
}


class MockImageGen(BaseImageGen):
    def generate(self, prompt: str, output_path: str) -> str:
        category = "general"
        for key in CATEGORY_COLORS:
            if key in prompt.lower():
                category = key
                break

        top, bottom = CATEGORY_COLORS[category]
        img = Image.new("RGB", (1080, 1080), top)
        draw = ImageDraw.Draw(img)
        for y in range(1080):
            ratio = y / 1080
            color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
            draw.line([(0, y), (1080, y)], fill=color)

        # Ensure output directory exists
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        img.save(output_path)
        logger.info("[MOCK IMAGE GEN] saved gradient placeholder -> %s", output_path)
        return output_path