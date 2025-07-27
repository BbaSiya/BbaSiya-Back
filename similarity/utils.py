from similarity.models import MyStock
from stock.models import ClosingPriceLog, Stock, Industry
import numpy as np

def get_stock_trend(stockid, days=30):
    qs = ClosingPriceLog.objects.filter(stockid=stockid).order_by('-date')[:days]
    qs = list(qs)[::-1]  # 날짜 오름차순
    closing_prices = [row.closing_price for row in qs]
    updown_rates = [row.updown_rate for row in qs]
    return closing_prices, updown_rates

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
    prices1, _ = get_stock_trend(stockid1, days)
    prices2, _ = get_stock_trend(stockid2, days)
    if len(prices1) < days or len(prices2) < days:
        return 0.0
    price1_norm = zscore_normalize(prices1)
    price2_norm = zscore_normalize(prices2)
    price_dist = dtw_distance(price1_norm, price2_norm)
    price_sim = 1 / (1 + price_dist)
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
    
    for stockid, name, value, cnt, current_price in top5:
        weight = value / total_value if total_value > 0 else 0
        # 패턴
        price_sim = similarity_dtw_price(target_stockid, stockid, days)
        # 업종 유사도
        industry_name = get_industry_name_by_stockid(stockid)
        industry_sim = get_industry_similarity(target_industry, industry_name)
        # type 유사도
        type_sim = get_type_similarity(target_stockid, stockid)
        
        weighted_price_sim += price_sim * weight
        weighted_industry_sim += industry_sim * weight
        weighted_type_sim += type_sim * weight
        
    
    # 종합 유사도 계산 (가격, 업종, 타입 유사도의 평균)
    total_weighted_similarity = (weighted_price_sim + weighted_industry_sim + weighted_type_sim) / 3
    
    return round(total_weighted_similarity, 2) 