from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from app.config import settings
from app.routers import auth, chats

app = FastAPI(title="Ollama Network Chat API")


@app.on_event("startup")
async def startup():
    redis_instance = redis.from_url(settings.celery_broker_url)
    await FastAPILimiter.init(redis_instance)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chats.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
