# IG News Automation Agent

Automasi end-to-end untuk mengambil berita viral, scoring dengan LLM, generate konten infografis, dan publish ke Instagram (dengan mode testing mock/telegram_preview).

## 📋 Deskripsi Project

Project ini adalah **IG News Automation Agent** — sebuah automation agent Python yang mengotomatiskan seluruh pipeline pembuatan konten berita untuk Instagram, mulai dari pengambilan berita hingga publishing. Didesain dengan arsitektur modular dan **publisher abstraction** yang memungkinkan switching mode publish via 1 environment variable tanpa mengubah kode.

### Alur Kerja Pipeline

```
RSS/News API → Deduplicasi & Freshness Filter → LLM Scoring → Content Generation → Template Rendering → Cloudinary Upload → (Review Manual) → Publish ke Instagram
```

### Fitur Utama

| # | Fitur | Deskripsi |
|---|-------|-----------|
| 1 | **Ingestion** | Fetch berita dari RSS feeds & News API (feedparser + generic News API client) |
| 2 | **Deduplication & Freshness** | Fuzzy matching judul (rapidfuzz) + filter umur berita berdasarkan timestamp |
| 3 | **LLM Scoring** | Viral potential, credibility score, sensitivity guard, cross-verification multi-source |
| 4 | **Content Generation** | Summarizer (parafrase untuk infografis) + Caption writer (IG style + hashtag) |
| 5 | **Design Rendering** | HTML/CSS template → PNG/JPEG via Playwright (varian: breaking_news, entertainment, general) |
| 6 | **Cloud Storage** | Upload gambar ke Cloudinary, return public URL |
| 7 | **Switchable Publisher** | **mock** (lokal, simpan JSON) \| **telegram_preview** (QA visual via Telegram) \| **instagram** (Graph API) |
| 8 | **Human-in-the-loop Review** | Telegram bot untuk approve/reject manual sebelum publish |
| 9 | **Rate Limiting** | Enforce max 25 post/24 jam (sliding window) |
| 10 | **Scheduling** | APScheduler untuk pipeline otomatis berkala |
| 11 | **Database** | SQLAlchemy + PostgreSQL/Supabase (NewsItem, Post, ScoreLog, ReviewLog) |

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Buat virtual environment
python -m venv .venv

# Aktifkan (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Aktifkan (Linux/macOS/Git Bash)
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Konfigurasi Environment

```bash
# Copy template environment
cp .env.example .env

# Edit .env dengan credentials Anda
# Minimal untuk testing mode mock: tidak perlu isi API key apapun
```

### 4. Jalankan Pipeline (Mode Testing Mock)

```bash
# Jalankan satu siklus pipeline penuh (MUST run as module)
python -m scripts.run_pipeline_once

# Cek hasil mock output
ls mock_output/
cat mock_output/*.json
```

> **⚠️ Penting**: Selalu jalankan `python -m scripts.run_pipeline_once` (bukan `python scripts/run_pipeline_once.py`) agar path import `src/` berfungsi dengan benar.

---

## 🔄 Publisher Modes (Fitur Kunci)

Ini adalah **fitur utama** yang membedakan project ini — publisher bisa di-switch via **1 environment variable** tanpa ubah kode:

| Mode | Nilai `PUBLISH_MODE` | Deskripsi | Use Case |
|------|---------------------|-----------|----------|
| **Mock** | `mock` | Simulasi lokal, tidak hit API apapun. Simpan metadata JSON ke `mock_output/` | Development, CI/CD, testing logika pipeline |
| **Telegram Preview** | `telegram_preview` | Kirim gambar render + caption ke channel/chat Telegram (real API call) | QA visual nyata sebelum IG API disetujui |
| **Instagram** | `instagram` | Publish sungguhan via Instagram Graph API | Production (butuh approval IG App Review 2-4 minggu) |

### Cara Switch Mode

```bash
# Di file .env, ubah baris ini:
PUBLISH_MODE=mock           # Development (default)
PUBLISH_MODE=telegram_preview  # QA visual
PUBLISH_MODE=instagram      # Production (butuh IG_ACCESS_TOKEN + IG_BUSINESS_ACCOUNT_ID)
```

