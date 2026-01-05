# Quick Check: Sync Jobs

## 1. Setup
```bash
docker compose up -d db redis
alembic upgrade head
export YANDEX_DIRECT_MOCK=1
```

## 2. Start Worker (in separate terminal)
```bash
# Assuming you are in root
celery -A app.workers.celery_app worker --loglevel=info
```

## 3. Create Sync Run
```bash
curl -X POST "http://localhost:8000/api/experiments/1/sync" \
     -H "Content-Type: application/json" \
     -d '{
           "platform": "yandex",
           "run_type": "full",
           "date_from": "2023-01-01",
           "date_to": "2023-01-05"
         }'
```
Response: `{"id": 1, "status": "queued", ...}`

## 4. Check Status
```bash
curl "http://localhost:8000/api/sync-runs/1"
```
Wait a few seconds. Status should become `success`.

## 5. Check History
```bash
curl "http://localhost:8000/api/experiments/1/sync-runs?platform=yandex"
```
