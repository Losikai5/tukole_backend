from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger("uvicorn.access")
logger.disabled = True

def register_middleware(app: FastAPI):
    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
             start_time = time.time()
             response = await call_next(request)
             process_time = time.time() - start_time
             message = f"{request.client.host} {request.client.port} - {request.method} {request.url.path}-{request.status_code} completed in {process_time:.2f}s"
             return message
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"],
    )