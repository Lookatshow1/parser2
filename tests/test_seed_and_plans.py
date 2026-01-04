import pytest

from app.main import app
from httpx import AsyncClient


@pytest.mark.anyio
async def test_seed_and_list_plans():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # call seed (dev mode expected)
        seed_resp = await client.post("/api/dev/seed")
        assert seed_resp.status_code in (200, 201)
        seed_data = seed_resp.json()
        assert "plan_id" in seed_data

        # list plans
        plans_resp = await client.get("/api/plans")
        assert plans_resp.status_code == 200
        plans_data = plans_resp.json()
        assert isinstance(plans_data, dict)
        items = plans_data.get("items")
        assert isinstance(items, list)
        assert len(items) >= 1
