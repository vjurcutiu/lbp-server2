from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.rate_limiter.rate_limiter_services import check_and_increment_usage

def quota_check(feature: str):
    def dependency(request: Request, db: Session = Depends()):
        account = request.state.account
        allowed = check_and_increment_usage(
            db, account.machine_id, account.tier.value, feature
        )
        if not allowed:
            raise HTTPException(429, f"{feature.capitalize()} quota exceeded")
    return dependency