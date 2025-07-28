import os
from django.apps import AppConfig


class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start
            start()
            print("APScheduler 시작 요청 완료 (메인 프로세스에서만).")# 시작 확인 로그
        else:
            print("APScheduler 시작 건너뜀 (서브 프로세스 또는 초기 로드).")