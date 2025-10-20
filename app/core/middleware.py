import time

from fastapi import Request

from app.logger import get_logger

logger = get_logger(name=__name__)


async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
        },
    )

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    logger.info(
        f"Request completed: {response.status_code}",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
        },
    )

    return response