**Tidak ada file Python lain yang perlu diubah** — `pipeline.py` memanggil `get_publisher()` dari factory dan otomatis mendapat instance yang benar.

### Prasyarat per Mode

| Mode | Environment Variables Wajib |
|------|----------------------------|
| `mock` | Tidak ada (bisa jalan tanpa API key apapun) |
| `telegram_preview` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_PREVIEW_CHAT_ID` |
| `instagram` | `IG_ACCESS_TOKEN`, `IG_BUSINESS_ACCOUNT_ID`, `FB_APP_ID`, `FB_APP_SECRET` |

---

## 📁 Struktur Project Lengkap

```
ig-news-agent/
│
├── .env                     # Environment variables (jangan commit, copy dari .env.example)
├── .env.example             # Template environment variables
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── README.md                # Dokumentasi ini
├── docker-compose.yml       # Docker compose untuk PostgreSQL + services
├── scaffold-instructions.md # Instruksi scaffolding (reference)
│
├── config/
│   ├── settings.py          # Load env vars, class Settings (threshold, rate limit, dll)
│   ├── sources.yaml         # Daftar RSS feed & sumber berita whitelist (3-5 media Indonesia)
│   ├── logging.yaml         # Konfigurasi logging Python (format, level, file handler ke logs/)
│   ├── design.yaml          # Config desain template
│   ├── publishing.yaml      # Config publishing
│   ├── scheduler.yaml       # Config scheduler
│   └── scoring.yaml         # Config scoring thresholds
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/           # Modul pengambilan & filter berita
│   │   ├── __init__.py
│   │   ├── rss_fetcher.py       # Fetch entries dari RSS feed (feedparser)
│   │   ├── news_api_client.py   # Wrapper News API pihak ketiga (generic interface)
│   │   ├── deduplicator.py      # Fuzzy matching judul vs history DB (rapidfuzz)
│   │   └── freshness_filter.py  # Filter berita berdasarkan umur (timestamp)
│   │
│   ├── scoring/             # Modul scoring & validasi LLM
│   │   ├── __init__.py
│   │   ├── llm_client.py        # Wrapper NVIDIA Nemotron (OpenAI-compatible) + retry/rate limit
│   │   ├── news_scorer.py       # score_news() → ScoreResult (viral, credibility, sensitive, verified)
│   │   ├── sensitivity_guard.py # Cek kategori sensitif (SARA, kematian, bencana, politik belum inkrah)
│   │   └── cross_verification.py # Cek berita muncul di >1 sumber kredibel
│   │
│   ├── content_generation/  # Modul generate teks untuk infografis & caption
│   │   ├── __init__.py
│   │   ├── summarizer.py        # Parafrase berita jadi poin-poin ringkas (bukan copy-paste)
│   │   ├── caption_writer.py    # Generate caption IG + hashtag relevan
│   │   └── prompts/             # Template prompt LLM (file teks, bukan hardcoded)
│   │       ├── scoring_prompt.txt
│   │       ├── summarize_prompt.txt
│   │       └── caption_prompt.txt
│   │
│   ├── design/              # Modul rendering infografis
│   │   ├── __init__.py
│   │   ├── template_renderer.py # Render HTML+CSS → PNG/JPEG (Playwright)
│   │   ├── templates/
│   │   │   ├── base.html        # Template HTML dasar
│   │   │   ├── style.css        # Styling CSS
│   │   │   └── variants/        # Varian per kategori berita
│   │   │       ├── breaking_news.html
│   │   │   ├── entertainment.html
│   │   │   └── general.html
│   │   └── assets/
│   │       ├── fonts/           # Font custom
│   │       └── logo.png         # Logo brand
│   │
│   ├── storage/             # Modul cloud storage
│   │   ├── __init__.py
│   │   └── cloudinary_client.py # Upload ke Cloudinary, return public URL
│   │
│   ├── publishing/          # ⭐ PUBLISHER ABSTRACTION (FULLY IMPLEMENTED)
│   │   ├── __init__.py
│   │   ├── base_publisher.py        # Abstract class BasePublisher (interface publish)
│   │   ├── mock_publisher.py        # MockPublisher: simpan JSON ke mock_output/
│   │   ├── telegram_preview_publisher.py # Kirim ke Telegram (real API)
│   │   ├── ig_client.py             # InstagramPublisher (Graph API, NotImplementedError)
│   │   ├── publisher_factory.py     # get_publisher() — switch via PUBLISH_MODE
│   │   └── rate_limiter.py          # Sliding window 25 post/24 jam
│   │
│   ├── review/              # Modul human-in-the-loop review
│   │   ├── __init__.py
│   │   ├── telegram_bot.py        # Kirim preview + skor ke Telegram untuk approve/reject
│   │   └── review_queue.py        # Antrian berita menunggu approval manual
│   │
│   ├── database/            # Modul database (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── models.py              # NewsItem, Post, ScoreLog, ReviewLog
│   │   ├── db.py                  # Koneksi & session (PostgreSQL/Supabase)
│   │   └── migrations/            # Alembic migrations
│   │
│   ├── scheduler/           # Modul scheduling & orchestration
│   │   ├── __init__.py
│   │   ├── scheduler.py           # APScheduler job scheduling
│   │   └── pipeline.py            # Orchestrate: ingest → dedup → score → generate → render → upload → review → publish → log
│   │
│   └── utils/               # Utilitas umum
│       ├── __init__.py
│       ├── logger.py              # Setup logger terpusat
│       └── retry.py               # Decorator retry exponential backoff
│
├── scripts/                 # CLI entry points
│   ├── run_pipeline_once.py     # Jalankan 1 siklus pipeline manual (testing)
│   ├── backfill_history.py      # Import histori posting lama ke DB
│   └── test_ig_connection.py    # Test koneksi & auth Instagram Graph API
│
├── tests/                   # Unit tests (pytest)
│   ├── __init__.py
│   ├── test_deduplicator.py
│   ├── test_news_scorer.py
│   ├── test_template_renderer.py
│   └── fixtures/
│       └── sample_news.json
│
├── logs/                    # Log files (gitignore)
│   └── .gitkeep
│
└── mock_output/             # Mock publisher output (gitignore)
    └── .gitkeep
