from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from similarity.utils import *
# Create your views here.

class StockSimilarityView(View):
    def get(self, request, stock_id, user_id):
        bs = calculate_weighted_similarity(stock_id, user_id)['bs']
        # 임시 데이터 세현오빠 수정 부탁해!!
        news = "삼성전자 실적 개선 예상, 반도체 시장 회복세"
        eq = 75  
        
        result = {
            'bs': bs,
            'news': news,
            'eq': eq
        }
        
        return JsonResponse(result, safe=False)

class UserCategoryRecommendationView(View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        category_id = request.GET.get('category_id')
        
        # 가장 유사한 종목 
        most_similar_stock = get_most_similar_stock_by_category(category_id, user_id)
        
        if not most_similar_stock:
            return JsonResponse({'error': '해당 카테고리에서 유사한 종목을 찾을 수 없습니다.'}, status=404)
        
        # 같은 type, industry 개수 계산
        similarity_counts = count_similar_stocks_by_user(user_id, most_similar_stock['stockid'])
        
        # 상위 5개 보유 종목 (비교종목)
        top5_stocks = get_top5_stocks_by_value(user_id)
        comparison_stocks = []
        for stockid, name, value, cnt, current_price in top5_stocks:
            comparison_stocks.append({
                'stock_id': stockid,
                'stock_name': name
            })
        

        chart_data = []
        

        most_similar_history = get_stock_price_history(most_similar_stock['stockid'])
        chart_data.append(most_similar_history)
        

        for stockid, name, value, cnt, current_price in top5_stocks:
            stock_history = get_stock_price_history(stockid)
            chart_data.append(stock_history)
        
        # 임시 데이터 !! 세현오빠 수정 부탁해!!
        news = "시장 전망 긍정적, 투자자 관심 증가"
        eq = 78  
        
        # bs 지수
        pattern_similarity = most_similar_stock['pattern_similarity']
        
        result = {
            'stock_id': most_similar_stock['stockid'],
            'stock_name': most_similar_stock['name'],
            'eq': eq,
            'news': news,
            'bs': most_similar_stock['similarity_score'],
            'stock_type': most_similar_stock['type'],
            'same_type_cnt': similarity_counts['same_type_count'],
            'stock_industry': most_similar_stock['industry_name'],
            'same_industry_cnt': similarity_counts['same_industry_count'],
            'pattern_similarity': pattern_similarity,
            'stocks': comparison_stocks,
            'chartData': chart_data
        }
        
        return JsonResponse(result, safe=False)
