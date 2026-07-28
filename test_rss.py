import feedparser

feeds = [
    'https://www.kompas.com/rss',
    'https://rss.detik.com/index.php/detikcom',
    'https://www.cnnindonesia.com/rss',
    'https://rss.tempo.co/nasional',
    'https://kumparan.com/rss',
    'https://rss.liputan6.com/rss',
]

for f in feeds:
    fp = feedparser.parse(f)
    status = fp.status if hasattr(fp, 'status') else 'N/A'
    print(f'{f}: {len(fp.entries)} entries, bozo={fp.bozo}, status={status}')
    if fp.bozo and fp.entries:
        title = fp.entries[0].get('title', 'N/A')
        print(f'  First entry: {title[:80]}')