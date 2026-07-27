# Instruksi Scaffolding Project: IG News Automation Agent

Gunakan file ini sebagai prompt untuk AI coding agent (Claude Code, Cursor, atau agent lain) untuk membuat scaffolding lengkap project ini. Salin seluruh isi file ini sebagai instruksi awal.

---

## Konteks project

Buatkan scaffolding untuk project Python bernama `ig-news-agent`. Project ini adalah automation agent yang:
1. Mengambil berita viral dari RSS feed/News API
2. Memfilter & scoring kelayakan berita pakai LLM (viral potential, credibility, sensitivity)
3. Generate teks ringkasan & caption pakai LLM
4. Render infografis dari template HTML ke gambar (Playwright)
5. Upload gambar ke cloud storage (Cloudinary)
6. Publish otomatis ke Instagram via Graph API (dengan rate limit 25 post/24 jam)
7. Punya opsi human-in-the-loop review via Telegram bot sebelum publish
8. Punya **publisher yang bisa di-switch** lewat 1 environment variable, tanpa ubah kode: `mock` (testing lokal, tidak hit API apapun), `telegram_preview` (kirim hasil render ke channel Telegram untuk cek visual nyata), atau `instagram` (publish sungguhan setelah Graph API disetujui). Ini penting karena approval Instagram Graph API bisa makan waktu 2-4 minggu, jadi seluruh pipeline harus bisa ditest end-to-end sebelum akses IG API didapat.

## Tugas yang harus dikerjakan agent

1. Buat seluruh struktur folder dan file kosong (atau berisi boilerplate minimal) sesuai folder tree di bawah.
2. Setiap file Python harus punya docstring modul di baris paling atas yang menjelaskan tanggung jawab file tersebut (1-3 kalimat), sesuai deskripsi pada tabel "Detail per file" di bawah.
3. Isi `requirements.txt` dengan dependency yang sesuai (lihat bagian Dependencies).
4. Isi `.env.example` dengan semua environment variable yang dibutuhkan (lihat bagian Environment Variables), tanpa nilai asli.
5. Isi `.gitignore` standar Python + tambahan `.env`, `logs/*.log`, `__pycache__/`, `.venv/`.
6. Setup virtual environment dan install dependencies dari `requirements.txt`.
7. Inisialisasi git repository dengan commit pertama "Initial project scaffolding".
8. JANGAN mengisi logic bisnis (isi fungsi) di file-file `src/` — cukup buat struktur, docstring, import yang relevan, dan function/class signature kosong (pakai `pass` atau `raise NotImplementedError`). Logic akan diisi bertahap di sesi berikutnya.
9. **KECUALI** untuk folder `src/publishing/` — ini HARUS diisi logic lengkap dan berfungsi sesuai kode di bagian "Publisher abstraction (wajib diisi penuh)" di bawah. Bagian ini adalah fondasi testing sebelum IG API disetujui, jadi tidak boleh kosong.
10. Setelah selesai, tampilkan folder tree final untuk verifikasi.

## Folder tree lengkap

```
ig-news-agent/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── docker-compose.yml
│
├── config/
│   ├── settings.py
│   ├── sources.yaml
│   └── logging.yaml
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── rss_fetcher.py
│   │   ├── news_api_client.py
│   │   ├── deduplicator.py
│   │   └── freshness_filter.py
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── news_scorer.py
│   │   ├── sensitivity_guard.py
│   │   └── cross_verification.py
│   │
│   ├── content_generation/
│   │   ├── __init__.py
│   │   ├── summarizer.py
│   │   ├── caption_writer.py
│   │   └── prompts/
│   │       ├── scoring_prompt.txt
│   │       ├── summarize_prompt.txt
│   │       └── caption_prompt.txt
│   │
│   ├── design/
│   │   ├── __init__.py
│   │   ├── template_renderer.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── style.css
│   │   │   └── variants/
│   │   │       ├── breaking_news.html
│   │   │       ├── entertainment.html
│   │   │       └── general.html
│   │   └── assets/
│   │       ├── fonts/
│   │       └── logo.png
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── cloudinary_client.py
│   │
│   ├── publishing/
│   │   ├── __init__.py
│   │   ├── base_publisher.py
│   │   ├── mock_publisher.py
│   │   ├── telegram_preview_publisher.py
│   │   ├── ig_client.py
│   │   ├── publisher_factory.py
│   │   └── rate_limiter.py
│   │
│   ├── review/
│   │   ├── __init__.py
│   │   ├── telegram_bot.py
│   │   └── review_queue.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── db.py
│   │   └── migrations/
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── scheduler.py
│   │   └── pipeline.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── retry.py
│
├── scripts/
│   ├── run_pipeline_once.py
│   ├── backfill_history.py
│   └── test_ig_connection.py
│
├── tests/
│   ├── __init__.py
│   ├── test_deduplicator.py
│   ├── test_news_scorer.py
│   ├── test_template_renderer.py
│   └── fixtures/
│       └── sample_news.json
│
├── logs/
│   └── .gitkeep
│
└── mock_output/
    └── .gitkeep
```

