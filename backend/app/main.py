from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.session import Base, SessionLocal, engine
from app.security.auth import seed_users


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.data_upload_directory.mkdir(parents=True, exist_ok=True)
    settings.export_directory.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_users(db)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)

