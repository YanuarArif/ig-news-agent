"""Factory untuk memilih image generator aktif berdasarkan env var
IMAGE_GEN_PROVIDER. Sama pola dengan publisher_factory.py."""

import os

from src.design.image_gen.base_image_gen import BaseImageGen
from src.design.image_gen.mock_image_gen import MockImageGen


def get_image_gen() -> BaseImageGen:
    provider = os.getenv("IMAGE_GEN_PROVIDER", "mock").lower()

    if provider == "mock":
        return MockImageGen()
    elif provider == "stability":
        from src.design.image_gen.stability_client import StabilityImageGen
        return StabilityImageGen()
    elif provider == "cloudflare_workers":
        from src.design.image_gen.cloudflare_workers_gen import CloudflareWorkersImageGen
        return CloudflareWorkersImageGen()
    else:
        raise ValueError(
            f"IMAGE_GEN_PROVIDER tidak dikenal: '{provider}'. "
            "Gunakan salah satu: mock | stability | cloudflare_workers"
        )