```

---

## ⚙️ Environment Variables Lengkap

Lihat `.env.example` untuk template. Berikut penjelasan tiap variable:

### LLM (NVIDIA Nemotron via build.nvidia.com)
```bash
NVIDIA_API_KEY=               # API key NVIDIA Nemotron (untuk scoring & content generation)
```

### Database (PostgreSQL/Supabase)
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/ig_news_agent
```

### Cloudinary (Image Hosting)
```bash
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Instagram Graph API (Production Only)
```bash
IG_ACCESS_TOKEN=                # Long-lived access token
IG_BUSINESS_ACCOUNT_ID=         # Instagram Business Account ID
FB_APP_ID=                      # Facebook App ID
FB_APP_SECRET=                  # Facebook App Secret
```

### Telegram (Review Bot + Preview Publisher)
```bash
TELEGRAM_BOT_TOKEN=             # Bot token dari @BotFather
TELEGRAM_CHAT_ID=               # Chat ID untuk review bot (approve/reject)
TELEGRAM_PREVIEW_CHAT_ID=       # Chat/channel ID untuk preview visual (mode telegram_preview)
```

### App Configuration
```bash
POST_SCORE_THRESHOLD_VIRAL=7    # Minimal viral potential score (1-10)
POST_SCORE_THRESHOLD_CREDIBILITY=6  # Minimal credibility score (1-10)
MAX_POSTS_PER_DAY=10            # Batas harian (selain rate limit IG 25/24h)
REVIEW_MODE=manual              # manual | auto (skip review jika auto)
```

### Publisher Mode (PENTING)
```bash
PUBLISH_MODE=mock               # mock | telegram_preview | instagram
```

### AI Image Generation
```bash
IMAGE_GEN_PROVIDER=cloudflare_workers   # mock | cloudflare_workers | stability
CF_WORKERS_AI_ENDPOINT=https://cf-image-gen.your-subdomain.workers.dev
STABILITY_API_KEY=                        # Untuk provider stability (production)
```

---

## 🧪 Testing & Development

### Smoke Test Mock Publisher

```bash
# Pastikan PUBLISH_MODE=mock di .env (default)
python -c "
from src.publishing.publisher_factory import get_publisher
publisher = get_publisher()
result = publisher.publish('dummy.jpg', 'Test caption dari scaffolding')
print('Result:', result)
"
```

**Expected Output:**
```json
{
  "status": "success",
  "post_id": "mock_abc12345",
  "mode": "mock",
  "error": null,
  "url": "file://.../mock_output/mock_abc12345.json"
}
```

File JSON akan muncul di `mock_output/` berisi metadata lengkap.

### Run Full Pipeline Test

```bash
# Test end-to-end pipeline (harus run as module)
python -m scripts.run_pipeline_once

