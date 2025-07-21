from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_services import get_or_create_machine_account
from rate_limiter.rate_limiter_models import UserTier

ALLOWED_PATHS = {"/api/webhook/stripe"}

class MachineGatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory

    async def dispatch(self, request: Request, call_next):
        print("=== [Middleware] Incoming Request ===")
        print("Path:", request.url.path)
        print("Headers:")
        for k, v in request.headers.items():
            print(f"  {k}: {v}")

        if not request.url.path.startswith("/api") or request.url.path in ALLOWED_PATHS:
            return await call_next(request)

        machine_id = request.headers.get('X-Machine-Id') or request.headers.get('X-Machine-ID')

        if not machine_id:
            print("[Middleware] ❌ Missing X-Machine-Id header")
            return Response("Missing MachineID", status_code=400)

        print("[Middleware] ✅ Found machine ID:", machine_id)

        db: Session = self.db_session_factory()
        try:
            from rate_limiter.rate_limiter_services import get_or_create_machine_account
            account = get_or_create_machine_account(db, machine_id)

            if account.tier == UserTier.banned:
                print("[Middleware] ❌ Account is banned:", machine_id)
                return Response("Account banned", status_code=403)

            print("[Middleware] ✅ Account tier:", account.tier)
            request.state.account = account
            return await call_next(request)

        finally:
            db.close()