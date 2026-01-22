import sys
import os
import asyncio
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.getcwd())

from app.db.base import Base
from app.db.models import (
    Organization, Connection, Platform, CampaignPlan, Experiment, 
    ExperimentStatus, ConnectionStatus, OrgAutomationAction, AdCampaign
)
from app.services.experiment_service import ExperimentService
from app.services.automation_execution_service import execute_action
from app.core.config import get_settings

# Setup DB
settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def main():
    print("--- Starting Verification ---")
    
    # 1. Setup Data
    org = db.query(Organization).first()
    if not org:
        print("Creating default org...")
        org = Organization(name="Test Org")
        db.add(org)
        db.commit()

    # Create VK Connection (Mock)
    conn_vk = db.query(Connection).filter_by(platform=Platform.vk).first()
    if not conn_vk:
        conn_vk = Connection(
            organization_id=org.id,
            platform=Platform.vk,
            status=ConnectionStatus.active,
            credentials_json={"mock": True}
        )
        db.add(conn_vk)
        db.commit()
    
    # Set Mock ENV
    os.environ["VK_ADS_MOCK"] = "1"
    os.environ["YANDEX_DIRECT_MOCK"] = "1"

    # 2. Test Campaign Creation (Experiment)
    print("\n[Test] Experiment Campaign Creation")
    # Plan
    plan = CampaignPlan(
        organization_id=org.id,
        advertiser_id=1, # Hack: assume advertiser 1 exists or fails
        name="Mega Plan",
        platform=Platform.vk,
        status="draft"
    )
    # We need advertiser?
    from app.db.models import Advertiser
    adv = db.query(Advertiser).first()
    if not adv:
        adv = Advertiser(name="Test Adv")
        db.add(adv)
        db.commit()
    plan.advertiser_id = adv.id
    db.add(plan)
    db.commit()

    service = ExperimentService()
    exp = service.create_experiment(
        db,
        plan_id=plan.id,
        total_budget=10000,
        platforms=["vk"]
    )
    # Start (creates round 1 and Should create campaign)
    # Need to make sure platforms includes 'vk' and connector is active.
    # We set platforms=['vk'] above.
    
    exp = service.start_experiment(db, exp.id)
    print(f"Experiment started: ID {exp.id}")

    # Check mapping
    from app.db.models import ExperimentCampaign
    exp_camp = db.query(ExperimentCampaign).filter_by(experiment_id=exp.id).first()
    if exp_camp:
        print(f"PASS: ExperimentCampaign created with ID {exp_camp.campaign_external_id}")
    else:
        print(f"FAIL: ExperimentCampaign not found for exp {exp.id}")
    
    # 3. Test Automation Execution
    print("\n[Test] Automation Execution")
    
    # Create valid AdCampaign linked to the interaction
    # (Since our Experiment creation creates ExperimentCampaign but not AdCampaign in catalog yet - catalog sync is separate)
    # But Automation works on AdCampaign (Catalog).
    # ensure we have an AdCampaign
    ad_campaign = AdCampaign(
        organization_id=org.id,
        connection_id=conn_vk.id,
        platform=Platform.vk,
        external_id="vk_stub_999", # Matches the mock ID from connector
        name="Test Campaign for Automation"
    )
    try:
        db.add(ad_campaign)
        db.commit()
    except:
        db.rollback()
        ad_campaign = db.query(AdCampaign).filter_by(external_id="vk_stub_999").first()

    # Create Action
    action = OrgAutomationAction(
        organization_id=org.id,
        title="Stop Campaign",
        description="Auto stop",
        action_type="stop_campaign",
        status="draft",
        payload_json={
            "recommendation_code": "NO_CONVERSIONS_SPEND", 
            "subject_type": "campaign", 
            "subject_id": ad_campaign.id
        }
    )
    db.add(action)
    db.commit()

    # Execute
    print(f"Executing action {action.id}...")
    execute_action(db, action.id)
    
    db.refresh(action)
    db.refresh(ad_campaign)
    
    print(f"Action Status: {action.status}")
    print(f"Campaign Desired Status: {ad_campaign.desired_status}")

    if action.status == "executed" and ad_campaign.desired_status == "stopped":
        print("PASS: Automation execution successful")
    else:
        print("FAIL: Automation execution failed")

if __name__ == "__main__":
    main()
