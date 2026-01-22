import sys
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.getcwd())

from app.db.base import Base
from app.db.models import Organization
from app.db.models_context import BusinessContext
from app.services.website_parser import WebsiteParserService
from app.services.magic import MagicService
from app.core.config import get_settings
from app.core.ai.mock_provider import MockTextProvider, MockImageProvider

# Setup DB
settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Ensure tables context exist (since we added new model file and might not have migrated)
# In dev we might use alembic, here we force create for verification if not exists
try:
    BusinessContext.__table__.create(engine)
except Exception:
    pass # Expected if already exists or handled by alembic

async def main():
    print("--- Starting Parser Verification ---")
    
    # 1. Setup Data
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Test Org Parser")
        db.add(org)
        db.commit()

    # 2. Test Parser
    parser = WebsiteParserService(db)
    url = "https://example.com" 
    print(f"\n[Test] Parsing {url}...")
    
    # We use example.com which is simple
    ctx = await parser.parse_and_save(url, org.id)
    
    print(f"Context Created: ID {ctx.id}")
    print(f"Status: {ctx.status}")
    print(f"Title: {ctx.meta_title}")
    print(f"Text Preview: {ctx.clean_text[:50]}...")
    
    if ctx.status == "success" and "Example Domain" in ctx.clean_text:
        print("PASS: Parsing successful")
    else:
        print(f"FAIL: Parsing failed or unexpected content (status={ctx.status})")

    # 3. Test Magic Generation from Context
    print("\n[Test] Magic Generation from Context...")
    # Use mocks to avoid API costs
    magic = MagicService(db, text_provider=MockTextProvider(), image_provider=MockImageProvider())
    
    result = await magic.generate_from_context(ctx.id, input_text="Create summer sale ads")
    
    ads_count = len(result.get("ads", []))
    print(f"Generated {ads_count} ads")
    print(f"Business Name: {result.get('business_name')}")
    
    if ads_count > 0:
        print("PASS: Generation successful")
    else:
        print("FAIL: No ads generated")

if __name__ == "__main__":
    asyncio.run(main())
