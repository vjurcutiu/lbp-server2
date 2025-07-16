from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, func, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from database import Base


class UserTier(enum.Enum):
    demo = "demo"
    pro = "pro"
    trial = "trial"
    banned = "banned"

class MachineAccount(Base):
    __tablename__ = "machine_accounts"
    id = Column(Integer, primary_key=True)
    machine_id = Column(String, unique=True, index=True, nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.demo, nullable=False)
    created_at = Column(DateTime, default=func.now())
    upgraded_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    email = Column(String, nullable=True)
    usage = relationship("UsageStats", back_populates="account")    
    subscription = relationship("UserSubscription", back_populates="machine_account", uselist=False)


class UsageStats(Base):
    __tablename__ = "usage_stats"
    id = Column(Integer, primary_key=True)
    machine_id = Column(String, ForeignKey("machine_accounts.machine_id"), index=True)
    feature_name = Column(String)
    used = Column(Integer, default=0)
    limit = Column(Integer, default=0)
    reset_at = Column(DateTime, default=func.now())
    account = relationship("MachineAccount", back_populates="usage")
    __table_args__ = (UniqueConstraint('machine_id', 'feature_name', name='_machine_feature_uc'),)