## Detail per file (docstring yang harus ditulis)

| File | Docstring / isi minimal |
|---|---|
| `config/settings.py` | Load semua environment variable via `python-dotenv`, definisikan konstanta global (threshold skor, rate limit, dsb) sebagai class/dataclass `Settings` |
| `config/sources.yaml` | Daftar RSS feed & sumber berita whitelist (isi contoh 3-5 sumber media Indonesia sebagai placeholder) |
| `config/logging.yaml` | Konfigurasi logging standar Python (format, level, file handler ke `logs/`) |
| `src/ingestion/rss_fetcher.py` | Fetch entries dari RSS feed pakai `feedparser`, return list berita mentah |
| `src/ingestion/news_api_client.py` | Wrapper client untuk News API pihak ketiga (opsional, siapkan interface generic) |
| `src/ingestion/deduplicator.py` | Fuzzy matching judul berita terhadap history di database, pakai `rapidfuzz` |
| `src/ingestion/freshness_filter.py` | Filter berita berdasarkan umur (timestamp publish vs sekarang) |
| `src/scoring/llm_client.py` | Wrapper generic untuk panggil Claude/OpenAI API, handle retry & rate limit |
| `src/scoring/news_scorer.py` | Fungsi `score_news(item) -> ScoreResult` yang panggil LLM dengan `scoring_prompt.txt`, return skor terstruktur (viral_potential, credibility_score, is_sensitive, is_verified_multi_source) |
| `src/scoring/sensitivity_guard.py` | Cek kategori sensitif (SARA, kematian, bencana, politik/hukum belum inkrah) |
| `src/scoring/cross_verification.py` | Cek apakah berita muncul di >1 sumber kredibel sebelum dianggap terverifikasi |
| `src/content_generation/summarizer.py` | Parafrase berita jadi poin-poin ringkas untuk infografis (bukan copy-paste teks asli) |
| `src/content_generation/caption_writer.py` | Generate caption Instagram + hashtag relevan |
| `src/content_generation/prompts/*.txt` | Template prompt LLM, tulis sebagai file teks biasa (bukan hardcoded di Python) |
| `src/design/template_renderer.py` | Render HTML+CSS template menjadi PNG/JPEG pakai Playwright, isi data dinamis ke template |
| `src/design/templates/*.html` | Template HTML dasar untuk infografis, beberapa varian sesuai kategori berita |
| `src/storage/cloudinary_client.py` | Upload gambar ke Cloudinary, return URL publik |
| `src/publishing/base_publisher.py` | Abstract class `BasePublisher` dengan method `publish(image_url, caption) -> dict` — diisi penuh, lihat bagian "Publisher abstraction" |
| `src/publishing/mock_publisher.py` | Simulasi publish tanpa hit API apapun — log ke console + simpan metadata JSON ke `mock_output/`, diisi penuh |
| `src/publishing/telegram_preview_publisher.py` | Kirim gambar hasil render + caption ke channel/chat Telegram untuk preview visual nyata (real API call, bukan mock) — diisi penuh |
| `src/publishing/ig_client.py` | Auth ke Instagram Graph API, create media container, publish. Class `InstagramPublisher` extends `BasePublisher`, tapi implementasi Graph API-nya boleh kosong (`raise NotImplementedError`) sampai akses API disetujui |
| `src/publishing/publisher_factory.py` | Fungsi `get_publisher()` yang baca `PUBLISH_MODE` dari env dan return instance publisher yang sesuai — diisi penuh, lihat bagian "Publisher abstraction" |
| `src/publishing/rate_limiter.py` | Jaga batas maksimal 25 post per 24 jam per akun |
| `src/review/telegram_bot.py` | Kirim preview infografis + skor ke Telegram untuk approve/reject manual |
| `src/review/review_queue.py` | Antrian berita yang menunggu approval manual |
| `src/database/models.py` | SQLAlchemy models: `NewsItem`, `Post`, `ScoreLog`, `ReviewLog` |
| `src/database/db.py` | Koneksi & session database (PostgreSQL/Supabase) |
| `src/scheduler/scheduler.py` | Job scheduling pakai APScheduler atau cron wrapper |
| `src/scheduler/pipeline.py` | Orchestrate seluruh alur: ingest → dedup → score → generate → render → upload → (review) → publish → log |
| `src/utils/logger.py` | Setup logger terpusat |
| `src/utils/retry.py` | Decorator retry untuk API call yang gagal (exponential backoff) |
| `scripts/run_pipeline_once.py` | CLI script untuk jalankan satu siklus pipeline penuh secara manual (untuk testing) |
| `scripts/backfill_history.py` | Import histori posting lama ke database (kalau ada data existing) |
| `scripts/test_ig_connection.py` | Script kecil untuk test koneksi & auth ke Instagram Graph API saja |
| `tests/*` | Unit test dasar (pakai `pytest`) untuk komponen kritikal: dedup, scorer, renderer |

