
print("[main.py] main.py imported")

from fastapi import FastAPI
from database import engine, Base

print("[main.py] Importing routers...")
from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router
from pinecone.pinecone_routes import router as pinecone_router

from dotenv import load_dotenv
load_dotenv()

# DB: Create tables on startup
print("[main.py] Creating DB tables...")
Base.metadata.create_all(bind=engine)

app = FastAPI()
print("[main.py] FastAPI app created")

# Mount all API routers here
app.include_router(openai_router, prefix="/api")
print("[main.py] Registered openai_router on /api")
app.include_router(user_router, prefix="/api")
print("[main.py] Registered user_router on /api")
app.include_router(payment_router, prefix="/api")
print("[main.py] Registered payment_router on /api")
app.include_router(pinecone_router, prefix="/api")
print("[main.py] Registered pinecone_router on /api")
