from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal

from rate_limiter.rate_limiter_middleware import MachineGatewayMiddleware
from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router
from pinecone_engine.pinecone_engine_routes import router as pinecone_router
from updates.update_routes import router as update_router

import os

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.routing import APIRoute

# --- New: For 405 exception handler ---
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

load_dotenv()

# DB: Create tables on startup
Base.metadata.create_all(bind=engine)

# Main FastAPI app (serves static files and mounts /api)
app = FastAPI()

# --- New: Middleware to log all incoming requests ---
@app.middleware("http")
async def log_request_method(request: Request, call_next):
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"[REQUEST] {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# --- New: Custom 405 handler to log allowed methods ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 405:
        logger = logging.getLogger("uvicorn.error")
        logger.error(
            f"[405] Method Not Allowed: {request.method} {request.url.path} | Detail: {exc.detail}"
        )
        return JSONResponse(
            status_code=405,
            content={"detail": f"Method Not Allowed: {request.method} {request.url.path}"}
        )
    # Let all other HTTPExceptions pass through
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail})

# Serve frontend at /


# Add middleware to the main app for API routes
db_factory = SessionLocal
app.add_middleware(MachineGatewayMiddleware, db_session_factory=db_factory)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers with the /api prefix
app.include_router(openai_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(pinecone_router, prefix="/api")
app.include_router(update_router, prefix="/api")

if os.path.isdir("frontend_build"):
    app.mount("/", StaticFiles(directory="frontend_build", html=True), name="static")
else:
    print("frontend_build directory not found, skipping static mount")

# Log all routes for verification
logger = logging.getLogger("uvicorn.error")
for route in app.routes:
    if isinstance(route, APIRoute):
        logger.info(f"[ROUTE] {route.path} METHODS: {route.methods}")

print("[main.py] All routers registered on /api via direct include")