## Dependencies (`requirements.txt`)

```
python-dotenv
pyyaml
feedparser
rapidfuzz
anthropic
sqlalchemy
psycopg2-binary
alembic
playwright
cloudinary
requests
apscheduler
python-telegram-bot
pytest
tenacity
```

> `python-telegram-bot` dipakai untuk dua hal: `review/telegram_bot.py` (approval manual) dan `publishing/telegram_preview_publisher.py` (mode preview). Satu bot Telegram yang sama bisa dipakai untuk keduanya, cukup beda chat/channel tujuan.

## Environment Variables (`.env.example`)

```
# LLM
ANTHROPIC_API_KEY=

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ig_news_agent

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Instagram Graph API
IG_ACCESS_TOKEN=
IG_BUSINESS_ACCOUNT_ID=
FB_APP_ID=
FB_APP_SECRET=

# Telegram (dipakai untuk review bot DAN telegram_preview_publisher)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_PREVIEW_CHAT_ID=

# App config
POST_SCORE_THRESHOLD_VIRAL=7
POST_SCORE_THRESHOLD_CREDIBILITY=6
MAX_POSTS_PER_DAY=10
REVIEW_MODE=manual

# Publisher mode: mock | telegram_preview | instagram
PUBLISH_MODE=mock
```

## Publisher abstraction (wajib diisi penuh)

Bagian ini adalah pengecualian dari aturan "jangan isi logic bisnis". Isi keempat file berikut persis seperti kode di bawah, supaya seluruh pipeline bisa langsung ditest sekarang (mode `mock`), lalu dicek visual nyata (mode `telegram_preview`), dan tinggal switch ke `instagram` begitu Graph API disetujui — **tanpa mengubah kode di modul lain manapun**.

### `src/publishing/base_publisher.py`

```python
"""Interface abstrak untuk semua publisher (mock, telegram preview, instagram).
Semua publisher harus implement method publish() dengan signature yang sama,
supaya bisa saling ditukar tanpa mengubah kode pemanggil (pipeline.py)."""

from abc import ABC, abstractmethod


class BasePublisher(ABC):
    @abstractmethod
    def publish(self, image_path_or_url: str, caption: str) -> dict:
        """Publish satu konten (gambar + caption).

        Args:
            image_path_or_url: path lokal gambar (mock, telegram) atau
                URL publik gambar (instagram, yang butuh hosting).
            caption: teks caption yang akan disertakan.

        Returns:
            dict dengan minimal key: {"status": "success"|"failed",
            "post_id": str, "mode": str, "error": str | None}
        """
        raise NotImplementedError
```

### `src/publishing/mock_publisher.py`

```python
"""Publisher untuk testing lokal. Tidak memanggil API eksternal apapun.
Menyimpan metadata publish (caption, path gambar, timestamp) sebagai JSON
di folder mock_output/, supaya hasil pipeline bisa diaudit manual."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.publishing.base_publisher import BasePublisher

logger = logging.getLogger(__name__)

MOCK_OUTPUT_DIR = Path("mock_output")


class MockPublisher(BasePublisher):
    def publish(self, image_path_or_url: str, caption: str) -> dict:
        MOCK_OUTPUT_DIR.mkdir(exist_ok=True)
        post_id = f"mock_{uuid.uuid4().hex[:8]}"
        record = {
            "post_id": post_id,
            "image": image_path_or_url,
            "caption": caption,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "mock",
        }
        out_path = MOCK_OUTPUT_DIR / f"{post_id}.json"
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False))

        logger.info("[MOCK POST] %s -> %s", post_id, out_path)
        logger.info("[MOCK POST] caption preview: %s...", caption[:80])

        return {"status": "success", "post_id": post_id, "mode": "mock", "error": None}
```

### `src/publishing/telegram_preview_publisher.py`

