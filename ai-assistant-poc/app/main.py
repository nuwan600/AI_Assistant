from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.auth import router as auth_router

setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Enterprise AI Assistant API is running"}