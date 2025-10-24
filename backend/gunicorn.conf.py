import multiprocessing

# 서버 바인딩
bind = "0.0.0.0:8080"

# 워커 프로세스 수 (CPU 코어 수에 따라 자동 조절)
workers = multiprocessing.cpu_count() * 2 + 1

# 비동기 처리를 위한 워커 클래스
worker_class = "uvicorn.workers.UvicornWorker"

# 동시 연결 수
worker_connections = 1000

# 연결 유지 시간
keepalive = 5

# 앱 미리 로드 (메모리 절약)
preload_app = True