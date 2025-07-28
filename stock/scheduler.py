from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from .utils import renew_token, renew_daily_price


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(renew_token, 'cron', hour=8)
    scheduler.start()

def daily_price():
    scheduler = BackgroundScheduler()
    #scheduler.add_job(renew_daily_price, 'cron', hour=8, minute=5)
    scheduler.add_job(renew_daily_price, 'cron', minute=15)
    scheduler.start()