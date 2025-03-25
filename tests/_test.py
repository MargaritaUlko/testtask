import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from sqlalchemy.ext.asyncio import AsyncSession

from app.db_helper import AsyncSessionLocal
from app.models import WalletRequest

from app.main import app  

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()
            await session.close()

@pytest.mark.asyncio
async def test_wallet_request_db(db_session: AsyncSession):
    address = "TP7FUePBVYT76VoPiw3NnkmruetDYKaYeg"
    wallet_request = WalletRequest(
        address=address,
        trx_balance=1442,
        bandwidth=600,
        energy=0,
    )

    db_session.add(wallet_request)
    await db_session.commit()
    await db_session.refresh(wallet_request)

    assert wallet_request.id is not None
    assert wallet_request.address == address





    
@pytest.mark.asyncio
async def test_get_wallet_requests(client):
    address = "TP7FUePBVYT76VoPiw3NnkmruetDYKaYeg"
    
    response = client.get("/wallets/?skip=0&limit=10")
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert isinstance(response_data, list)
    assert len(response_data) <= 10
