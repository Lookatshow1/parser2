# Quick Check: Dashboard API

## 1. Setup
```bash
docker compose up -d db redis
alembic upgrade head
```

## 2. Create Data (Python shell or curl)
Assuming you have an experiment ID=1.

## 3. Check Campaigns
```bash
curl -s "http://localhost:8000/api/experiments/1/campaigns" | python3 -m json.tool
```
Expect: `{"items": [{"campaign_external_id": "...", "platform": "yandex"}], "total": N}`

## 4. Check Metrics (Daily)
```bash
curl -s "http://localhost:8000/api/experiments/1/metrics?date_from=2023-01-01&date_to=2023-01-10&group_by=day" | python3 -m json.tool
```
Expect list of items with date, impressions, clicks, ctr, etc.

## 5. Check Summary
```bash
curl -s "http://localhost:8000/api/experiments/1/summary?date_from=2023-01-01&date_to=2023-01-10" | python3 -m json.tool
```
Expect single object with totals and averages (ctr, cpc, cpm).
