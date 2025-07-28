from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from .utils import renew_token


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(renew_token, 'cron', hour=8)
    scheduler.start()