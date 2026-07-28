import os
os.environ['IMAGE_GEN_PROVIDER'] = 'mock'
os.environ['PUBLISH_MODE'] = 'mock'

import sys
sys.path.insert(0, 'src')

from datetime import datetime, timezone, timedelta

# Test with fresh dates
from src.scoring.news_scorer import score_news

# Fresh items with recent dates
raw = [
    {
        'title': 'Kemenkes Siapkan Robot Bedah AI, Dokter Tetap Jadi Pengambil Keputusan',
        'body': 'Kementerian Kesehatan menyiapkan robot bedah bertenaga AI untuk membantu dokter dalam operasi kompleks. Robot ini dirancang untuk presisi tinggi tapi dokter tetap pengambil keputusan akhir.',
        'source_name': 'CNN Indonesia',
        'source_url': 'https://www.cnnindonesia.com/teknologi/2024/07/28/robot-bedah-ai',
        'published_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        'category': 'technology'
    },
    {
        'title': 'Hasil Washington Open: Janice Lolos 16 Besar Usai Menangi Laga Pertama',
        'body': 'Atlet tenis Indonesia Janice Tjen berhasil lolos ke babak 16 besar Washington Open setelah mengalahkan lawan dari Belgia dengan skor 6-3 6-4.',
        'source_name': 'CNN Indonesia',
        'source_url': 'https://www.cnnindonesia.com/olahraga/2024/07/28/washington-open-janice',
        'published_at': (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        'category': 'sports'
    },
]

print('Testing scoring with fresh items...')
for item in raw:
    try:
        score = score_news(item)
        print(f"Score: viral={score.viral_potential}, cred={score.credibility_score}, sens={score.is_sensitive}")
    except Exception as e:
        print(f'Error: {e}')