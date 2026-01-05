from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Connection
from app.api.schemas import ConnectionCreateRequest, ConnectionOut, ConnectionListResponse

router = APIRouter(prefix="/connections", tags=["connections"])

@router.post("/", response_model=ConnectionOut)
def create_connection(item: ConnectionCreateRequest, db: Session = Depends(get_db)):
    db_obj = Connection(
        advertiser_id=item.advertiser_id,
        platform=item.platform,
        name=item.name,
        credentials_json=item.credentials_json
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=ConnectionListResponse)
def list_connections(db: Session = Depends(get_db)):
    items = db.query(Connection).all()
    return {"items": items}

@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(connection_id: int, db: Session = Depends(get_db)):
    conn = db.query(Connection).get(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn
