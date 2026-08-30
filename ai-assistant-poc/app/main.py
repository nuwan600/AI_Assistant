from app.core.exceptions import global_exception_handler
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.auth import router as auth_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
setup_logging()

from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.openapi.utils import get_openapi
import json

from fastapi.responses import JSONResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,  # Custom docs route configured below for fast CDN loading
    openapi_url=None,  # Custom openapi endpoint configured below
    redoc_url="/redoc"
)

# Register Degradation Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Include API Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(search_router, prefix=f"{settings.API_V1_STR}/rag", tags=["search"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

# OpenAPI Specification endpoint
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(custom_openapi())

# Fast Swagger UI Docs endpoint (using Cloudflare CDN)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui-bundle.min.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.18.2/swagger-ui.min.css"
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/")
async def root():
    return {"message": "Enterprise AI Assistant API is running"}

def custom_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Enterprise AI Assistant API with RAG and Multi-Agent Orchestration",
        routes=app.routes,
    )
    
    # Standardize verbose auto-generated Body_* schema names
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    paths_str = json.dumps(openapi_schema.get("paths", {}))
    
    for key in list(schemas.keys()):
        if key.startswith("Body_"):
            clean_name = "LoginRequest" if any(w in key.lower() for w in ["login", "auth", "token"]) else key.replace("Body_", "")
            schemas[clean_name] = schemas.pop(key)
            schemas[clean_name]["title"] = clean_name
            paths_str = paths_str.replace(f"#/components/schemas/{key}", f"#/components/schemas/{clean_name}")
            
    openapi_schema["paths"] = json.loads(paths_str)
    return openapi_schema

app.openapi = custom_openapi