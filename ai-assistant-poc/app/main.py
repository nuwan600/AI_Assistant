from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.auth import router as auth_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(search_router, prefix=f"{settings.API_V1_STR}/rag", tags=["search"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Enterprise AI Assistant API is running"}