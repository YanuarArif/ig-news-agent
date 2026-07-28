import sys
sys.path.insert(0, 'src')

import os
from dotenv import load_dotenv
load_dotenv()

from src.ingestion.rss_fetcher import fetch_rss_feeds
from src.ingestion.deduplicator import get_deduplicator
from src.ingestion.freshness_filter import get_freshness_filter
from src.scoring.news_scorer import score_news
from src.content_generation.summarizer import NewsSummarizer
from src.content_generation.caption_writer import CaptionWriter
from src.design.compositor import build_infographic
from src.publishing.publisher_factory import get_publisher

# Fetch only tech feeds
raw = fetch_rss_feeds([
    {'url': 'https://www.cnnindonesia.com/teknologi/rss', 'name': 'CNN Teknologi', 'category': 'technology'},
])
print('Raw:', len(raw), 'items')

dedup = get_deduplicator()
unique = dedup.filter_batch(raw, [])
print('After dedup:', len(unique), 'items')

fresh = get_freshness_filter().filter_batch(unique)
print('After fresh:', len(fresh), 'items')

# Score and process
for item in fresh[:10]:
    try:
        score = score_news(item)
        if hasattr(score, 'to_dict'):
            score_dict = score.to_dict()
        else:
            score_dict = score
        item['score'] = score_dict
        print('Item: ' + item['title'][:50] + '...')
        print('  viral=' + str(score_dict.get('viral_potential')) + ' cred=' + str(score_dict.get('credibility_score')) + ' sens=' + str(score_dict.get('is_sensitive')))
        if score_dict.get('viral_potential', 0) >= 7 and score_dict.get('credibility_score', 0) >= 6:
            print('  PASSES THRESHOLD!')
            summarizer = NewsSummarizer()
            caption_writer = CaptionWriter()
            summary = summarizer.summarize(item['title'], item['summary'], item['source_name'], item['category'], item['score'].get('viral_potential', 5), item['score'].get('credibility_score', 5))
            caption_data = caption_writer.write_caption(summary, item['source_name'], item['score'].get('viral_potential', 5), item['score'].get('credibility_score', 5))
            image_path = build_infographic(summary, caption_data['source_attribution'])
            print('  Image: ' + image_path)
            publisher = get_publisher()
            result = publisher.publish(image_path, caption_data['full_text'])
            print('  Published: ' + str(result))
    except Exception as e:
        print('Error: ' + str(e))