import sys
sys.path.insert(0, 'src')

from src.scoring.news_scorer import score_news

items = [
    {
        'title': 'Nvidia Buat Aliansi Keamanan Agen AI Usai OpenAI Serang Hugging Face',
        'body': 'Nvidia mengumumkan aliansi keamanan agen AI bersama perusahaan teknologi terkemuka setelah insiden OpenAI menyerang Hugging Face. Aliansi ini bertujuan untuk meningkatkan keamanan ekosistem AI.',
        'source_name': 'CNN Indonesia',
        'category': 'technology'
    },
    {
        'title': 'Awas, Salah Masukkan PIN di HP Samsung Bisa Kena Reset Paksa',
        'body': 'Pengguna Samsung diperingatkan untuk hati-hati memasukkan PIN. Kesalahan input berulang dapat memicu factory reset otomatis yang menghapus semua data.',
        'source_name': 'CNN Indonesia',
        'category': 'technology'
    },
    {
        'title': 'Indosat Bakal Kaji Putusan MK Soal Kuota Internet Rollover',
        'body': 'Indosat Ooredoo Hutchison akan mengevaluasi putusan Mahkamah Konstitusi terkait kuota internet rollover. Keputusan ini diharapkan menguntungkan pengguna.',
        'source_name': 'CNN Indonesia',
        'category': 'technology'
    }
]

from src.scoring.news_scorer import score_news

for item in items:
    try:
        score = score_news(item)
        print('Title: ' + item['title'][:60] + '...')
        print('  viral={}, cred={}, sens={}, overall={}'.format(score.viral_potential, score.credibility_score, score.is_sensitive, score.overall_score))
        print('  passes: ' + str(score.passes_threshold()))
    except Exception as e:
        print('Error: ' + str(e))