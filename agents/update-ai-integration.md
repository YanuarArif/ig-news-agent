# Update: Integrasi AI (Summary, Caption, Desain Infografis)

File ini adalah **update tambahan** untuk project `ig-news-agent` yang scaffolding awalnya sudah dibuat dari `scaffold-instructions.md`. Jalankan file ini SETELAH scaffolding awal selesai — jangan dari nol.

Salin seluruh isi file ini sebagai prompt lanjutan ke AI coding agent (Claude Code/Cursor/dll).

---

## Apa yang ditambahkan di update ini

Sebelumnya `summarizer.py`, `caption_writer.py`, dan `template_renderer.py` masih kosong (signature doang). Update ini mengisi 3 kemampuan AI yang belum ada:

1. **AI summary berita** — LLM (Claude) meringkas & memparafrase berita jadi poin-poin untuk infografis.
2. **AI caption Instagram** — LLM menulis caption + hashtag berdasarkan berita & ringkasan.
3. **AI desain infografis** — AI image generation membuat background/ilustrasi abstrak sesuai kategori berita, lalu teks di-overlay di atasnya lewat template HTML/CSS (bukan AI yang nulis teksnya langsung ke gambar).

Sama seperti `publishing/`, folder `src/scoring/` (bagian summarizer & caption), dan `src/design/image_gen/` di update ini **dikecualikan dari aturan "jangan isi logic"** — harus diisi penuh dan berfungsi.

## Kenapa desain background & teks dipisah (penting dibaca)

AI image generation (Stable Diffusion, DALL-E, Flux, dll) masih buruk kalau disuruh render teks panjang/presisi langsung di gambar — hasilnya sering typo, huruf aneh, atau tidak terbaca. Karena itu:

- AI image gen **hanya** bikin elemen visual: background abstrak, ilustrasi simbolis, tekstur, gradient sesuai mood berita (breaking news = merah/urgent, hiburan = cerah/playful, dst).
- Teks (judul, poin ringkasan, atribusi sumber, logo) tetap di-render lewat HTML/CSS + Playwright seperti arsitektur sebelumnya — supaya 100% terbaca dan konsisten brand.
- **Guardrail penting**: prompt untuk image generation harus diarahkan ke ilustrasi abstrak/simbolis, JANGAN prompt yang menghasilkan wajah orang nyata/tokoh publik spesifik — ini menghindari risiko gambar menyesatkan (mirip deepfake) yang bisa berbahaya untuk konten berita.
- **Wajib ada watermark kecil "Ilustrasi AI"** di pojok infografis, supaya audience tahu background-nya bukan foto asli kejadian — ini praktik transparansi yang penting khusus untuk konten berita.

## Folder tambahan

```
src/
├── scoring/
│   ├── llm_client.py               # (sudah ada, sekarang diisi penuh)
│   ├── news_scorer.py              # (sudah ada, sekarang diisi penuh)
│
├── content_generation/
│   ├── summarizer.py                # diisi penuh — panggil llm_client
│   ├── caption_writer.py            # diisi penuh — panggil llm_client
│
├── design/
│   ├── template_renderer.py         # diisi penuh — terima background_image_path
│   ├── image_prompt_builder.py      # BARU — susun prompt image gen dari kategori berita
│   ├── image_gen/                   # BARU
│   │   ├── __init__.py
│   │   ├── base_image_gen.py        # interface, sama pola dengan base_publisher.py
│   │   ├── mock_image_gen.py        # generate gradient/warna solid lokal, tanpa API call
│   │   ├── stability_client.py      # implementasi asli via Stability AI API
│   │   └── image_gen_factory.py     # baca IMAGE_GEN_PROVIDER dari env
│   └── compositor.py                # BARU — gabungkan background AI + overlay teks
```

## 1. LLM client (dasar untuk summary & caption)

### `src/scoring/llm_client.py`

```python
"""Wrapper generic untuk memanggil Claude API. Dipakai bersama oleh
news_scorer.py, summarizer.py, dan caption_writer.py supaya retry &
error handling konsisten di satu tempat."""

import os
import logging

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"  # cek docs.claude.com untuk model terbaru


class LLMClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY belum diisi di .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
```

