import time
from tracemalloc import start
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware

#  ???  这里的__name__ 是什么意思?
logger = logging.getLogger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    # ???  这里的self
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()

        response = await call_next(request)

        duration = (
                    time.time() - start
                ) * 1000
        logger.info(
            {
                "event": "request_finished",
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round(
                    duration,
                    2,
                ),
            }
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response

