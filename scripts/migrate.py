import sys
import os
sys.path.append(os.getcwd())

from app.db.base import Base
from app.core.config import get_settings
from sqlalchemy import create_engine

# Import all models to ensure they are registered in Base
from app.db import models
from app.db import models_context
from app.db import models_magic
from app.db import models_billing
from app.db import models_analytics
from app.db import models_drafts
from app.db import models_optimizer
from app.db import models_abtests

def migrate():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    migrate()
