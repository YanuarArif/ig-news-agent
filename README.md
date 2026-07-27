# IG News Automation Agent

Automasi end-to-end untuk mengambil berita viral, scoring dengan LLM, generate konten infografis, dan publish ke Instagram (dengan mode testing mock/telegram_preview).

## Fitur Utama
1. **Ingestion**: Fetch berita dari RSS feeds & News API
2. **Deduplication & Freshness**: Fuzzy matching + filter umur berita
3. **Scoring LLM**: Viral potential, credibility, sensitivity check, cross-verification
4. **Content Generation**: Summarizer + Caption writer dengan prompt template
5. **Design Rendering**: HTML/CSS template → PNG via Playwright
6. **Storage**: Upload gambar ke Cloudinary
7. **Publishing**: Switchable publisher (mock | telegram_preview | instagram)
8. **Review**: Human-in-the-loop via Telegram bot
9. **Scheduling**: APScheduler untuk pipeline otomatis

## Quick Start

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Configure environment
cp .env.example .env
# Edit .env dengan credentials Anda

# 4. Run pipeline once (testing mode mock)
python scripts/run_pipeline_once.py

# 5. Check mock output
ls mock_output/
```

## Publisher Modes

| Mode | Deskripsi | Use Case |
|------|-----------|----------|
| `mock` | Simulasi lokal, simpan JSON ke `mock_output/` | Development & CI |
| `telegram_preview` | Kirim ke Telegram channel untuk QA visual | Pre-production QA |
| `instagram` | Publish sungguhan via Instagram Graph API | Production (butuh approval IG API) |

Ubah mode via `.env`: `PUBLISH_MODE=mock|telegram_preview|instagram`

## Project Structure

```
ig-news-agent/
├── config/           # Config files (settings, sources, logging)
├── src/
│   ├── ingestion/    # RSS fetch, News API, dedup, freshness
│   ├── scoring/      # LLM scoring, sensitivity, verification
│   ├── content_generation/  # Summarizer, caption writer, prompts
│   ├── design/       # Template renderer, HTML/CSS templates
│   ├── storage/      # Cloudinary client
│   ├── publishing/   # Publisher abstraction (mock/telegram/IG)
│   ├── review/       # Telegram review bot & queue
│   ├── database/     # SQLAlchemy models & migrations
│   ├── scheduler/    # APScheduler & pipeline orchestrator
│   └── utils/        # Logger, retry decorator
├── scripts/          # CLI entry points
├── tests/            # Unit tests
├── logs/             # Log files
└── mock_output/      # Mock publisher output
```

## Environment Variables

Lihat `.env.example` untuk daftar lengkap.

## Testing

```bash
# Run unit tests
pytest tests/

# Smoke test mock publisher
python -c "
from src.publishing.publisher_factory import get_publisher
publisher = get_publisher()
result = publisher.publish('dummy.jpg', 'Test caption')
print(result)
"
```

## License

MIT