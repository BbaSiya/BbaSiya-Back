from similarity.models import MyStock
from stock.models import ClosingPriceLog, Stock, Industry
from category.utils import get_stockids_by_category
import numpy as np


def get_stock_trend_with_dates(stockid, days=30):
    qs = ClosingPriceLog.objects.filter(stockid=stockid).order_by('-date')[:days]
    qs = list(qs)[::-1]  
    
    closing_prices = np.array([row.closing_price for row in qs])
    updown_rates = np.array([row.updown_rate for row in qs])
    dates = np.array([row.date.date() for row in qs])
    
    return closing_prices, updown_rates, dates


def batch_get_stock_trends(stockids, days=30):
    all_data = {}
    
    for stockid in stockids:
        try:
            prices, _, dates = get_stock_trend_with_dates(stockid, days)
            all_data[stockid] = (prices, dates)
        except Exception:
            continue
    
    return all_data


def find_common_dates(all_stock_data):
    if not all_stock_data:
        return np.array([])
    
    common_dates = set(all_stock_data[list(all_stock_data.keys())[0]][1])
    
    for stockid, (_, dates) in all_stock_data.items():
        common_dates = common_dates.intersection(set(dates))
    
    return np.array(sorted(list(common_dates)))


def extract_prices_for_dates(prices, dates, target_dates):
    if len(target_dates) == 0:
        return np.array([])
    
    date_indices = []
    for target_date in target_dates:
        matches = np.where(dates == target_date)[0]
        if len(matches) > 0:
            date_indices.append(matches[0])
    
    if len(date_indices) == 0:
        return np.array([])
    
    return prices[date_indices]


def create_price_matrix(stockids, all_stock_data, common_dates):
    if len(common_dates) == 0:
        return np.array([]), []
    
    valid_stockids = []
    price_matrix = []
    
    for stockid in stockids:
        if stockid in all_stock_data:
            prices, dates = all_stock_data[stockid]
            extracted_prices = extract_prices_for_dates(prices, dates, common_dates)
            
            if len(extracted_prices) == len(common_dates):
                price_matrix.append(extracted_prices)
                valid_stockids.append(stockid)
    
    return np.array(price_matrix), valid_stockids


def vectorized_dtw_similarity(target_prices, price_matrix):
    if len(price_matrix) == 0:
        return np.array([])
    
    similarities = np.zeros(len(price_matrix))
    
    for i in range(len(price_matrix)):
        if len(target_prices) >= 5 and len(price_matrix[i]) >= 5:
            target_norm = zscore_normalize(target_prices)
            stock_norm = zscore_normalize(price_matrix[i])
            
            price_dist = dtw_distance(target_norm, stock_norm)
            similarities[i] = 1 / (1 + price_dist)
        else:
            similarities[i] = 0.0
    
    return similarities


def batch_get_user_stock_info(user_id):
    mystocks = MyStock.objects.filter(userid=user_id)
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
    return result[:5]


def batch_get_industry_names(stockids):
    industry_names = {}
    stocks = Stock.objects.filter(id__in=stockids)
    
    for stock in stocks:
        try:
            industry = Industry.objects.get(industry_code=stock.industry_code)
            industry_names[stock.id] = industry.industry_name
        except Industry.DoesNotExist:
            industry_names[stock.id] = None
    
    return industry_names


def batch_get_stock_types(stockids):
    stock_types = {}
    stocks = Stock.objects.filter(id__in=stockids)
    
    for stock in stocks:
        stock_types[stock.id] = stock.type
    
    return stock_types


