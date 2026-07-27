"""Menyusun prompt image generation berdasarkan kategori & mood berita.
Tetap abstrak/simbolis — TIDAK menyebut nama orang/tokoh spesifik dari
berita, untuk menghindari AI generate wajah yang menyesatkan."""

CATEGORY_PROMPTS = {
    "breaking_news": (
        "urgent breaking news background, bold red and dark tones, "
        "abstract geometric shapes, high contrast, editorial design"
    ),
    "entertainment": (
        "vibrant playful background, warm orange and yellow gradient, "
        "abstract celebratory shapes, modern editorial design"
    ),
    "general": (
        "clean modern news background, cool blue-gray tones, "
        "abstract minimal shapes, editorial design"
    ),
    "tech": (
        "futuristic technology background, cyan and blue neon accents, "
        "abstract circuit patterns, digital editorial design"
    ),
    "sports": (
        "dynamic sports background, energetic green and white, "
        "abstract motion lines and shapes, modern editorial design"
    ),
    "health": (
        "calm healthcare background, teal and mint gradients, "
        "abstract molecular and organic shapes, editorial design"
    ),
    "business": (
        "professional business background, dark blue and gold accents, "
        "abstract chart and growth patterns, editorial design"
    ),
    "politics": (
        "serious political news background, deep navy and red tones, "
        "abstract institutional architecture shapes, editorial design"
    ),
}


def build_prompt(category: str) -> str:
    return CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["general"])