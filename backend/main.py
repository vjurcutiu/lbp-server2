
print("[main.py] main.py imported")

from fastapi import FastAPI
from database import engine, Base

print("[main.py] Importing routers...")
from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router
from pinecone_engine.pinecone_engine_routes import router as pinecone_router

from rate_limiter.rate_limiter_middleware import MachineGatewayMiddleware
from database import SessionLocal

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

# DB: Create tables on startup
print("[main.py] Creating DB tables...")
Base.metadata.create_all(bind=engine)

app = FastAPI()
print("[main.py] FastAPI app created")

app.add_middleware(MachineGatewayMiddleware, db_session_factory=SessionLocal)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all domains
    allow_credentials=False,    # Must be False if allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount all API routers here
app.include_router(openai_router, prefix="/api")
print("[main.py] Registered openai_router on /api")
app.include_router(user_router, prefix="/api")
print("[main.py] Registered user_router on /api")
app.include_router(payment_router, prefix="/api")
print("[main.py] Registered payment_router on /api")
app.include_router(pinecone_router, prefix="/api")
print("[main.py] Registered pinecone_router on /api")