def vectorized_weighted_similarity(target_stockid, user_id, category_stockids, days=30):
    all_stock_data = batch_get_stock_trends(category_stockids, days)
    user_stocks = batch_get_user_stock_info(user_id)
    
    if not user_stocks or not all_stock_data:
        return np.zeros(len(category_stockids)), np.zeros(len(category_stockids))
    
    common_dates = find_common_dates(all_stock_data)
    
    if len(common_dates) < 5:
        return np.zeros(len(category_stockids)), np.zeros(len(category_stockids))
    
    price_matrix, valid_stockids = create_price_matrix(category_stockids, all_stock_data, common_dates)
    
    if len(price_matrix) == 0:
        return np.zeros(len(category_stockids)), np.zeros(len(category_stockids))
    
    user_stockids = [stock[0] for stock in user_stocks]
    user_stock_data = batch_get_stock_trends(user_stockids, days)
    
    all_stockids = list(set(category_stockids + user_stockids))
    industry_names = batch_get_industry_names(all_stockids)
    stock_types = batch_get_stock_types(all_stockids)
    
    total_price_similarities = np.zeros(len(valid_stockids))
    total_industry_similarities = np.zeros(len(valid_stockids))
    total_type_similarities = np.zeros(len(valid_stockids))
    total_value = sum([stock[2] for stock in user_stocks])
    
    for user_stockid, name, value, cnt, current_price in user_stocks:
        if user_stockid in user_stock_data:
            user_prices, user_dates = user_stock_data[user_stockid]
            user_extracted_prices = extract_prices_for_dates(user_prices, user_dates, common_dates)
            
            if len(user_extracted_prices) == len(common_dates):
                price_similarities = vectorized_dtw_similarity(user_extracted_prices, price_matrix)
                
                user_industry = industry_names.get(user_stockid)
                industry_similarities = np.array([
                    get_industry_similarity(user_industry, industry_names.get(stockid))
                    for stockid in valid_stockids
                ])
                
                user_type = stock_types.get(user_stockid)
                type_similarities = np.array([
                    get_type_similarity_from_types(user_type, stock_types.get(stockid))
                    for stockid in valid_stockids
                ])
                
                weight = value / total_value if total_value > 0 else 0
                total_price_similarities += price_similarities * weight
                total_industry_similarities += industry_similarities * weight
                total_type_similarities += type_similarities * weight
    
    total_similarities = (total_price_similarities + total_industry_similarities + total_type_similarities) / 3
    
    pattern_result = np.zeros(len(category_stockids))
    bs_result = np.zeros(len(category_stockids))
    
    for i, stockid in enumerate(category_stockids):
        if stockid in valid_stockids:
            valid_idx = valid_stockids.index(stockid)
            pattern_result[i] = round(total_price_similarities[valid_idx] * 100, 2)  # 패턴 점수 (소수점 2자리)
            bs_result[i] = round(total_similarities[valid_idx], 2)  # 종합 점수 (소수점 2자리)
    
    return pattern_result, bs_result


def zscore_normalize(vec):
    arr = np.array(vec)
    if len(arr) == 0:
        return arr
    return (arr - arr.mean()) / (arr.std() + 1e-8)


def dtw_distance(a, b):
    n, m = len(a), len(b)
    dtw = np.full((n+1, m+1), np.inf)
    dtw[0, 0] = 0
    
    a_arr = np.array(a)
    b_arr = np.array(b)
    
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(a_arr[i-1] - b_arr[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
    
    return dtw[n, m]


def get_industry_name_by_stockid(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        industry = Industry.objects.get(industry_code=stock.industry_code)
        return industry.industry_name
    except (Stock.DoesNotExist, Industry.DoesNotExist):
        return None


def get_industry_similarity(name1, name2):
    if name1 is None or name2 is None:
        return 0.3  
    if name1 == name2:
        return 1.0
    return 0.5


TYPE_SIM_MATRIX = {
    '성장주': {'성장주': 1.0, '가치주': 0.4, '배당주': 0.2},
    '가치주': {'성장주': 0.4, '가치주': 1.0, '배당주': 0.5},
    '배당주': {'성장주': 0.2, '가치주': 0.5, '배당주': 1.0},
}


def get_type_similarity_from_types(type1, type2):
    if not type1 or not type2:
        return 0.3  
    return TYPE_SIM_MATRIX.get(type1, {}).get(type2, 0.3)


def get_most_similar_stock_by_category(category_id, user_id, days=30):
    category_stockids = get_stockids_by_category(category_id)
    
    if not category_stockids:
        return None
    
    pattern_scores, bs_scores = vectorized_weighted_similarity(target_stockid=None, user_id=user_id, 
                                                              category_stockids=category_stockids, days=days)
    
    if len(bs_scores) == 0 or np.max(bs_scores) == 0:
        return None
    
    best_idx = np.argmax(bs_scores)
    best_stockid = category_stockids[best_idx]
    best_similarity = bs_scores[best_idx]
    best_pattern_score = pattern_scores[best_idx]
    
    try:
        stock = Stock.objects.get(id=best_stockid)
        industry_name = get_industry_name_by_stockid(best_stockid)
        
        best_stock = {
            'stockid': best_stockid,
            'name': stock.name,
            'type': stock.type,
            'industry_name': industry_name,
            'similarity_score': best_similarity,
            'pattern_similarity': best_pattern_score,
        }
        
        return best_stock
        
    except Stock.DoesNotExist:
        return None



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
                if stock.type == target_type:
                    same_type_count += 1
                
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