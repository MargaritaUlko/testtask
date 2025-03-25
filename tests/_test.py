import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_helper import AsyncSessionLocal
from app.models import WalletRequest


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


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
    """Проверка добавления кошелька в БД"""
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
async def test_get_wallet_requests(client: AsyncClient, db_session: AsyncSession):
    """Проверка получения списка кошельков"""
    address = "TP7FUePBVYT76VoPiw3NnkmruetDYKaYeg"

    # Добавляем тестовые данные
    wallet_request = WalletRequest(
        address=address,
        trx_balance=1000,
        bandwidth=500,
        energy=200,
    )
    db_session.add(wallet_request)
    await db_session.commit()

    response = await client.get("/wallets/?skip=0&limit=10")

    assert response.status_code == 200
    response_data = response.json()

    assert isinstance(response_data, list)
    assert any(wallet["address"] == address for wallet in response_data)
