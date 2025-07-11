from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from backend.rate_limiter.rate_limiter_services import get_or_create_machine_account
from backend.rate_limiter.rate_limiter_models import UserTier

class MachineGatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory

    async def dispatch(self, request: Request, call_next):
        machine_id = request.headers.get('X-Machine-ID')
        if not machine_id:
            return Response("Missing MachineID", status_code=400)
        db: Session = self.db_session_factory()
        account = get_or_create_machine_account(db, machine_id)
        if account.tier == UserTier.banned:
            db.close()
            return Response("Account banned", status_code=403)
        request.state.account = account
        db.close()
        return await call_next(request)