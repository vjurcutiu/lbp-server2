from fastapi import FastAPI
from database import engine, Base

from openai_api.openai_routes import router as openai_router
from payment.payment_routes import router as payment_router
from tiers.tiers_routes import router as user_router

# DB: Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Mount all API routers here
app.include_router(openai_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