# Output yang diharapkan:
# [1/8] Fetching RSS feeds...  Fetched 500+ raw items
# [2/8] Deduplicating...       500+ unique items
# [3/8] Filtering freshness... 200+ fresh items
# [4/8] Scoring news items...  Converted 200+ items to dicts for scoring
# ✓ 'Judul Berita' - viral:8 cred:9
```

### Run Unit Tests

```bash
# Semua test
pytest tests/

# Test spesifik dengan verbose
pytest tests/test_deduplicator.py -v
pytest tests/test_news_scorer.py -v
pytest tests/test_template_renderer.py -v
```

### Type Check (Compile All)

```bash
python -m compileall src/
# Harus tidak ada error
```

---

## 🐳 Docker (Optional)

```bash
# Start PostgreSQL + services
docker-compose up -d

# Lihat logs
docker-compose logs -f

# Stop
docker-compose down
```

`docker-compose.yml` menyediakan PostgreSQL database untuk development.

---

## 🔧 Development Workflow

### Menambah Fitur Baru (Contoh: Source Baru)

1. Tambah RSS feed ke `config/sources.yaml`
2. Implement logic di `src/ingestion/rss_fetcher.py` (sudah ada signature)
3. Tambah test di `tests/test_deduplicator.py`
4. Jalankan `python -m scripts.run_pipeline_once.py` untuk test end-to-end

### Debugging Pipeline

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG  # Linux/macOS
$env:LOG_LEVEL="DEBUG"  # Windows PowerShell

python -m scripts.run_pipeline_once
```

### Cek Rate Limit Status

```python
from src.publishing.rate_limiter import get_rate_limiter
limiter = get_rate_limiter()
print(f"Remaining posts: {limiter.get_remaining()}")
print(f"Reset time: {limiter.get_reset_time()}")
```

---

## 📝 Catatan Penting

### ⚠️ Instagram Graph API Approval
- **Approval butuh 2-4 minggu** dari Meta
- Selama menunggu, gunakan `PUBLISH_MODE=mock` atau `telegram_preview`
- Seluruh pipeline **bisa ditest end-to-end** tanpa akses IG API
- Cukup implement `InstagramPublisher` di `src/publishing/ig_client.py` nanti

### 🔐 Keamanan
- **JANGAN** commit file `.env` (sudah di `.gitignore`)
- **JANGAN** hardcode API key di kode
- Gunakan `.env.example` sebagai template untuk team

### 📦 Dependencies Utama
| Package | Fungsi |
|---------|--------|
| `feedparser` | Parse RSS feed |
| `rapidfuzz` | Fuzzy string matching (deduplikasi) |
| `openai` | OpenAI-compatible client (NVIDIA Nemotron) |
| `playwright` | Render HTML → PNG |
| `cloudinary` | Image upload & hosting |
| `python-telegram-bot` | Telegram bot API |
| `apscheduler` | Job scheduling |
| `sqlalchemy` + `psycopg2` | Database ORM |
| `tenacity` | Retry decorator |
| `pillow` | Image processing (mock image generation) |

