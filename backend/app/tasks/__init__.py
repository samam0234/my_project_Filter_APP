"""비동기/배치 작업 패키지.

run_batch_job 이 한 장씩 처리한다.
BATCH_USE_CELERY=true 이고 celery 가 있으면 Redis 워커로 넘긴다.
"""
