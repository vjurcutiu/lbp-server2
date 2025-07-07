from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

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
    email = Column(String, nullable=True)  # If you ever want to bind to email/user

    def __repr__(self):
        return f"<MachineAccount(machine_id={self.machine_id}, tier={self.tier})>"