## 2. AI summary berita

### `src/content_generation/prompts/summarize_prompt.txt`

```
Kamu adalah editor infografis berita untuk Instagram. Tugasmu meringkas
berita berikut menjadi 3-5 poin singkat (maksimal 15 kata per poin) dalam
Bahasa Indonesia yang mudah dibaca di infografis.

ATURAN PENTING:
- JANGAN copy-paste kalimat asli dari berita. Tulis ulang dengan kata sendiri.
- Fokus pada fakta inti: apa, siapa, kapan, di mana, kenapa penting.
- Netral, tidak dramatisir, tidak clickbait.
- Jangan tambahkan informasi yang tidak ada di teks asli.

Output HANYA dalam format JSON:
{
  "headline": "judul singkat maks 8 kata",
  "points": ["poin 1", "poin 2", "poin 3"],
  "category": "breaking_news | entertainment | general"
}
```

### `src/content_generation/summarizer.py`

```python
"""Meringkas & memparafrase berita jadi poin-poin untuk infografis,
menggunakan Claude API. TIDAK boleh copy-paste teks asli (hak cipta)."""

import json
import logging
from pathlib import Path

from src.scoring.llm_client import LLMClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "summarize_prompt.txt"


class NewsSummarizer:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def summarize(self, news_title: str, news_body: str) -> dict:
        user_prompt = f"Judul: {news_title}\n\nIsi berita:\n{news_body}"
        raw = self.llm.complete(self.system_prompt, user_prompt, max_tokens=512)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Gagal parse JSON dari LLM: %s", raw)
            raise
```

## 3. AI caption Instagram

### `src/content_generation/prompts/caption_prompt.txt`

```
Kamu adalah social media manager akun berita Instagram Indonesia.
Berdasarkan ringkasan berita berikut, tulis caption Instagram yang:
- Menarik tapi tidak clickbait/menyesatkan
- 2-4 kalimat pembuka + call-to-action ringan (misal ajak komentar pendapat)
- Diakhiri 5-8 hashtag relevan (campuran hashtag umum & spesifik topik)
- Sertakan atribusi singkat ke sumber berita asli
- Bahasa Indonesia santai tapi tetap sopan, tanpa emoji berlebihan (maks 3 emoji)

Output HANYA dalam format JSON:
{
  "caption": "teks caption lengkap termasuk hashtag",
  "source_attribution": "Sumber: Nama Media"
}
```

### `src/content_generation/caption_writer.py`

```python
"""Menulis caption Instagram + hashtag berdasarkan ringkasan berita,
menggunakan Claude API."""

import json
import logging
from pathlib import Path

from src.scoring.llm_client import LLMClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "caption_prompt.txt"


class CaptionWriter:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def write_caption(self, summary: dict, source_name: str) -> dict:
        user_prompt = (
            f"Headline: {summary['headline']}\n"
            f"Poin: {'; '.join(summary['points'])}\n"
            f"Sumber: {source_name}"
        )
        raw = self.llm.complete(self.system_prompt, user_prompt, max_tokens=400)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Gagal parse JSON dari LLM: %s", raw)
            raise
```

## 4. AI image generation untuk background infografis

### `src/design/image_gen/base_image_gen.py`

```python
"""Interface abstrak untuk semua image generator (mock, stability, dll).
Sama pola dengan BasePublisher — supaya provider bisa ditukar tanpa
mengubah kode compositor.py."""

from abc import ABC, abstractmethod


class BaseImageGen(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: str) -> str:
        """Generate 1 gambar background dari prompt, simpan ke output_path.

        Returns:
            path file gambar yang dihasilkan (sama dengan output_path).
        """
        raise NotImplementedError
```

### `src/design/image_gen/mock_image_gen.py`

```python
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

        img.save(output_path)
        logger.info("[MOCK IMAGE GEN] saved gradient placeholder -> %s", output_path)
        return output_path
```

### `src/design/image_gen/stability_client.py`

