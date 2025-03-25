from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from tronpy import Tron
from tronpy.exceptions import AddressNotFound
from app.db_helper import get_db
from app.models import KRASNOYARSK_TZ, WalletRequest
from tronpy.providers import HTTPProvider
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


app = FastAPI()

load_dotenv()

TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
class TronGridAdapter(HTTPAdapter):
    def add_headers(self, request, **kwargs):
        request.headers["TRON-PRO-API-KEY"] = TRONGRID_API_KEY

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

session = requests.Session()
session.mount("https://", TronGridAdapter(max_retries=retry_strategy))

provider = HTTPProvider(endpoint_uri="https://api.trongrid.io") 
client = Tron(network="mainnet", provider=provider)


@app.post("/wallet/")
async def get_wallet_info(address: str, db: AsyncSession = Depends(get_db)):
    try:
        account = client.get_account(address)
        trx_balance_sun = account.get("balance", 0)
        trx_balance_trx = trx_balance_sun / 1_000_000         
        account_resource = client.get_account_resource(address)
        bandwidth = account_resource.get("freeNetLimit", 0)
        energy = account_resource.get("EnergyLimit", 0)
        
        wallet_request = WalletRequest(
            address=address,
            trx_balance=trx_balance_trx,
            bandwidth=bandwidth,
            energy=energy,
            created_at=datetime.now(KRASNOYARSK_TZ) 
        )

        db.add(wallet_request)
        await db.commit()
        await db.refresh(wallet_request)
        
        return {
            "address": address,
            "trx_balance": round(trx_balance_trx, 6),  
            "bandwidth": bandwidth,
            "energy": energy
        }
    except AddressNotFound:
        raise HTTPException(status_code=404, detail="Address not found")
    
@app.get("/wallets/")
async def get_wallet_requests(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WalletRequest).order_by(WalletRequest.created_at.desc()).offset(skip).limit(limit)
    )
    wallet_requests = result.scalars().all()
    
    for wallet_request in wallet_requests:
        if wallet_request.created_at is not None:
            wallet_request.created_at = wallet_request.created_at.astimezone(KRASNOYARSK_TZ)
    
    return wallet_requests