---

## 🤖 AI Integration

### Fitur AI Baru
Update ini menambahkan 3 kemampuan AI inti ke pipeline:

| # | Fitur | Deskripsi | File Utama |
|---|-------|-----------|------------|
| 1 | **AI Summary Berita** | LLM (Nemotron) meringkas & memparafrase berita jadi 3-5 poin untuk infografis | `src/content_generation/summarizer.py` |
| 2 | **AI Caption Instagram** | LLM menulis caption + hashtag berdasarkan ringkasan berita | `src/content_generation/caption_writer.py` |
| 3 | **AI Desain Infografis** | AI image generation membuat background abstrak per kategori, teks di-overlay via HTML/CSS | `src/design/image_gen/`, `src/design/compositor.py` |

### Arsitektur Desain: Background AI + Teks HTML (Penting)
AI image generation (Stable Diffusion, DALL-E, Flux) **buruk rendering teks panjang/presisi** di gambar — hasilnya sering typo, huruf aneh, atau tidak terbaca. Solusi:

1. **AI image gen hanya bikin elemen visual**: background abstrak, ilustrasi simbolis, tekstur, gradient sesuai mood berita
   - Breaking news = merah/urgent
   - Hiburan = cerah/playful
   - Umum = biru-abu/netral
2. **Teks tetap di-render lewat HTML/CSS + Playwright** (seperti arsitektur sebelumnya) — supaya 100% terbaca & konsisten brand
3. **Guardrail wajib**: prompt image gen diarahkan ke ilustrasi abstrak/simbolis, **JANGAN** prompt yang menghasilkan wajah orang nyata/tokoh publik spesifik — menghindari risiko gambar menyesatkan (mirip deepfake) berbahaya untuk konten berita
4. **Watermark "Ilustrasi AI" wajib** di pojok infografis — transparansi bahwa background bukan foto asli kejadian

---

## ☁️ Cloudflare Workers AI Image Generation (Free Tier)

### Mengapa Cloudflare Workers AI?
- **Gratis**: 10.000 neurons/hari (~130 gambar flux-1-schnell)
- **Cepat**: Edge network global (~50ms latency di Asia)
- **Tidak perlu GPU**: Serverless, auto-scale
- **Integrasi native**: Python client via HTTP ke deployed worker

### Arsitektur

```
Python App                          Cloudflare Edge
┌─────────────────┐      HTTPS       ┌────────────────────────┐
│ compositor.py   │ ──────────────▶  │ Worker (cf-image-gen)  │
│ get_image_gen() │  POST /generate  │ env.AI.run(flux-schnell)│
└─────────────────┘ ◀──────────────  │ Return JPEG binary     │
       ▲                                 └────────────────────────┘
       │                                          │
       │                    10k neurons/day free  │
       └──────────────────────────────────────────┘
```

### 1. Deploy Worker (Satu Kali Saja)

```bash
cd src/workers/cf-image-gen
npm install
npx wrangler login          # Login via browser
npx wrangler deploy         # Deploy ke Cloudflare
# Output: https://cf-image-gen.<subdomain>.workers.dev
```

### 2. Konfigurasi Environment

```bash
# .env
IMAGE_GEN_PROVIDER=cloudflare_workers
CF_WORKERS_AI_ENDPOINT=https://cf-image-gen.your-subdomain.workers.dev
```

### 3. Test Endpoint

```bash
# Health check
curl https://cf-image-gen.your-subdomain.workers.dev/health
# {"status":"ok","model":"@cf/black-forest-labs/flux-1-schnell"}

# Generate image
curl -X POST https://cf-image-gen.your-subdomain.workers.dev/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"breaking news urgent red background"}' \
  --output test.jpg
# Returns valid JPEG (~400-500KB)
```

### 4. Model yang Digunakan

**Default**: `@cf/black-forest-labs/flux-1-schnell` (optimal free tier)

