from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_services import get_usage
from database import get_db
from rate_limiter.rate_limiter_config import TIER_LIMITS

router = APIRouter()

@router.get("/usage")
def get_usage_status(request: Request, db: Session = Depends(get_db)):
    account = request.state.account  # set by your middleware
    usage = {}
    updated = False
    for feature in ['files', 'messages']:
        stats = get_usage(db, account.machine_id, feature)
        # Get current config limit
        config_limit = TIER_LIMITS[account.tier.value][feature]
        if stats:
            # Update limit if needed
            if stats.limit != config_limit:
                print(f"[RateLimiter] Updating limit for {account.machine_id} {feature} from {stats.limit} to {config_limit}")
                stats.limit = config_limit
                updated = True
            usage[feature] = {
                "used": stats.used,
                "limit": stats.limit
            }
        else:
            usage[feature] = {
                "used": 0,
                "limit": config_limit
            }
    if updated:
        db.commit()
    return usage
