import sys
sys.path.insert(0, 'src')

from src.ingestion.rss_fetcher import fetch_rss_feeds

raw = fetch_rss_feeds([
    {'url': 'https://www.cnnindonesia.com/teknologi/rss', 'name': 'CNN Teknologi', 'category': 'technology'},
])
print('Total items:', len(raw))
for item in raw[:5]:
    title = item.get('title', '')
    cat = item.get('category')
    print('  ' + title[:80] + ' | cat: ' + str(cat))