from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from similarity.utils import *
from news.utils import *
# Create your views here.

class StockSimilarityView(View):
    def get(self, request, stock_id, user_id):
        pattern_scores, bs_scores = vectorized_weighted_similarity(
            target_stockid=stock_id, 
            user_id=user_id, 
            category_stockids=[stock_id], 
            days=30
        )
        
        bs = bs_scores[0] if len(bs_scores) > 0 else 0.0
        
        # 내가할게 -bbh
        try:
            news = news_summary(stock_id)
        except Exception as e:
            news = None
            return JsonResponse({'error': str(e)}, status=500)

        eq = get_sentiment_score(news)
        
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
        
        # 상위 5개 보유 종목 (비교종목) - batch_get_user_stock_info 사용
        top5_stocks = batch_get_user_stock_info(user_id)
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
        
        # 내가할게 -bbh
        news = news_summary(most_similar_stock['stockid'])
        eq = get_sentiment_score(news)
        
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