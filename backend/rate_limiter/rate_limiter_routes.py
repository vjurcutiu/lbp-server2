from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_services import get_usage
from database import get_db

router = APIRouter()

@router.get("/usage")
def get_usage_status(request: Request, db: Session = Depends(get_db)):
    account = request.state.account  # set by your middleware
    usage = {}
    for feature in ['files', 'messages']:  # or whatever features you want
        stats = get_usage(db, account.machine_id, feature)
        if stats:
            usage[feature] = {
                "used": stats.used,
                "limit": stats.limit
            }
        else:
            usage[feature] = {
                "used": 0,
                "limit": 0
            }
    return usage
