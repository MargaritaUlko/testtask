
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import WalletRequest


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