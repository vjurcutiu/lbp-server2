from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
import stripe
import os
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_models import MachineAccount, UserTier
from rate_limiter.rate_limiter_services import reset_all_quotas
from database import get_db
import json

from payment.payment_services import (
    get_subscription_status,
    cancel_subscription,
    update_subscription_from_stripe,
    update_subscription_from_invoice,
    reactivate_subscription,
)

PROD = os.getenv('ENV', 'dev') == 'prod'

if PROD:
    SUCCESS_URL = "https://lexbot.pro/payment-success"
    CANCEL_URL = "https://lexbot.pro/payment-cancel"
else:
    SUCCESS_URL = "http://localhost:5173/payment-success"
    CANCEL_URL = "http://localhost:5173/payment-cancel"

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.get("/subscription-status")
def subscription_status(x_machine_id: str = Header(...), db: Session = Depends(get_db)):
    return get_subscription_status(x_machine_id, db)

@router.post("/cancel-subscription")
def cancel_subscription_route(x_machine_id: str = Header(...), db: Session = Depends(get_db)):
    ok, msg = cancel_subscription(x_machine_id, db)
    if not ok:
        raise HTTPException(404, msg)
    return {"message": msg}

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    machine_id = request.headers.get("X-Machine-ID")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'LexBot PRO Subscription'},
                    'unit_amount': 1900,
                    'recurring': {'interval': 'month'}
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            billing_address_collection='required',
            custom_fields=[{
                'key': 'cif',
                'label': {'type': 'custom', 'custom': 'CIF/CUI'},
                'type': 'text',
                'optional': False, 
            }],
            metadata={"machine_id": machine_id},
            subscription_data={"metadata": {"machine_id": machine_id}},
        )
        return {"url": session.url}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event['type']
    data_object = event['data']['object']

    print(f"[webhook/stripe] Event type: {event_type}")
    print(f"[webhook/stripe] Data: {json.dumps(data_object, indent=2)}")
    
    # Update subscription from subscription events
    if event_type.startswith("customer.subscription."):
        update_subscription_from_stripe(event, db)
    # Update from invoice on payment succeeded (and fetch subscription from Stripe)
    elif event_type == "invoice.payment_succeeded":
        update_subscription_from_invoice(event, db)
    # Optional: handle other invoice.* events if needed

    return {"ok": True}

@router.post("/reactivate-subscription")
def reactivate_subscription_route(x_machine_id: str = Header(...), db: Session = Depends(get_db)):
    ok, msg = reactivate_subscription(x_machine_id, db)
    if not ok:
        raise HTTPException(404, msg)
    return {"message": msg}