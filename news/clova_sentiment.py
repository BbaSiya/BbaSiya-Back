# -*- coding: utf-8 -*-

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        }

        with requests.post(self._host + '/v3/chat-completions/HCX-005',
                           headers=headers, json=completion_request, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    print(line.decode("utf-8"))


def get_sentiment_score(sentence):
    host = 'https://clovastudio.stream.ntruss.com'
    api_key = os.getenv('CLOVA_API_KEY')
    request_id = os.getenv('CLOVA_REQUEST_ID', 'test-request-id')
    executor = CompletionExecutor(host, f'Bearer {api_key}', request_id)

    system_prompt = """- 이것은 문장 감정 분석기 입니다.\n- 긍정지수만 알려주고 부연 설명은 하지 마세요.\n- 문장에 대한 긍정 지수를 0부터 100까지로 나타내주세요 \n\n문장: 기분 진짜 좋다\n감정: 긍정\n###\n문장: 아오 진짜 짜증나게 하네\n감정: 부정\n###\n문장: 이걸로 보내드릴게요\n감정: 중립\n###"""
    user_prompt = f"문장: {sentence}"

    request_data = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt}
                ]
            }
        ],
        "topP": 0.6,
        "topK": 0,
        "maxTokens": 256,
        "temperature": 0.1,
        "repetitionPenalty": 1.1,
        "stop": ["###"],
        "seed": 0,
        "includeAiFilters": True
    }

    # 응답 파싱 및 긍정지수 추출
    result_text = ""
    with requests.post(host + '/v3/chat-completions/HCX-005',
                      headers={
                          'Authorization': f'Bearer {api_key}',
                          'X-NCP-CLOVASTUDIO-REQUEST-ID': request_id,
                          'Content-Type': 'application/json; charset=utf-8',
                          'Accept': 'text/event-stream'
                      },
                      json=request_data, stream=True) as r:
        for line in r.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                print(decoded)
                try:
                    import re
                    numbers = re.findall(r'\d+', decoded)
                    if numbers:
                        return int(numbers[0])
                except Exception:
                    continue
    return None
