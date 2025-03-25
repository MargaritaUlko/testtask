
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_helper import create_async_engine
from app.main import WalletRequest
from app.models import Base

@pytest.fixture(scope="session")
def test_db_url():
    return "postgresql+asyncpg://postgres:123@localhost:5432/testtask"

@pytest.fixture(scope="session")
async def async_engine(test_db_url):
    engine = create_async_engine(test_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def async_db_session(async_engine):
    async with AsyncSession(async_engine) as session:
        yield session
@pytest.mark.asyncio
async def test_db_write_unit():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_commit = AsyncMock()
    mock_refresh = AsyncMock()
    
    mock_session.commit = mock_commit
    mock_session.refresh = mock_refresh

    test_data = {
        "address": "TEST_ADDRESS",
        "trx_balance": 1.23,
        "bandwidth": 100,
        "energy": 200,
        "created_at": datetime.now()
    }

    wallet_request = WalletRequest(**test_data)
    mock_session.add(wallet_request)
    await mock_session.commit()
    await mock_session.refresh(wallet_request)

    mock_session.add.assert_called_once()
    mock_commit.assert_awaited_once()
    mock_refresh.assert_awaited_once_with(wallet_request)