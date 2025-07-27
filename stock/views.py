from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from similarity.utils import calculate_weighted_similarity

# Create your views here.

class StockSimilarityView(View):
    def get(self, request, stock_id, user_id):
        bs = calculate_weighted_similarity(stock_id, user_id)
        # 임시 데이터 세현오빠 수정 부탁해!!
        news = "삼성전자 실적 개선 예상, 반도체 시장 회복세"
        eq = 75  
        
        result = {
            'bs': bs,
            'news': news,
            'eq': eq
        }
        
        return JsonResponse(result, safe=False)
