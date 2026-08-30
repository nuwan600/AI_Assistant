import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()

async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled system exception", error=str(exc), path=request.url.path)
    
    # Degrade gracefully with brand-safe error messaging
    return JSONResponse(
        status_code=500,
        content={
            "error": "Service Temporarily Unavailable",
            "message": "The assistant encountered a temporary failure interacting with internal services. Please try again or contact support.",
            "degraded": True
        }
    )