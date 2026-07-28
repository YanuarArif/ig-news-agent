import os
os.environ['IMAGE_GEN_PROVIDER'] = 'mock'
os.environ['PUBLISH_MODE'] = 'mock'

import sys
sys.path.insert(0, 'src')

from src.ingestion.rss_fetcher import fetch_rss_feeds
from src.ingestion.deduplicator import get_deduplicator
from src.ingestion.freshness_filter import get_freshness_filter

raw = fetch_rss_feeds([
    {'url': 'https://www.cnnindonesia.com/rss', 'name': 'CNN Indonesia', 'category': 'general'},
    {'url': 'https://www.antaranews.com/rss/terkini.xml', 'name': 'Antara News', 'category': 'general'},
    {'url': 'https://rss.tempo.co/bisnis', 'name': 'Tempo Bisnis', 'category': 'business'},
])
print('Raw:', len(raw), 'items')

dedup = get_deduplicator()
unique = dedup.filter_batch(raw, [])
print('After dedup:', len(unique), 'items')

fresh = get_freshness_filter().filter_batch(unique)
print('After fresh:', len(fresh), 'items')

for i, item in enumerate(fresh[:2]):
    title = item.get('title', '')
    source = item.get('source_name', '')
    print('  {}. {}... ({})'.format(i+1, title[:60], source))