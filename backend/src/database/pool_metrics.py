"""DB 연결 풀 메트릭 수집 (추후 구현)

TODO: Prometheus + Grafana 연동 시 구현
- SQLAlchemy pool events 연결
- Gauge/Counter 메트릭 정의
- /metrics 엔드포인트 연동
"""

# TODO: Prometheus 클라이언트 import
# from prometheus_client import Gauge, Counter

# TODO: 메트릭 정의
# db_pool_size = Gauge('db_pool_size', 'Current pool size')
# db_pool_checked_out = Gauge('db_pool_checked_out', 'Checked out connections')
# db_pool_overflow = Gauge('db_pool_overflow', 'Overflow connections')
# db_pool_timeouts = Counter('db_pool_timeouts_total', 'Pool timeout errors')


def setup_pool_metrics(engine):
    """DB 연결 풀 메트릭 이벤트 리스너 설정 (추후 구현)

    Args:
        engine: SQLAlchemy async engine

    TODO: SQLAlchemy pool events 연결
    - connect: 새 연결 생성 시
    - checkout: 연결 체크아웃 시
    - checkin: 연결 반환 시
    - close: 연결 종료 시
    """
    pass
    # TODO: event.listens_for(engine.pool, "connect") 등록
    # TODO: event.listens_for(engine.pool, "checkout") 등록
    # TODO: event.listens_for(engine.pool, "checkin") 등록
    # TODO: event.listens_for(engine.pool, "close") 등록
