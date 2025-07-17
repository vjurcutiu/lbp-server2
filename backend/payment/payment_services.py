import stripe
from datetime import datetime
from payment.payment_models import UserSubscription, SubscriptionStatus
from rate_limiter.rate_limiter_models import MachineAccount, UserTier
from sqlalchemy.orm import Session
import json
import pprint

def get_subscription_status(machine_id, db: Session):
    account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
    subscription = db.query(UserSubscription).filter_by(machine_id=machine_id).first()

    renewal_date = None
    if subscription and subscription.current_period_end:
        renewal_date = subscription.current_period_end.isoformat()
    elif subscription and subscription.cancel_at_period_end:
        print("WARNING: cancel_at_period_end is True but no current_period_end is set in DB!")

    result = {
        "machine_id": machine_id,
        "tier": account.tier.value if account else None,
        "subscription": {
            "status": subscription.status.value if subscription else None,
            "renewal_date": renewal_date,
            "cancel_at_period_end": subscription.cancel_at_period_end if subscription else None,
            "stripe_subscription_id": subscription.stripe_subscription_id if subscription else None,
        }
    }
    print("=== get_subscription_status API RESPONSE ===")
    print(json.dumps(result, indent=2, default=str))  # default=str handles dates
    return result

def cancel_subscription(machine_id, db: Session):
    subscription = db.query(UserSubscription).filter_by(machine_id=machine_id).first()
    if not subscription or not subscription.stripe_subscription_id:
        return False, "No subscription found"
    # Call Stripe to set cancel at period end
    sub = stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        cancel_at_period_end=True
    )

    # Only update our own internal intent flag - let the webhook update all other fields
    subscription.cancel_at_period_end = True
    db.commit()
    return True, "Subscription set to cancel at period end"

def update_subscription_from_stripe(event, db: Session):
    """
    Called from your webhook handler with the parsed event.
    Only processes customer.subscription.* events!
    """
    data = event['data']['object']
    machine_id = data.get('metadata', {}).get('machine_id')
    sub_id = data.get('id')
    customer_id = data.get('customer')

    # Defensive: try all sources for current_period_end
    current_period_end = data.get('current_period_end')
    if not current_period_end:
        items = data.get("items", {}).get("data", [])
        if items and items[0].get("current_period_end"):
            current_period_end = items[0]["current_period_end"]

    current_period_end_dt = datetime.utcfromtimestamp(current_period_end) if current_period_end else None
    cancel_at_period_end = data.get('cancel_at_period_end', False)
    status = data.get('status', 'incomplete')

    try:
        status_enum = SubscriptionStatus(status)
    except ValueError:
        status_enum = SubscriptionStatus.incomplete

    sub = db.query(UserSubscription).filter_by(machine_id=machine_id).first()
    if not sub:
        sub = UserSubscription(
            machine_id=machine_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=sub_id,
            status=status_enum,
            current_period_end=current_period_end_dt,
            cancel_at_period_end=cancel_at_period_end
        )
        db.add(sub)
    else:
        sub.stripe_customer_id = customer_id
        sub.stripe_subscription_id = sub_id
        sub.status = status_enum
        # Only update current_period_end if present (don't overwrite good value with None)
        if current_period_end_dt:
            sub.current_period_end = current_period_end_dt
        sub.cancel_at_period_end = cancel_at_period_end

    # Also update MachineAccount tier for convenience
    account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
    if account:
        if status == "active":
            account.tier = UserTier.pro
        else:
            account.tier = UserTier.demo
    db.commit()

def update_subscription_from_invoice(event, db: Session):
    print("[DEBUG] Entered update_subscription_from_invoice")
    data = event['data']['object']
    subscription_id = data.get("subscription")
    if not subscription_id:
        # Try alternate paths
        # 1. Inside parent.subscription_details.subscription
        parent = data.get("parent", {})
        if parent and "subscription_details" in parent:
            subscription_id = parent["subscription_details"].get("subscription")
            print(f"[DEBUG] Found subscription_id in parent.subscription_details: {subscription_id}")
        # 2. Inside lines.data[0].parent.subscription_item_details.subscription
        if not subscription_id:
            lines = data.get("lines", {}).get("data", [])
            for item in lines:
                subscription_item_details = item.get("parent", {}).get("subscription_item_details", {})
                subscription_id = subscription_item_details.get("subscription")
                if subscription_id:
                    print(f"[DEBUG] Found subscription_id in lines: {subscription_id}")
                    break

    if not subscription_id:
        print("[DEBUG] No subscription_id found in invoice!")
        return

    print(f"[DEBUG] subscription_id from invoice: {subscription_id}")

    # Fetch subscription object from Stripe API
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    print(f"[DEBUG] stripe_subscription: {stripe_subscription}")
    machine_id = stripe_subscription.get('metadata', {}).get('machine_id')
    customer_id = stripe_subscription.get('customer')
    current_period_end = stripe_subscription.get("current_period_end")
    if not current_period_end:
        items = stripe_subscription.get("items", {}).get("data", [])
        if items and items[0].get("current_period_end"):
            current_period_end = items[0]["current_period_end"]
            print(f"[DEBUG] Fallback current_period_end from item: {current_period_end}")

    # Final conversion to datetime
    current_period_end_dt = datetime.utcfromtimestamp(current_period_end) if current_period_end else None
    print(f"[DEBUG] current_period_end (datetime): {current_period_end_dt}")

    cancel_at_period_end = stripe_subscription.get('cancel_at_period_end', False)
    status = stripe_subscription.get('status', 'incomplete')

    try:
        status_enum = SubscriptionStatus(status)
    except ValueError:
        status_enum = SubscriptionStatus.incomplete

    sub = db.query(UserSubscription).filter_by(machine_id=machine_id).first()
    if not sub:
        sub = UserSubscription(
            machine_id=machine_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            status=status_enum,
            current_period_end=current_period_end_dt,
            cancel_at_period_end=cancel_at_period_end
        )
        db.add(sub)
    else:
        sub.stripe_customer_id = customer_id
        sub.stripe_subscription_id = subscription_id
        sub.status = status_enum
        # Only update current_period_end if present (don't overwrite good value with None)
        if current_period_end_dt:
            sub.current_period_end = current_period_end_dt
        sub.cancel_at_period_end = cancel_at_period_end

    # Also update MachineAccount tier for convenience
    account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
    if account:
        if status == "active":
            account.tier = UserTier.pro
        else:
            account.tier = UserTier.demo
    db.commit()

def reactivate_subscription(machine_id, db: Session):
    subscription = db.query(UserSubscription).filter_by(machine_id=machine_id).first()
    if not subscription or not subscription.stripe_subscription_id:
        return False, "No subscription found"
    sub = stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        cancel_at_period_end=False
    )
    subscription.cancel_at_period_end = False
    db.commit()
    return True, "Subscription reactivated"
