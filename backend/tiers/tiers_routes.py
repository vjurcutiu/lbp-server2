
print("[tiers_routes.py] tiers_routes.py imported")

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from database import get_db  # assumes you have a dependency that provides a DB session
from rate_limiter.rate_limiter_models import MachineAccount, UserTier
from typing import Optional
from rate_limiter.rate_limiter_services import reset_all_quotas


router = APIRouter()

def get_account(db: Session, machine_id: str) -> Optional[MachineAccount]:
    print("[tiers_routes.py] get_account called with machine_id:", machine_id)
    return db.query(MachineAccount).filter_by(machine_id=machine_id).first()

@router.get("/tier")
def get_tier(machine_id: str, db: Session = Depends(get_db)
):
    print("[tiers_routes.py] Entered: get_tier /api/tier")
    account = get_account(db, machine_id)
    if not account:
        print("[tiers_routes.py] Machine ID not found")
        raise HTTPException(status_code=404, detail="Machine ID not found")
    return {
        "machine_id": account.machine_id,
        "tier": account.tier.value,
        "is_active": account.is_active,
        "email": account.email,
        "created_at": account.created_at,
        "upgraded_at": account.upgraded_at,
    }

@router.post("/tier/upgrade")
def upgrade_tier(machine_id: str, new_tier: UserTier, db: Session = Depends(get_db)
):
    print("[tiers_routes.py] Entered: upgrade_tier /api/tier/upgrade")
    account = get_account(db, machine_id)
    if not account:
        print("[tiers_routes.py] Machine ID not found (upgrade)")
        raise HTTPException(status_code=404, detail="Machine ID not found")
    account.tier = new_tier
    if new_tier == UserTier.pro:
        from datetime import datetime
        account.upgraded_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "machine_id": machine_id, "tier": account.tier.value}

@router.post("/tier/ban")
def ban_user(machine_id: str, db: Session = Depends(get_db)
):
    print("[tiers_routes.py] Entered: ban_user /api/tier/ban")
    account = get_account(db, machine_id)
    if not account:
        print("[tiers_routes.py] Machine ID not found (ban)")
        raise HTTPException(status_code=404, detail="Machine ID not found")
    account.tier = UserTier.banned
    account.is_active = False
    db.commit()
    return {"status": "banned", "machine_id": machine_id}

@router.post("/tier/unban")
def unban_user(machine_id: str, db: Session = Depends(get_db)
):
    print("[tiers_routes.py] Entered: unban_user /api/tier/unban")
    account = get_account(db, machine_id)
    if not account:
        print("[tiers_routes.py] Machine ID not found (unban)")
        raise HTTPException(status_code=404, detail="Machine ID not found")
    account.tier = UserTier.demo
    account.is_active = True
    db.commit()
    return {"status": "unbanned", "machine_id": machine_id}

@router.get("/tiers/all")
def list_accounts(
    tier: Optional[UserTier] = Query(None),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
):
    print("[tiers_routes.py] Entered: list_accounts /api/tiers/all")
    query = db.query(MachineAccount)
    if tier:
        query = query.filter_by(tier=tier)
    accounts = query.offset(offset).limit(limit).all()
    return [
        {
            "machine_id": acc.machine_id,
            "tier": acc.tier.value,
            "is_active": acc.is_active,
            "email": acc.email,
            "created_at": acc.created_at,
            "upgraded_at": acc.upgraded_at,
        }
        for acc in accounts
    ]

# Utility for integration with payment_routes
def set_user_pro(db: Session, machine_id: str, email: Optional[str] = None):
    print("[tiers_routes.py] set_user_pro called")
    account = get_account(db, machine_id)
    from datetime import datetime
    if not account:
        print("[tiers_routes.py] Account auto-created in set_user_pro")
        account = MachineAccount(
            machine_id=machine_id,
            tier=UserTier.pro,
            is_active=True,
            email=email,
            upgraded_at=datetime.utcnow(),
        )
        db.add(account)
    else:
        account.tier = UserTier.pro
        account.is_active = True
        account.email = email or account.email
        account.upgraded_at = datetime.utcnow()
    db.commit()
    return account