```python
"""Publisher yang mengirim hasil render infografis ke channel/chat Telegram
untuk preview visual nyata. Ini API call sungguhan (bukan mock), tapi tujuannya
untuk QA visual sebelum Instagram Graph API disetujui, bukan publish ke publik."""

import logging
import os

import requests

from src.publishing.base_publisher import BasePublisher

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendPhoto"


class TelegramPreviewPublisher(BasePublisher):
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_PREVIEW_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN dan TELEGRAM_PREVIEW_CHAT_ID wajib diisi di .env "
                "untuk memakai mode telegram_preview"
            )

    def publish(self, image_path_or_url: str, caption: str) -> dict:
        url = TELEGRAM_API_BASE.format(token=self.token)
        try:
            with open(image_path_or_url, "rb") as img_file:
                response = requests.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption[:1024]},
                    files={"photo": img_file},
                    timeout=30,
                )
            response.raise_for_status()
            message_id = response.json()["result"]["message_id"]
            logger.info("[TELEGRAM PREVIEW] sent, message_id=%s", message_id)
            return {
                "status": "success",
                "post_id": str(message_id),
                "mode": "telegram_preview",
                "error": None,
            }
        except Exception as exc:
            logger.exception("[TELEGRAM PREVIEW] gagal kirim")
            return {
                "status": "failed",
                "post_id": None,
                "mode": "telegram_preview",
                "error": str(exc),
            }
```

### `src/publishing/publisher_factory.py`

```python
"""Factory untuk memilih publisher aktif berdasarkan environment variable
PUBLISH_MODE. Ini satu-satunya tempat yang perlu diubah ketika beralih dari
testing (mock/telegram_preview) ke publish sungguhan (instagram)."""

import os

from src.publishing.base_publisher import BasePublisher
from src.publishing.mock_publisher import MockPublisher
from src.publishing.telegram_preview_publisher import TelegramPreviewPublisher


def get_publisher() -> BasePublisher:
    mode = os.getenv("PUBLISH_MODE", "mock").lower()

    if mode == "mock":
        return MockPublisher()
    elif mode == "telegram_preview":
        return TelegramPreviewPublisher()
    elif mode == "instagram":
        from src.publishing.ig_client import InstagramPublisher
        return InstagramPublisher()
    else:
        raise ValueError(
            f"PUBLISH_MODE tidak dikenal: '{mode}'. "
            "Gunakan salah satu: mock | telegram_preview | instagram"
        )
```

**Cara switch nanti setelah IG API disetujui:**
1. Isi logic `InstagramPublisher` di `src/publishing/ig_client.py` (auth, create container, publish).
2. Ubah `.env`: `PUBLISH_MODE=instagram`.
3. Isi `IG_ACCESS_TOKEN` dan `IG_BUSINESS_ACCOUNT_ID` di `.env`.
4. Tidak ada file lain yang perlu diubah — `pipeline.py` memanggil `get_publisher()` dan otomatis dapat instance yang benar.

Di `pipeline.py`, pemanggilannya cukup seperti ini (agent boleh tulis contoh ini sebagai referensi, walau `pipeline.py` sendiri masih boleh kosong sesuai aturan no. 8):

```python
from src.publishing.publisher_factory import get_publisher

publisher = get_publisher()
result = publisher.publish(image_path_or_url=rendered_image_path, caption=caption_text)
```

## Setelah scaffolding selesai

Agent harus menjalankan verifikasi berikut dan melaporkan hasilnya:
1. `python -m venv .venv && source .venv/bin/activate` (atau equivalent Windows)
2. `pip install -r requirements.txt`
3. `playwright install chromium` (untuk template renderer)
4. Tampilkan struktur folder final dengan `tree` atau equivalent
5. Konfirmasi tidak ada error import di setiap modul (`python -m compileall src/`)
6. Jalankan smoke test singkat untuk memastikan `MockPublisher` berfungsi:
   ```python
   from src.publishing.publisher_factory import get_publisher
   publisher = get_publisher()  # default PUBLISH_MODE=mock
   result = publisher.publish("dummy.jpg", "Test caption dari scaffolding")
   print(result)
   ```
   Konfirmasi file JSON baru muncul di `mock_output/` dan `result["status"] == "success"`.

## Catatan penting untuk agent

- Jangan isi API key asli di manapun. `.env` boleh dibuat kosong/dengan placeholder, `.env.example` adalah template referensi.
- Jangan install atau konfigurasi apapun yang melakukan publish sungguhan ke Instagram pada tahap scaffolding ini.
- Struktur folder harus persis seperti di atas — jangan menambah/mengurangi tanpa konfirmasi terlebih dahulu.