| Model | Neurons/gambar | Gambar/hari gratis | Keunggulan |
|-------|----------------|-------------------|------------|
| **flux-1-schnell** ⭐ | ~77 | **~130** | Cepat, kualitas bagus, balance |
| flux-2-klein-4b | ~500 | ~20 | Ultra-cepat |
| flux-2-dev | ~1.500+ | ~6 | Kualitas tinggi, mahal |

Ganti model di `src/workers/cf-image-gen/index.js` line 50:
```javascript
const response = await env.AI.run("@cf/black-forest-labs/flux-1-schnell", { ... });
```

### 5. Safety & Guardrails

Worker otomatis menambahkan safety suffix ke setiap prompt:
```
", abstract symbolic illustration, no realistic human faces, no specific real people, editorial illustration style, news infographic background"
```

Ini mencegah generate wajah orang nyata/tokoh publik — **wajib untuk konten berita**.

### 6. Quota Handling

Python client (`cloudflare_workers_gen.py`) cek quota otomatis:
- Call `/health` sebelum generate
- Cek header `x-ratelimit-remaining` dari response
- Raise `RuntimeError` kalau quota habis → pipeline bisa fallback ke `mock` atau stop graceful

### 7. Monitoring

```bash
# Real-time logs
npx wrangler tail

# Dashboard
https://dash.cloudflare.com/?to=/:account/ai/workers-ai
# Lihat: Neurons used, Requests, Errors, Latency
```

### 8. Fallback ke Mock (Development Offline)

```bash
# .env
IMAGE_GEN_PROVIDER=mock
```
Menghasilkan gradient solid per kategori — **gratis, offline, instant**.

---

## 🔧 Troubleshooting

### RSS Feed Error / 0 Items Fetched

Jika `Fetched 0 raw items` atau RSS gagal:

1. Cek `config/sources.yaml` - pastikan URL RSS masih aktif
2. Test manual:
```bash
python -c "
import feedparser
fp = feedparser.parse('https://www.cnnindonesia.com/rss')
print(f'Entries: {len(fp.entries)}, Status: {fp.status if hasattr(fp, \"status\") else \"N/A\"}, Bozo: {fp.bozo}')
"
```

**Working feeds (per Juli 2026)**:
- CNN Indonesia: `https://www.cnnindonesia.com/rss` (100 entries)
- CNN Nasional: `https://www.cnnindonesia.com/nasional/rss`
- Antara News: `https://www.antaranews.com/rss/terkini.xml`
- Tempo Bisnis: `https://rss.tempo.co/bisnis`
- Tempo Tekno: `https://rss.tempo.co/tekno`

**Broken feeds (per Juli 2026)**:
- Kompas: 404
- Detik: Connection reset
- Tempo Tekno/English: Cloudflare 522/blocked

### LLM Scoring Fails / JSON Parse Error

Jika LLM scoring gagal:
1. Pastikan `NVIDIA_API_KEY` valid di `.env`
2. LLM kadang return malformed JSON — sudah ditangani dengan regex fallback di `_llm_score()`
3. Jika persistent, check NVIDIA API status

### Import Error: No module named 'src'

Jalankan **selalu sebagai module**:
```bash
# ✅ Benar
python -m scripts.run_pipeline_once

# ❌ Salah
python scripts/run_pipeline_once.py
```

### Pipeline Stuck at Scoring

Jika pipeline macet di scoring lama:
1. NVIDIA API mungkin rate limit (503 Service Unavailable)
4. LLM kadang timeout — retry otomatis via `tenacity`
5. Gunakan `IMAGE_GEN_PROVIDER=mock` untuk testing cepat tanpa LLM

---

## 📄 License

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

## 🤝 Kontribusi

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -am 'Tambah fitur X'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

---

## 📞 Support & Pertanyaan

Untuk pertanyaan teknis atau issue, buka GitHub Issues atau hubungi maintainer.

**Happy coding! 🚀**
Kalau nanti mau pindah dari Stability AI ke provider lain (Replicate/Flux, DALL-E):
1. Buat class baru extend `BaseImageGen`
2. Daftarkan di `image_gen_factory.py`
3. **Tidak perlu ubah `compositor.py`** — pola factory sama seperti publisher

