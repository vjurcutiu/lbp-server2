from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import os
import logging
from dotenv import load_dotenv

# --- Your database, routers, and middleware imports ---
from database import engine, Base, SessionLocal
from rate_limiter.rate_limiter_middleware import MachineGatewayMiddleware
from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router
from pinecone_engine.pinecone_engine_routes import router as pinecone_router
from updates.update_routes import router as update_router
from rate_limiter.rate_limiter_routes import router as rate_limiter_router


from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

# --- Setup ---
load_dotenv()

FRONTEND_BUILD_DIR = "frontend_build"
INDEX_FILE = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Logging middleware (optional) ---
@app.middleware("http")
async def log_request_method(request: Request, call_next):
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"[REQUEST] {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# --- 405 handler (optional, for nicer errors) ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # SPA fallback for 404: serve index.html if NOT /api and GET/HEAD
    if exc.status_code == 404 and request.method in ("GET", "HEAD"):
        if not request.url.path.startswith("/api"):
            if os.path.isfile(INDEX_FILE):
                return FileResponse(INDEX_FILE)
    # 405 Method Not Allowed: log it and show better message
    if exc.status_code == 405:
        logger = logging.getLogger("uvicorn.error")
        logger.error(
            f"[405] Method Not Allowed: {request.method} {request.url.path} | Detail: {exc.detail}"
        )
        return JSONResponse(
            status_code=405,
            content={"detail": f"Method Not Allowed: {request.method} {request.url.path}"}
        )
    # All other errors
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# --- CORS and custom middleware ---
db_factory = SessionLocal
app.add_middleware(MachineGatewayMiddleware, db_session_factory=db_factory)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(openai_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(pinecone_router, prefix="/api")
app.include_router(update_router, prefix="/api")
app.include_router(rate_limiter_router, prefix="/api")

# --- Serve the React build from "/" ---
if os.path.isdir(FRONTEND_BUILD_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=False), name="static")
else:
    print("frontend_build directory not found, skipping static mount")

# --- Log routes at startup (optional) ---
logger = logging.getLogger("uvicorn.error")
for route in app.routes:
    if isinstance(route, APIRoute):
        logger.info(f"[ROUTE] {route.path} METHODS: {route.methods}")

print("[main.py] All routers registered on /api via direct include")
