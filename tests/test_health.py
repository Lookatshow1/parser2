import pytest

from app.main import app
from httpx import AsyncClient


@pytest.mark.anyio
async def test_api_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
