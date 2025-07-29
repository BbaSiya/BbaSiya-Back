# -*- coding: utf-8 -*-

import http.client
import json
import numpy as np
import os
import time
from dotenv import load_dotenv

load_dotenv()


class ClovaEmbeddingExecutor:
    def __init__(self):
        self._host = 'clovastudio.stream.ntruss.com'
        self._api_key = f"Bearer {os.getenv('CLOVA_API_KEY')}"
        self._request_id = os.getenv('CLOVA_REQUEST_ID', '9b0b3add3679499c812501b3a7156785')
        self._cache = {}  # 임베딩 캐시
        self._last_request_time = 0
        self._min_interval = 0.1 

    def _send_request(self, text):
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_interval:
            time.sleep(self._min_interval - time_since_last)
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': self._api_key,
        }

        request_data = {
            "text": text
        }

        try:
            conn = http.client.HTTPSConnection(self._host)
            conn.request('POST', '/v1/api-tools/embedding/v2', json.dumps(request_data), headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode(encoding='utf-8'))
            conn.close()
            
            self._last_request_time = time.time()
            
            if result['status']['code'] == '20000':
                return result['result']['embedding']
            else:
                print(f"API Error: {result['status']['code']} - {result['status']['message']}")
                return None
                
        except Exception as e:
            print(f"Request Error: {str(e)}")
            return None

    def get_embedding(self, text):
        if not text:
            return None
        
        # 캐시에서 먼저 확인
        if text in self._cache:
            return self._cache[text]
            
        embedding = self._send_request(text)
        if embedding:
            self._cache[text] = np.array(embedding)  # 캐시에 저장
            return self._cache[text]
        return None

    def cosine_similarity(self, vec1, vec2):
        #print("vec1, vec2", vec1, vec2)
        if vec1 is None or vec2 is None:
            return 0.0

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)

        #print("norm_vec1, norm_vec2", norm_vec1, norm_vec2)
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        cosine_sim = dot_product / (norm_vec1 * norm_vec2)

        #print("cosine_sim2", (cosine_sim + 1) / 2)
        
        return (cosine_sim + 1) / 2

    def calculate_industry_similarity(self, industry1, industry2):
        if industry1 == industry2:
            return 1.0  # 동일 업종
            
        try:
            embedding1 = self.get_embedding(industry1)
            embedding2 = self.get_embedding(industry2)
            
            if embedding1 is not None and embedding2 is not None:
                similarity = self.cosine_similarity(embedding1, embedding2)
                return round(similarity, 3)  
            else:
                return 0.5
                
        except Exception as e:
            print(f"Industry similarity calculation error: {str(e)}")
            return 0.5  # 에러 시 기본값

    def clear_cache(self):
        self._cache.clear()


clova_executor = ClovaEmbeddingExecutor()


def get_industry_similarity_clova(industry1, industry2):
    return clova_executor.calculate_industry_similarity(industry1, industry2)
