# Quick Check: Ozon Mock Sync

## 1. Setup
```bash
docker compose up -d db redis
alembic upgrade head
export OZON_PERF_MOCK=1
```

## 2. Create Ozon Connection & Experiment
(Assuming you have advertiser_id=1)
```bash
# Create Connection
curl -X POST "http://localhost:8000/api/connections/" \
     -H "Content-Type: application/json" \
     -d '{"platform": "ozon", "name": "Ozon Mock", "credentials_json": {"client_id": "1", "client_secret": "2"}}'

# Create Plan (use connection_id from above, e.g. 1)
curl -X POST "http://localhost:8000/api/plans/" ...

# Create Experiment
curl -X POST "http://localhost:8000/api/experiments/" ...
```

## 3. Run Sync
```bash
curl -X POST "http://localhost:8000/api/experiments/{id}/sync" \
     -H "Content-Type: application/json" \
     -d '{"platform": "ozon", "run_type": "full", "date_from": "2023-01-01", "date_to": "2023-01-05"}'
```

## 4. Check Results
```bash
curl "http://localhost:8000/api/experiments/{id}/summary?platform=ozon&date_from=2023-01-01&date_to=2023-01-05"
```
Expect non-zero impressions/clicks.
