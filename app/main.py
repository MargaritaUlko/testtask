from datetime import datetime
import logging
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

if not TRONGRID_API_KEY:
    raise ValueError("TRONGRID_API_KEY нет в .env файле")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)


TRONGRID_API_URL = "https://api.trongrid.io"

@app.post("/wallet/")
async def get_wallet_info(address: str, db: AsyncSession = Depends(get_db)):
    try:
        
        if not address.startswith("T"):
            raise HTTPException(status_code=400, detail="Некорректный формат адреса")

        
        url = f"{TRONGRID_API_URL}/v1/accounts/{address}"
        headers = {
            "Content-Type": "application/json",
            "TRON-PRO-API-KEY": TRONGRID_API_KEY
        }
        logger.info(f"Запрос к TronGrid API: {url}")

        response = session.get(url, headers=headers)
        logger.info(f"Ответ от TronGrid API: {response.status_code}, {response.text}")

        response.raise_for_status()  
        account_data = response.json()

        if not account_data.get("data") or not account_data["data"]:
            raise HTTPException(status_code=404, detail="Address not found")

        account = account_data["data"][0]
        trx_balance_sun = account.get("balance", 0)
        trx_balance_trx = trx_balance_sun / 1_000_000  

  
        bandwidth = 0
        energy = 0
        try:
            url = f"{TRONGRID_API_URL}/v1/accounts/{address}/resources"
            logger.info(f"Запрос к TronGrid API: {url}")

            response = session.get(url, headers=headers)
            logger.info(f"Ответ от TronGrid API: {response.status_code}, {response.text}")

            response.raise_for_status()
            account_resource = response.json()
            bandwidth = account_resource.get("freeNetLimit", 0)
            energy = account_resource.get("EnergyLimit", 0)
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Ресурсы недоступны для адреса {address}: {e}")

      
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
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ошибка при запросе к TronGrid API: {e}")
        logger.error(f"Статус код: {e.response.status_code}")
        logger.error(f"Тело ответа: {e.response.text}")
        raise HTTPException(status_code=500, detail="Ошибка при запросе к TronGrid API")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        raise HTTPException(status_code=500, detail="Неизвестная ошибка")
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