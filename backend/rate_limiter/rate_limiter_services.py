from datetime import datetime, timedelta
from rate_limiter.rate_limiter_models import MachineAccount, UsageStats, UserTier
from rate_limiter.rate_limiter_config import TIER_LIMITS

def get_or_create_machine_account(db, machine_id: str) -> MachineAccount:
    account = db.query(MachineAccount).filter_by(machine_id=machine_id).first()
    if not account:
        account = MachineAccount(machine_id=machine_id, tier=UserTier.demo)
        db.add(account)
        db.commit()
        db.refresh(account)
        for feature, limit in TIER_LIMITS["demo"].items():
            usage = UsageStats(
                machine_id=machine_id,
                feature_name=feature,
                used=0,
                limit=limit,
                reset_at=datetime.utcnow()
            )
            db.add(usage)
        db.commit()
    return account

def get_usage(db, machine_id: str, feature: str) -> UsageStats:
    return db.query(UsageStats).filter_by(machine_id=machine_id, feature_name=feature).first()

def check_and_increment_usage(db, machine_id: str, tier: str, feature: str):
    usage = get_usage(db, machine_id, feature)
    if not usage:
        from rate_limiter.rate_limiter_config import TIER_LIMITS
        usage = UsageStats(
            machine_id=machine_id,
            feature_name=feature,
            used=0,
            limit=TIER_LIMITS[tier][feature],
            reset_at=datetime.utcnow()
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    if usage.reset_at < datetime.utcnow() - timedelta(days=1):
        usage.used = 0
        usage.reset_at = datetime.utcnow()
        from rate_limiter.rate_limiter_config import TIER_LIMITS
        usage.limit = TIER_LIMITS[tier][feature]
        db.commit()
    if usage.used >= usage.limit:
        return False
    usage.used += 1
    db.commit()
    return True

def reset_all_quotas(account: MachineAccount, db):
    from rate_limiter.rate_limiter_config import TIER_LIMITS
    for feature, limit in TIER_LIMITS[account.tier.value].items():
        usage = get_usage(db, account.machine_id, feature)
        if usage:
            usage.used = 0
            usage.limit = limit
            usage.reset_at = datetime.utcnow()
        else:
            usage = UsageStats(
                machine_id=account.machine_id,
                feature_name=feature,
                used=0,
                limit=limit,
                reset_at=datetime.utcnow()
            )
            db.add(usage)
    db.commit()