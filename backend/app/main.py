from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base

# Import all models so Alembic / Base.metadata sees them
import app.models.vehicle  # noqa
import app.models.user     # noqa
import app.models.dossier  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev mode — use Alembic in production)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
