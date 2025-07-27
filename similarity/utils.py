from similarity.models import MyStock
from stock.models import ClosingPriceLog, Stock, Industry
from category.utils import get_stockids_by_category
import numpy as np


def get_stock_trend_with_dates(stockid, days=30):

    qs = ClosingPriceLog.objects.filter(stockid=stockid).order_by('-date')[:days]
    qs = list(qs)[::-1]  
    closing_prices = [row.closing_price for row in qs]
    updown_rates = [row.updown_rate for row in qs]
    dates = [row.date.date() for row in qs]  
    return closing_prices, updown_rates, dates

def zscore_normalize(vec):
    arr = np.array(vec)
    return (arr - arr.mean()) / (arr.std() + 1e-8)

def dtw_distance(a, b):
    n, m = len(a), len(b)
    dtw = np.full((n+1, m+1), np.inf)
    dtw[0, 0] = 0
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(a[i-1] - b[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
    return dtw[n, m]


def similarity_dtw_price(stockid1, stockid2, days=30):
    prices1, _, dates1 = get_stock_trend_with_dates(stockid1, days)
    prices2, _, dates2 = get_stock_trend_with_dates(stockid2, days)

    common_dates = set(dates1) & set(dates2)
    common_prices1 = []
    common_prices2 = []
    
    for date in sorted(common_dates):
        if date in dates1 and date in dates2:
            idx1 = dates1.index(date)
            idx2 = dates2.index(date)
            common_prices1.append(prices1[idx1])
            common_prices2.append(prices2[idx2])
    
    price1_norm = zscore_normalize(common_prices1)
    price2_norm = zscore_normalize(common_prices2)
    price_dist = dtw_distance(price1_norm, price2_norm)
    price_sim = 1 / (1 + price_dist)
    
    #print(f"{stockid1} vs {stockid2} - DTW 거리: {price_dist}, 유사도: {price_sim}")
    
    return price_sim


def get_top5_stocks_by_value(userid):
    mystocks = MyStock.objects.filter(userid=userid)
    result = []
    for ms in mystocks:
        try:
            stock = Stock.objects.get(id=ms.stockid)
            if ms.cnt is not None and stock.current_price is not None:
                value = ms.cnt * stock.current_price
                result.append((ms.stockid, stock.name, value, ms.cnt, stock.current_price))
        except Stock.DoesNotExist:
            continue
    result.sort(key=lambda x: x[2], reverse=True) 
    return result[:5] #상위 5개 

def get_industry_name_by_stockid(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        industry = Industry.objects.get(industry_code=stock.industry_code)
        return industry.industry_name
    except (Stock.DoesNotExist, Industry.DoesNotExist):
        return None

def get_type_by_stockid(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        return stock.type
    except Stock.DoesNotExist:
        return None

# Clova Studio API 
def get_industry_similarity(name1, name2):
    if name1 is None or name2 is None:
        return 0.3  
    if name1 == name2:
        return 1.0
    return 0.5  # 임시값

# type 유사도 매트릭스
TYPE_SIM_MATRIX = {
    '성장주': {'성장주': 1.0, '가치주': 0.4, '배당주': 0.2},
    '가치주': {'성장주': 0.4, '가치주': 1.0, '배당주': 0.5},
    '배당주': {'성장주': 0.2, '가치주': 0.5, '배당주': 1.0},
}

def get_type_similarity(stockid1, stockid2):
    type1 = get_type_by_stockid(stockid1)
    type2 = get_type_by_stockid(stockid2)
    if not type1 or not type2:
        return 0.3  
    return TYPE_SIM_MATRIX.get(type1, {}).get(type2, 0.3)

def calculate_weighted_similarity(target_stockid, user_id, days=30):
 
    # 상위 5개 보유 종목
    top5 = get_top5_stocks_by_value(user_id)
    total_value = sum([x[2] for x in top5])
    weighted_price_sim = 0.0
    weighted_industry_sim = 0.0
    weighted_type_sim = 0.0
    target_industry = get_industry_name_by_stockid(target_stockid)
    
    #print(f"target_stockid={target_stockid}, user_id={user_id}")
    #print(f"top5 count={len(top5)}, total_value={total_value}")
    
    for stockid, name, value, cnt, current_price in top5:
        weight = value / total_value if total_value > 0 else 0
        # 패턴
        price_sim = similarity_dtw_price(target_stockid, stockid, days)
        # 업종 유사도
        industry_name = get_industry_name_by_stockid(stockid)
        industry_sim = get_industry_similarity(target_industry, industry_name)
        # type 유사도
        type_sim = get_type_similarity(target_stockid, stockid)
        
        #print(f"stockid={stockid}, weight={weight}, price_sim={price_sim}")
        
        weighted_price_sim += price_sim * weight
        weighted_industry_sim += industry_sim * weight
        weighted_type_sim += type_sim * weight
    
    
    # 종합 유사도 (가격, 업종, 타입 유사도의 평균)
    total_weighted_similarity = (weighted_price_sim + weighted_industry_sim + weighted_type_sim) / 3
    
    pattern_score = weighted_price_sim * 100
    #print(f"패턴 점수 (가격 유사도 * 100): {pattern_score}")
    
    return {
        'pattern': pattern_score,
        'bs': round(total_weighted_similarity, 2)
    } 

def get_most_similar_stock_by_category(category_id, user_id, days=30):
    
    category_stockids = get_stockids_by_category(category_id)
    
    if not category_stockids:
        return None
    
    best_stock = None
    best_similarity = -1
    
    # 각 종목에 대해 유사도 계산
    for stockid in category_stockids:
        try:
            similarity_score = calculate_weighted_similarity(stockid, user_id, days)
            pattern_similarity = similarity_score['pattern']
            bs_score = similarity_score['bs']
            
            if bs_score > best_similarity:
                best_similarity = bs_score
                
                # 종목 정보 가져오기
                stock = Stock.objects.get(id=stockid)
                industry_name = get_industry_name_by_stockid(stockid)

                #print(f"DEBUG: 파탄 점수: {pattern_similarity}")
                
                best_stock = {
                    'stockid': stockid,
                    'name': stock.name,
                    'type': stock.type,
                    'industry_name': industry_name or 'N/A',
                    'similarity_score': bs_score,
                    'pattern_similarity': pattern_similarity,
                }
        except Exception as e:
            continue
    
    return best_stock

def count_similar_stocks_by_user(user_id, stock_id):
    try:
        target_stock = Stock.objects.get(id=stock_id)
        target_type = target_stock.type
        target_industry_code = target_stock.industry_code
        
        mystocks = MyStock.objects.filter(userid=user_id)
        
        same_type_count = 0
        same_industry_count = 0
        
        for mystock in mystocks:
            try:
                stock = Stock.objects.get(id=mystock.stockid)                
                # 같은 type인지
                if stock.type == target_type:
                    same_type_count += 1
                
                # 같은 industry_code인지 
                if stock.industry_code == target_industry_code:
                    same_industry_count += 1
                
                    
            except Stock.DoesNotExist:
                continue
        
        return {
            'same_type_count': same_type_count,
            'same_industry_count': same_industry_count,
        }
        
    except Stock.DoesNotExist:
        return {
            'same_type_count': 0,
            'same_industry_count': 0,
        }

def get_stock_price_history(stock_id):
    try:

        price_logs = ClosingPriceLog.objects.filter(stockid=stock_id).order_by('-date')[:30]
        price_logs = list(price_logs)[::-1]  
        stock_name = Stock.objects.get(id=stock_id).name
        data = []
        for log in price_logs:
            data.append({
                'date': log.date.strftime('%Y-%m-%d'),
                'closing_price': log.closing_price
            })
        
        return {
            'stock_id': stock_id,
            'stock_name': stock_name,
            'data': data
        }
        
    except Exception as e:
        return {
            'stock_id': stock_id,
            'data': [],
            'error': str(e)
        } 