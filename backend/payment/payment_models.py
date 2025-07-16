from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import enum

class SubscriptionStatus(enum.Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    unpaid = "unpaid"
    incomplete = "incomplete"
    trialing = "trialing"

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True)
    machine_id = Column(String, ForeignKey("machine_accounts.machine_id"), unique=True, nullable=False)
    # The above ensures a 1:1 relationship between subscription and machine account
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.incomplete)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    machine_account = relationship("MachineAccount", back_populates="subscription", uselist=False)
