from sqlalchemy import create_engine, text
import os

# Get DB URL from env or use default (matching docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/ads")


def cleanup():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Dropping new tables if they exist...")
        # Order matters due to foreign keys
        tables = [
            "billing_transactions",
            "billing_documents",
            "billing_accounts",
            "draft_ads",
            "draft_ad_groups",
            "draft_campaigns",
            "magic_runs"
        ]
        
        for table in tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        conn.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
