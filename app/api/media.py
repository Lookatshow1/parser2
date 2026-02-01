import shutil
import os
import uuid
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.staticfiles import StaticFiles

from app.api.deps import get_current_user
from app.db.models import User

# In a real app this would go to S3/MinIO
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

media_router = APIRouter(prefix="/media", tags=["media"])

@media_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    try:
        # Generate safe filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "png"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return URL (assuming static file serving is set up)
        return {"url": f"/static/uploads/{filename}", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
