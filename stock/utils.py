from .models import Stock, ClosingPriceLog, Industry
import os, requests
from dotenv import load_dotenv
from pathlib import Path
from holidayskr import is_holiday
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
 
def get_stock_info(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        return {
            'id': stock.id,
            'industry_code': stock.industry_code,
            'name': stock.name,
            'volume_power': stock.volume_power,
            'current_price': stock.current_price,
            'type': stock.type,
            'eq': stock.eq,
            'country': stock.country,
            'updown_rate': stock.updown_rate,
        }
    except Stock.DoesNotExist:
        return None 
    
    
def check_domestic(stockid):
    domestic = [
    "005930",  # 삼성전자
    "034220",  # LG디스플레이
    "006800",  # 미래에셋증권
    "000660",  # SK하이닉스
    "323410",  # 카카오뱅크
    "095700",  # 제넥신
    "042660",  # 한화오션 (구 대우조선해양)
    "003670",  # 포스코퓨처엠
    "010140",  # 삼성중공업
    "001510",  # SK증권
    ]
    foreign = [
    ("02209", "HKS"),     # YESASIA HLDGS (HKEX)
    ("01810", "HKS"),     # 샤오미그룹 (HKEX)
    ("06181", "HKS"),     # 라오푸골드 (HKEX)
	  ("00700", "HKS"),     # 텐센트 (HKEX)
	  
	  #10개
    ("GXIG", "AMS"),     # GLOBAL X INVESTMENT GRADE CORPORATE BOND (ETF / NASDAQ)
    ("BLOK", "AMS"),     # AMPLIFY TRANSFORMATIONAL DATA SHARING (NYSE Arca or NASDAQ)
    ("IGV", "AMS"),      # ISHARES NORTH AMERICAN TECH SOFTWARE (ETF / NASDAQ)
    ("SHLD", "AMS"),     # GLOBAL X DEFENSE TECH (ETF / NASDAQ)
    ("REMX", "AMS"),     # VANECK RARE EARTH/STRATEGIC METALS (NYSE Arca)
    ("SCHD", "AMS"),     # SCHWAB US DIVIDEND EQUITY (NYSE Arca)
    ("SOXL", "AMS"),     # DIREXION SEMICONDUCTOR DAILY 3X (NASDAQ)
    ("EWY", "AMS"),      # ISHARES MSCI SOUTH KOREA CAPPED (NYSE Arca)
    ("VOO", "AMS"),      # VANGUARD S&P 500 (NYSE Arca)
    ("SPY", "AMS"),      # SPDR S&P 500 (NYSE Arca)
        
    ("2837", "TSE"),    # GLOBAL X HANG SENG TECH HKD (HKEX ETF)
    
    #8개
    ("BABA", "NYS"),     # 알리바바그룹홀딩스 (NYSE)
    ("VG", "NYS"),       # 벤처 글로벌 (비상장 추정, 예시로 NAS)
    ("CRCL", "NYS"),     # 서클 인터넷 그룹 (Circle / NASDAQ)
    ("DOCS", "NYS"),     # 독시미티 (Doximity) (NASDAQ)
    ("IONQ", "NYS"),     # 아이온큐 (NASDAQ)
    ("GEV", "NYS"),      # GE베르노바 (NYSE)
    ("JOBY", "NYS"),     # 조비 에비에이션 (NYSE)
    ("TSM", "NYS"),     # TSMC(ADR) (NYSE)
    
    #15개
    ("COIN", "NAS"),     # 코인베이스 글로벌 (NASDAQ)
    ("APP", "NAS"),      # 앱플로빈 (NASDAQ)
    ("GPRE", "NAS"),     # 그린 플레인스 (NASDAQ)
    ("ASML", "NAS"),     # ASML 홀딩(ADR) (NASDAQ)
    ("NFLX", "NAS"),     # 넷플릭스 (NASDAQ)
    ("PLTR", "NAS"),     # 팔란티어 테크 (NYSE 이후 → NASDAQ)
    ("TSLL", "NAS"),     # DIREXION TSLA DAILY 2X (ETF / NASDAQ)
    ("RKLB", "NAS"),     # 로켓 랩 (NASDAQ)
    ("HOOD", "NAS"),     # 로빈훗 마케츠 (NASDAQ)
    ("RGTI", "NAS"),     # 리게티 컴퓨팅 (NASDAQ)
    ("NVDA", "NAS"),     # 엔비디아 (NASDAQ)
    ("TSLA", "NAS"),     # 테슬라 (NASDAQ)
    ("AVGO", "NAS"),     # 브로드컴 (NASDAQ)
    ("AAPL", "NAS"),     # 애플 (NASDAQ)
    ("QQQ", "NAS"),      # INVESCO QQQ TRUST (NASDAQ)
    ]
    
    if stockid in domestic:
        return True
    else:
        return False


def recent_business_day():
    # 한국 시간
    kst_offset = timedelta(hours=9)
    now_kst = datetime.utcnow() + kst_offset
    current_date = now_kst.date()

    while True:
        # 평일 확인 (월요일=0, 일요일=6)
        is_weekday = current_date.weekday() < 5
        # 공휴일 확인
        is_holiday_status = is_holiday(current_date.strftime("%Y-%m-%d"))

        if is_weekday and not is_holiday_status:
            return current_date
        else:
            current_date -= timedelta(days=1)


def find_unit(country):
    if country == "TSE":
        return "JPY(100)"
    elif country == "HKS":
        return "HKD"
    else:
        return "USD"

def replace_comma(price):
    return float(price.replace(",", ""))

def exchange(cur_unit, prpr):
    try:
        url = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
        date = recent_business_day()
        params = {
            "authkey" : os.getenv("KORAEXIM_API_KEY"),
            "data" : "AP01",
            "searchdate" : date
        }
        response = requests.get(url, params=params)
        data = response.json()
        for item in data:
            if item.get("cur_unit") == cur_unit:
                prpr = float(prpr)
                ttb = replace_comma(item.get("ttb"))
                if cur_unit == "JPY(100)":
                    return (prpr*ttb)/100
                else:
                    return prpr*ttb

    except Exception as e:
        print(e)
        return None


def renew_stockinfo(stocklist):
    try:
        """
        국내/해외 확인 후
        현재가, 등락률, 체결 강도 조회 및 DB 업데이트
        해외주식의 경우 달러->원 변환
        """
        base_url = "https://openapi.koreainvestment.com:9443"
        headers = {
            "content-type" : "application/json",
            "authorization" : "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImVkMzcwNTQ3LWYxYzctNDEwMS04MzU3LWJlZmI5YjY5YjU3YiIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc1MzY5NDA0NCwiaWF0IjoxNzUzNjA3NjQ0LCJqdGkiOiJQUzhlYmFRdG1DZ0dWYk1xeFpmOXdsOWtkVjl4Wnl3ZFkxYTQifQ.ikevgC1pd3Z3bpoDvOC_DN5TfL5qge2en_K3RHc868LcprovjopL_9VSIdwnKbkrBY8L6Ogr9p9M-8kMapGglQ",
            "appkey" : os.getenv("KIS_APPKEY"),
            "appsecret" : os.getenv("KIS_APPSECRET"),
            "tr_id" : "FHKST01010300",
            "custtype" : "P"
        }
        for stockcode in stocklist:
            stock = Stock.objects.get(id=stockcode)
            if check_domestic(stockcode):
                url = base_url + "/uapi/domestic-stock/v1/quotations/inquire-ccnl"
                params = {
                    "FID_COND_MRKT_DIV_CODE" : "J",
                    "FID_INPUT_ISCD" : stockcode
                }
                response = requests.get(url, headers=headers, params=params)
                data = response.json()

                prpr = data["output"][0]["stck_prpr"]
                rate = data["output"][0]["prdy_ctrt"]
                volume_power = data["output"][0]["tday_rltv"]

                #업데이트
                stock.current_price = prpr
                stock.updown_rate = rate
                stock.volume_power = volume_power

            else:
                url = base_url + "/uapi/overseas-price/v1/quotations/inquire-ccnl"
                headers.update({
                    "tr_id" : "HHDFS76200300"
                })
                params = {
                    "EXCD" : stock.country,
                    "AUTH" : "",
                    "KEYB" : "",
                    "TDAY" : "1",
                    "SYMB" : stockcode
                }
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                if not data["output1"]:
                    continue
                rate = data["output1"][0]["rate"]
                volume_power = data["output1"][0]["vpow"]

                url = base_url + "/uapi/overseas-price/v1/quotations/price-detail"
                headers.update({
                    "tr_id" : "HHDFS76200200"
                })
                params = {
                    "EXCD" : stock.country,
                    "AUTH" : "",
                    "SYMB" : stockcode
                }
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                if not data["output"]:
                    continue
                prpr = data["output"]["last"]
                cur_unit = find_unit(stock.country)
                changed_price = exchange(cur_unit, prpr)

                stock.current_price = changed_price
                stock.updown_rate = rate
                stock.volume_power = volume_power

            stock.save()
        return None
    except Exception as e:
        print(e)
        return None

def get_industry_name_by_stockid(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        industry = Industry.objects.get(industry_code=stock.industry_code)
        return industry.industry_name
    except (Stock.DoesNotExist, Industry.DoesNotExist):
        return None 