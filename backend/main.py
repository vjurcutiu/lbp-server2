from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal

from rate_limiter.rate_limiter_middleware import MachineGatewayMiddleware
from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router
from pinecone_engine.pinecone_engine_routes import router as pinecone_router
from updates.update_routes import router as update_router  # <-- Add this at the top with other imports

import os

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# DB: Create tables on startup
Base.metadata.create_all(bind=engine)

# Main FastAPI app (serves static files and mounts /api)
app = FastAPI()

# Serve frontend at /
if os.path.isdir("frontend_build"):
    app.mount("/", StaticFiles(directory="frontend_build", html=True), name="static")
else:
    print("frontend_build directory not found, skipping static mount")

# --------- API sub-app with middleware ----------
api_app = FastAPI()

# Add your middleware to the API app
api_app.add_middleware(MachineGatewayMiddleware, db_session_factory=SessionLocal)
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers on the sub-app
api_app.include_router(openai_router, prefix="")
api_app.include_router(user_router, prefix="")
api_app.include_router(payment_router, prefix="")
api_app.include_router(pinecone_router, prefix="")
api_app.include_router(update_router, prefix="")

# Mount /api so all requests to /api/* go through the sub-app and its middleware
app.mount("/api", api_app)

# (No need to include routers on the main app anymore!)

print("[main.py] All routers registered on /api (via sub-app)")

import logging
logger = logging.getLogger("uvicorn.error")
for route in api_app.routes:
    logger.info(f"[ROUTE] {route.path} METHODS: {route.methods}")
