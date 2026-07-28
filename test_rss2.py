import feedparser

feeds = [
    ('CNN Indonesia', 'https://www.cnnindonesia.com/rss'),
    ('CNN Indonesia Nasional', 'https://www.cnnindonesia.com/nasional/rss'),
    ('Tempo.co', 'https://rss.tempo.co/nasional'),
    ('Antara News', 'https://www.antaranews.com/rss/terkini.xml'),
    ('Tempo English', 'https://rss.tempo.co/english'),
    ('Tempo Bisnis', 'https://rss.tempo.co/bisnis'),
    ('Tempo Tekno', 'https://rss.tempo.co/tekno'),
    ('Tempo Bola', 'https://rss.tempo.co/bola'),
]

for name, url in feeds:
    fp = feedparser.parse(url)
    status = fp.status if hasattr(fp, 'status') else 'N/A'
    print(f'{name}: {len(fp.entries)} entries, status={status}, bozo={fp.bozo}')
    if fp.entries:
        print(f'  First: {fp.entries[0].get("title", "N/A")[:70]}')