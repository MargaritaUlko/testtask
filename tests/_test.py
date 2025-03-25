import select
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import app
from app.db_helper import AsyncSessionLocal

from unittest.mock import AsyncMock, patch
import requests
from datetime import datetime

from app.main import WalletRequest

client = TestClient(app)

@pytest.fixture
async def async_db_session():

    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_wallet_endpoint_integration(async_db_session):
    mock_response = {
        "data": [{
            "balance": 1_000_000,
            "freeNetLimit": 5000,
            "EnergyLimit": 1000
        }]
    }
    
    with patch.object(requests.Session, 'get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        response = client.post("/wallet/", json={"address": "TF5Bn4qJKMWeQJShR6D1WpAxh53m5BMp6d"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["trx_balance"] == 1.0
        assert data["bandwidth"] == 5000
        assert data["energy"] == 1000

        await async_db_session.commit()
        result = await async_db_session.execute(select(WalletRequest))
        db_entry = result.scalars().first()
        assert db_entry.address == "TF5Bn4qJKMWeQJShR6D1WpAxh53m5BMp6d"



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