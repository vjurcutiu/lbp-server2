from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models import MachineAccount, UserTier
from services import reset_all_quotas

router = APIRouter()

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends()):
    # For demo, pretend the event is a success and contains a machine_id in query params
    params = dict(request.query_params)
    machine_id = params.get("machine_id")
    event_type = params.get("event_type", "invoice.payment_succeeded")

    account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    if event_type == "invoice.payment_succeeded":
        account.tier = UserTier.pro
        reset_all_quotas(account, db)
        db.commit()
    elif event_type == "customer.subscription.deleted":
        account.tier = UserTier.demo
        reset_all_quotas(account, db)
        db.commit()
    return {"ok": True}