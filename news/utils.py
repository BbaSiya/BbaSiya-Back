import re
import pandas as pd
from datetime import datetime, timedelta
import os
import http.client
import json
from dotenv import load_dotenv

from stock.models import Stock
from .clova_sentiment import get_sentiment_score as _get_sentiment_score

load_dotenv()


def get_recent_news_by_stock_id(stock_id, days=3):
  
    mapping_path = os.path.join(os.path.dirname(__file__), 'csv', 'mapping.csv')
    news_path = os.path.join(os.path.dirname(__file__), 'csv', 'news.csv')

    mapping_df = pd.read_csv(mapping_path, dtype={'stock_id': str, 'news_id': str})
    news_df = pd.read_csv(news_path, dtype={'news_id': str})

    print(mapping_df, 'mapping_df',news_df, 'news_df' )

    today = datetime.now().date()
    three_days_ago = today - timedelta(days=3)

    mapping_df['date'] = pd.to_datetime(mapping_df['date']).dt.date
    filtered = mapping_df[(mapping_df['stock_id'] == str(stock_id)) & (mapping_df['date'] >= three_days_ago)]
    filtered = filtered.sort_values('date', ascending=False).head(10)

    news_list = []
    for news_id in filtered['news_id']:
        news_row = news_df[news_df['news_id'] == news_id]
        if not news_row.empty:
                news_list.append(news_row.iloc[0].to_dict())
        print(f"[DEBUG] 반환 뉴스 개수: {len(news_list)}")
        return news_list



def news_list_to_text(news_list, text_key='text'):
    texts = [news[text_key] for news in news_list if text_key in news and isinstance(news[text_key], str)]
    return '\n'.join(texts)


def summarize_text_with_clova(text):
    if not text or not text.strip():
        return "최근 뉴스소식이 없어요"
    CLOVA_API_KEY = os.getenv('CLOVA_API_KEY')
    host = 'clovastudio.stream.ntruss.com'
    url = '/testapp/v1/api-tools/summarization/v2'
    headers = {
        'Authorization': f'Bearer {CLOVA_API_KEY}',
        'Content-Type': 'application/json',
    }
    body = {
        "texts": [text],
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000,
        "segMinSize": 300,
        "includeAiFilters": False
    }
    try:
        conn = http.client.HTTPSConnection(host)
        conn.request('POST', url, json.dumps(body), headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode('utf-8'))
        conn.close()
        if result['status']['code'] == '20000':
            summary = result['result']['text']
            if '\n' in summary:
                first_sentence = summary.split('\n')[0].strip()
                return first_sentence
            return summary.strip()
        else:
            print(f"Clova 요약 API Error: {result['status']['code']} - {result['status']['message']}")
            return None
    except Exception as e:
        print(f"Clova 요약 API Request Error: {str(e)}")
        return None


def get_sentiment_score(sentence):
    if not sentence or not sentence.strip():
        return 50
    return _get_sentiment_score(sentence)


def news_summary(stock_id):
    news_list = get_recent_news_by_stock_id(stock_id)
    text =  news_list_to_text(news_list)
    print(text, 'text')
    return summarize_text_with_clova(text)