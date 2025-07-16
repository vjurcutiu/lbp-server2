from fastapi import APIRouter, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse
import stripe
import os
import smtplib
from email.message import EmailMessage
from tiers.tiers_routes import set_user_pro
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_models import MachineAccount, UserTier
from rate_limiter.rate_limiter_services import reset_all_quotas
from database import get_db

PROD = os.getenv('ENV', 'dev') == 'prod'

if PROD:
    SUCCESS_URL = "https://lexbot.pro/payment-success"
    CANCEL_URL = "https://lexbot.pro/payment-cancel"
else:
    SUCCESS_URL = "http://localhost:5173/payment-success"
    CANCEL_URL = "http://localhost:5173/payment-cancel"

def send_license_email(email: str, uuid: str):
    # Example email text
    subject = "Your LexBot PRO Subscription is Active!"
    body = (
        f"Hi,\n\n"
        f"Thank you for your purchase! Your license (ID: {uuid}) is now active.\n"
        f"You can now use all LexBot PRO features.\n\n"
        f"Best regards,\nThe LexBot Team"
    )
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "noreply@yourapp.com"
    msg["To"] = email
    msg.set_content(body)

    # Replace with your SMTP server details
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"Sent license confirmation email to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    machine_id = request.headers.get("X-Machine-ID")
    print(f"[checkout-session] X-Machine-ID header: {machine_id}")

    try:
        print("[checkout-session] Creating Stripe Checkout Session with the following params:")
        print({
            "payment_method_types": ['card'],
            "line_items": [{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'LexBot PRO Subscription'},
                    'unit_amount': 1900,
                    'recurring': {'interval': 'month'}
                },
                'quantity': 1,
            }],
            "mode": 'subscription',
            "success_url": SUCCESS_URL,
            "cancel_url": CANCEL_URL,
            "billing_address_collection": 'required',
            "custom_fields": [{
                'key': 'cif',
                'label': {'type': 'custom', 'custom': 'CIF/CUI'},
                'type': 'text',
                'optional': False, 
            }],
            "metadata": {"machine_id": machine_id},
            "subscription_data": {"metadata": {"machine_id": machine_id}},
        })

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
            subscription_data={
                "metadata": {"machine_id": machine_id}
            },
        )

        print(f"[checkout-session] Created Stripe session id: {session.id}")
        print(f"[checkout-session] Stripe session metadata: {session.metadata}")
        print(f"[checkout-session] Stripe session subscription: {session.subscription}")

        # Fetch the created subscription immediately and print metadata
        if session.subscription:
            sub = stripe.Subscription.retrieve(session.subscription)
            print(f"[checkout-session] Subscription id: {sub.id}")
            print(f"[checkout-session] Subscription metadata: {sub.metadata}")

        return {"url": session.url}
    except Exception as e:
        print(f"[checkout-session] Exception occurred: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    print(f"[webhook/stripe] Received webhook call.")
    print(f"[webhook/stripe] Headers: {dict(request.headers)}")
    print(f"[webhook/stripe] Raw body: {payload}")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        print("[webhook/stripe] Invalid payload error!")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        print("[webhook/stripe] Signature verification error!")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event['type']
    data_object = event['data']['object']
    print(f"[webhook/stripe] Event type: {event_type}")
    print(f"[webhook/stripe] Data object: {data_object}")

    if event_type == "invoice.payment_succeeded":
        # Try invoice metadata
        machine_id = data_object.get('metadata', {}).get('machine_id')
        if not machine_id:
            # 1. Try all line items
            lines = data_object.get('lines', {}).get('data', [])
            for item in lines:
                machine_id = item.get('metadata', {}).get('machine_id')
                if machine_id:
                    print(f"[webhook/stripe] machine_id found in line_item: {machine_id}")
                    break
        if not machine_id:
            # 2. Try parent.subscription_details.metadata
            parent = data_object.get('parent', {})
            sub_details = parent.get('subscription_details', {}) if parent else {}
            machine_id = sub_details.get('metadata', {}).get('machine_id')
            if machine_id:
                print(f"[webhook/stripe] machine_id found in parent.subscription_details: {machine_id}")
        if not machine_id:
            # 3. (if available) Fallback to classic way: fetch subscription if there's a subscription id
            subscription_id = data_object.get('subscription')
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                machine_id = subscription.get('metadata', {}).get('machine_id')
                if machine_id:
                    print(f"[webhook/stripe] machine_id found from subscription fetch: {machine_id}")
        if not machine_id:
            print(f"[webhook/stripe] invoice.payment_succeeded still missing machine_id. Event ID: {event['id']}")
            return {"ok": True}

        account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
        print(f"[webhook/stripe] Queried MachineAccount: {account}")
        if not account:
            print(f"[webhook/stripe] No account found for machine_id {machine_id}")
            return {"ok": True}
        print(f"[webhook/stripe] Account tier before update: {account.tier}")
        account.tier = UserTier.pro
        reset_all_quotas(account, db)
        db.commit()
        db.refresh(account)
        print(f"[webhook/stripe] Account tier after update: {account.tier}")
        return {"ok": True}

    elif event_type == "customer.subscription.deleted":
        machine_id = data_object.get('metadata', {}).get('machine_id')
        if not machine_id:
            # 1. Try all line items
            lines = data_object.get('lines', {}).get('data', [])
            for item in lines:
                machine_id = item.get('metadata', {}).get('machine_id')
                if machine_id:
                    print(f"[webhook/stripe] machine_id found in line_item: {machine_id}")
                    break
        if not machine_id:
            # 2. Try parent.subscription_details.metadata
            parent = data_object.get('parent', {})
            sub_details = parent.get('subscription_details', {}) if parent else {}
            machine_id = sub_details.get('metadata', {}).get('machine_id')
            if machine_id:
                print(f"[webhook/stripe] machine_id found in parent.subscription_details: {machine_id}")
        if not machine_id:
            # 3. (if available) Fallback to classic way: fetch subscription if there's a subscription id
            subscription_id = data_object.get('subscription')
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                machine_id = subscription.get('metadata', {}).get('machine_id')
                if machine_id:
                    print(f"[webhook/stripe] machine_id found from subscription fetch: {machine_id}")
        if not machine_id:
            print(f"[webhook/stripe] invoice.payment_succeeded still missing machine_id. Event ID: {event['id']}")
            return {"ok": True}
        account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
        print(f"[webhook/stripe] Queried MachineAccount: {account}")
        if not account:
            print(f"[webhook/stripe] No account found for machine_id {machine_id}")
            return {"ok": True}
        print(f"[webhook/stripe] Account tier before update: {account.tier}")
        account.tier = UserTier.demo
        reset_all_quotas(account, db)
        db.commit()
        db.refresh(account)
        print(f"[webhook/stripe] Account tier after update: {account.tier}")
        return {"ok": True}

    print(f"[webhook/stripe] Ignoring event type: {event_type}")
    return {"ok": True}

