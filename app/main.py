# TODO: добавить middleware для логирования каждого запроса (request_id, latency)
# TODO: добавить CORS-настройки, если реестр будет доступен из браузера
# TODO: добавить rate limiting для защиты от перегрузки
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.database import init_db
from app.routers import models as models_router
from app.routers import versions as versions_router

app = FastAPI(
    title="Model Registry",
    description="Внутренний реестр ML-моделей.",
    version="0.1.0",
    # TODO: в production выставить docs_url=None, redoc_url=None
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(models_router.router)
app.include_router(versions_router.router)
@app.get("/health", tags=["system"])
def health_check():
    return JSONResponse({"status": "ok"})

@app.get("/", tags=["system"], include_in_schema=False)
def root():
    return JSONResponse({"service": "Model Registry", "version": "0.1.0", "docs": "/docs"})