```python
"""Implementasi asli image generation via Stability AI API.
Bisa diganti ke provider lain (Replicate/Flux, DALL-E, dll) dengan
membuat class baru yang extend BaseImageGen — tidak perlu ubah compositor.py."""

import base64
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
```

### `src/design/image_gen/image_gen_factory.py`

```python
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
    else:
        raise ValueError(
            f"IMAGE_GEN_PROVIDER tidak dikenal: '{provider}'. "
            "Gunakan salah satu: mock | stability"
        )
```

## 5. Prompt builder untuk image generation

### `src/design/image_prompt_builder.py`

```python
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
}


def build_prompt(category: str) -> str:
    return CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["general"])
```

## 6. Compositor — gabungkan background AI + teks overlay

### `src/design/compositor.py`

```python
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
```

### Update `src/design/template_renderer.py`

Fungsi `render_infographic()` sekarang menerima parameter tambahan `background_image_path` dan `watermark_text`, lalu inject ke template HTML sebagai `background-image: url(...)` dan elemen watermark kecil di pojok bawah. Signature yang harus dibuat agent:

```python
def render_infographic(
    headline: str,
    points: list[str],
    category: str,
    background_image_path: str,
    source_attribution: str,
    watermark_text: str = "Ilustrasi AI",
) -> str:
    """Render template HTML (variants/{category}.html) menjadi JPEG,
    dengan background_image_path sebagai background-image, dan overlay
    headline/points/source_attribution/watermark_text sebagai teks HTML.
    Return path file JPEG hasil render (untuk dipakai compositor.py)."""
    ...
```

## Dependencies tambahan (`requirements.txt`)

```
pillow
```

(`anthropic` dan `requests` sudah ada dari scaffolding awal)

## Environment Variables tambahan (`.env.example`)

```
# AI Image Generation
IMAGE_GEN_PROVIDER=mock
STABILITY_API_KEY=
```

## Update pipeline.py (referensi, boleh tetap kosong sesuai aturan awal)

```python
from src.content_generation.summarizer import NewsSummarizer
from src.content_generation.caption_writer import CaptionWriter
from src.design.compositor import build_infographic
from src.publishing.publisher_factory import get_publisher

summarizer = NewsSummarizer()
caption_writer = CaptionWriter()

summary = summarizer.summarize(news_title, news_body)
caption_data = caption_writer.write_caption(summary, source_name)
image_path = build_infographic(summary, caption_data["source_attribution"])

publisher = get_publisher()
result = publisher.publish(image_path, caption_data["caption"])
```

## Verifikasi setelah update ini

1. `pip install -r requirements.txt` (pastikan `pillow` terinstall)
2. Smoke test summarizer (butuh `ANTHROPIC_API_KEY` asli di `.env`):
   ```python
   from src.content_generation.summarizer import NewsSummarizer
   s = NewsSummarizer()
   print(s.summarize("Judul contoh", "Isi berita contoh untuk testing..."))
   ```
3. Smoke test image gen mock (tidak butuh API key apapun):
   ```python
   from src.design.image_gen.image_gen_factory import get_image_gen
   gen = get_image_gen()  # default IMAGE_GEN_PROVIDER=mock
   gen.generate("breaking_news test", "tmp_design/test.jpg")
   ```
   Konfirmasi file `tmp_design/test.jpg` muncul (gradient warna sesuai kategori).
4. Konfirmasi `mock_output/` dan `tmp_design/` sudah ada di `.gitignore`.

## Catatan penting

- **Biaya**: setiap panggilan LLM (summary + caption) dan image generation (kalau bukan mock) kena biaya per call. Untuk 5-10 post/hari, hitung estimasi biaya bulanan sebelum switch dari `mock` ke provider asli.
- **Ganti provider image gen**: kalau nanti mau pindah dari Stability AI ke provider lain (Replicate/Flux, DALL-E), cukup buat class baru extend `BaseImageGen`, daftarkan di `image_gen_factory.py` — tidak perlu ubah `compositor.py`.
- **Transparansi konten AI**: watermark "Ilustrasi AI" di infografis sebaiknya tidak dihapus — ini melindungi kamu dari tuduhan menyebarkan gambar asli kejadian yang sebenarnya bukan foto sungguhan.
