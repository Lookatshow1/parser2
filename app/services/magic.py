from sqlalchemy.orm import Session
from app.db.models_magic import MagicRun
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
# Use absolute imports or ensure these exist. I assume models_magic was created earlier.
from app.core.ai.interfaces import TextProvider
from app.core.ai.mock_provider import MockTextProvider
import logging

logger = logging.getLogger(__name__)

class MagicService:
    def __init__(self, db: Session, ai_provider: TextProvider = None):
        self.db = db
        self.ai = ai_provider or MockTextProvider()

    async def create_magic_run(self, org_id: int, user_id: int, input_data: dict) -> MagicRun:
        run = MagicRun(
            organization_id=org_id,
            created_by_user_id=user_id,
            status="pending",
            input_json=input_data
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    async def process_run(self, run_id: int):
        """
        Execute the AI generation pipeline.
        This should be called by a background worker (Celery), but we simulate it here or await it for now.
        """
        run = self.db.query(MagicRun).filter(MagicRun.id == run_id).first()
        if not run:
            return
        
        run.status = "running"
        self.db.commit()
        
        try:
            # TODO: Construct a real prompt based on input inputs (URL, description)
            prompt = f"Create an ad campaign for {run.input_json.get('landing_url', 'unknown')}. Target audience: {run.input_json.get('target_audience', 'general')}."
            
            # Call AI (Mock)
            result = await self.ai.generate_text(
                prompt, 
                json_schema={"type": "object"} # Schema validation to be added
            )
            
            # Store Result
            if isinstance(result, dict):
                run.result_json = result
            else:
                run.result_json = {"raw_text": result}
            
            run.status = "success"
            
            # Create Draft Entities
            self._create_drafts(run)
            
        except Exception as e:
            logger.exception("Magic Run Failed")
            run.error = str(e)
            run.status = "failed"
        
        self.db.commit()

    def _create_drafts(self, run: MagicRun):
        """
        Parses the AI output and creates DraftCampaign, DraftAdGroup, DraftAd.
        """
        data = run.result_json
        if not data or "ad_groups" not in data:
            # Fallback or simple one-group creation
            campaign = DraftCampaign(
                organization_id=run.organization_id,
                connection_id=run.input_json.get("connection_id"),
                magic_run_id=run.id,
                platform=run.input_json.get("platform", "yandex"),
                name=data.get("campaign_name", "Magic Campaign"),
                status="draft",
                payload_json=data
            )
            self.db.add(campaign)
            return

        # Detailed creation
        campaign = DraftCampaign(
            organization_id=run.organization_id,
            connection_id=run.input_json.get("connection_id"),
            magic_run_id=run.id,
            platform=run.input_json.get("platform", "yandex"),
            name=data.get("campaign_name", "Magic Campaign"),
            status="draft",
            payload_json={"budget": data.get("budget")}
        )
        self.db.add(campaign)
        self.db.flush() # get ID

        for group_data in data.get("ad_groups", []):
            group = DraftAdGroup(
                campaign_id=campaign.id,
                name=group_data.get("name", "New Ad Group"),
                payload_json={"keywords": group_data.get("keywords")}
            )
            self.db.add(group)
            self.db.flush()

            for ad_data in group_data.get("ads", []):
                ad = DraftAd(
                    ad_group_id=group.id,
                    title=ad_data.get("title"),
                    text=ad_data.get("text"),
                    landing_url=run.input_json.get("landing_url"),
                    payload_json={}
                )
                self.db.add(ad)
