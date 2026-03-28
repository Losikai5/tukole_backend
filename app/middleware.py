from fastapi import FastAPI, Request
import time
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logging.getLogger("uvicorn.access").disabled = True

def register_middleware(app: FastAPI):

    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        
        host = getattr(request.client, "host", "-")
        port = getattr(request.client, "port", "-")
        
        print(f"{host}:{port} - {request.method} {request.url.path} "
              f"[{response.status_code}] {time.time() - start_time:.2f}s")
        
        return response

    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"],
    )