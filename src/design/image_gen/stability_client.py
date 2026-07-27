"""Implementasi asli image generation via Stability AI API.
Bisa diganti ke provider lain (Replicate/Flux, DALL-E, dll) dengan
membuat class baru yang extend BaseImageGen — tidak perlu ubah compositor.py."""

import logging
import os

import requests

from src.design.image_gen.base_image_gen import BaseImageGen

logger = logging.getLogger(__name__)

STABILITY_API_URL = (
    "https://api.stability.ai/v2beta/stable-image/generate/core"
)

# Ditambahkan otomatis ke setiap prompt untuk menghindari generate wajah
# tokoh publik/orang nyata secara spesifik pada konten berita.
SAFETY_SUFFIX = (
    ", abstract symbolic illustration, no realistic human faces, "
    "no specific real people, editorial illustration style"
)


class StabilityImageGen(BaseImageGen):
    def __init__(self):
        self.api_key = os.getenv("STABILITY_API_KEY")
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY belum diisi di .env")

    def generate(self, prompt: str, output_path: str) -> str:
        full_prompt = f"{prompt}{SAFETY_SUFFIX}"
        response = requests.post(
            STABILITY_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "image/*",
            },
            files={"none": ""},
            data={
                "prompt": full_prompt,
                "output_format": "jpeg",
                "aspect_ratio": "1:1",
            },
            timeout=60,
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("[STABILITY] generated -> %s", output_path)
        return output_path