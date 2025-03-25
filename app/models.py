from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, Float, Integer, Numeric, String, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from pytz import timezone

KRASNOYARSK_TZ = timezone('Asia/Krasnoyarsk')

Base = declarative_base()


KRASNOYARSK_TZ = timezone('Asia/Krasnoyarsk')

Base = declarative_base()

class WalletRequest(Base):
    __tablename__ = "wallet_requests"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    trx_balance = Column(Numeric(12, 6)) 
    bandwidth = Column(Integer)
    energy = Column(Integer)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Krasnoyarsk'")  
    )