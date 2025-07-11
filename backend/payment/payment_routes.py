from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os
import smtplib
from email.message import EmailMessage
from tiers.tiers_routes import set_user_pro
from sqlalchemy.orm import Session
from backend.rate_limiter.rate_limiter_models import MachineAccount, UserTier
from backend.rate_limiter.rate_limiter_services import reset_all_quotas




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
    data = await request.json()
    uuid = data.get("uuid")
    if not uuid:
        return JSONResponse({"error": "Missing uuid"}, status_code=400)

    try:
        # Optionally, add metadata for later lookup (license activation, etc.)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'LexBot PRO Subscription',
                    },
                    'unit_amount': 1900,
                    'recurring': {'interval': 'month'}
                },
                'quantity': 1,
            }],
            mode='subscription',
            metadata={'uuid': uuid},
            success_url='https://yourapp.com/payment-success',
            cancel_url='https://yourapp.com/payment-cancel',
        )
        return {"url": session.url}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        uuid = session["metadata"]["uuid"]
        email = session.get("customer_email")
        db = get_db()
        set_user_pro(db, uuid, email)
        if email:
            send_license_email(email, uuid)
    return "ok", 200

@router.get("/license-status")
def license_status(uuid: str):
    # Look up uuid in your database
    if is_licensed(uuid):
        return {"status": "active"}
    return {"status": "inactive"}

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