---

## ☁️ Cloudflare Workers AI Image Generation (Free Tier)

### Mengapa Cloudflare Workers AI?
- **Gratis**: 10.000 neurons/hari (~130 gambar flux-1-schnell)
- **Cepat**: Edge network global (~50ms latency di Asia)
- **Tidak perlu GPU**: Serverless, auto-scale
- **Integrasi native**: Python client via HTTP ke deployed worker

### Arsitektur

```
Python App                          Cloudflare Edge
┌─────────────────┐      HTTPS       ┌────────────────────────┐
│ compositor.py   │ ──────────────▶  │ Worker (cf-image-gen)  │
│ get_image_gen() │  POST /generate  │ env.AI.run(flux-schnell)│
└─────────────────┘ ◀──────────────  │ Return JPEG binary     │
       ▲                                 └────────────────────────┘
       │                                          │
       │                    10k neurons/day free  │
       └──────────────────────────────────────────┘
```

### 1. Deploy Worker (Satu Kali Saja)

```bash
cd src/workers/cf-image-gen
npm install
npx wrangler login          # Login via browser
npx wrangler deploy         # Deploy ke Cloudflare
# Output: https://cf-image-gen.<subdomain>.workers.dev
```

### 2. Konfigurasi Environment

```bash
# .env
IMAGE_GEN_PROVIDER=cloudflare_workers
CF_WORKERS_AI_ENDPOINT=https://cf-image-gen.your-subdomain.workers.dev
```

### 3. Test Endpoint

```bash
# Health check
curl https://cf-image-gen.your-subdomain.workers.dev/health
# {"status":"ok","model":"@cf/black-forest-labs/flux-1-schnell"}

# Generate image
curl -X POST https://cf-image-gen.your-subdomain.workers.dev/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"breaking news urgent red background"}' \
  --output test.jpg
# Returns valid JPEG (~400-500KB)
```

### 4. Model yang Digunakan

**Default**: `@cf/black-forest-labs/flux-1-schnell` (optimal free tier)

| Model | Neurons/gambar | Gambar/hari gratis | Keunggulan |
|-------|----------------|-------------------|------------|
| **flux-1-schnell** ⭐ | ~77 | **~130** | Cepat, kualitas bagus, balance |
| flux-2-klein-4b | ~500 | ~20 | Ultra-cepat |
| flux-2-dev | ~1.500+ | ~6 | Kualitas tinggi, mahal |

Ganti model di `src/workers/cf-image-gen/index.js` line 50:
```javascript
const response = await env.AI.run("@cf/black-forest-labs/flux-1-schnell", { ... });
```

### 5. Safety & Guardrails

Worker otomatis menambahkan safety suffix ke setiap prompt:
```
", abstract symbolic illustration, no realistic human faces, no specific real people, editorial illustration style, news infographic background"
```

Ini mencegah generate wajah orang nyata/tokoh publik — **wajib untuk konten berita**.

### 6. Quota Handling

Python client (`cloudflare_workers_gen.py`) cek quota otomatis:
- Call `/health` sebelum generate
- Cek header `x-ratelimit-remaining` dari response
- Raise `RuntimeError` kalau quota habis → pipeline bisa fallback ke `mock` atau stop graceful

### 7. Monitoring

```bash
# Real-time logs
npx wrangler tail

# Dashboard
https://dash.cloudflare.com/?to=/:account/ai/workers-ai
# Lihat: Neurons used, Requests, Errors, Latency
```

### 8. Fallback ke Mock (Development Offline)

```bash
# .env
IMAGE_GEN_PROVIDER=mock
```
Menghasilkan gradient solid per kategori — **gratis, offline, instant**.

---

### Ganti Provider Image Generation

## 📄 License

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

## 🤝 Kontribusi

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -am 'Tambah fitur X'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

---

## 📞 Support & Pertanyaan

Untuk pertanyaan teknis atau issue, buka GitHub Issues atau hubungi maintainer.

**Happy coding! 🚀**