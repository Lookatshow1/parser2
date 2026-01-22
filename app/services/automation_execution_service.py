from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import (
    OrgAutomationAction,
    AdCampaign,
    Connection,
    OrgRecommendation,
)
from app.services.connector_service import get_connector
from app.services.audit import log_org_event

def execute_action(db: Session, action_id: int, user_id: int | None = None) -> OrgAutomationAction:
    """
    Executes an automation action.
    Currently supports stopping campaigns for 'NO_CONVERSIONS_SPEND' recommendations.
    """
    action = db.get(OrgAutomationAction, action_id)
    if not action:
        raise ValueError(f"Action {action_id} not found")

    if action.status != "draft":
        # Already executed or failed
        return action

    # 1. Parse Payload
    # payload_json pattern: {"recommendation_code": "NO_CONVERSIONS_SPEND", "subject_type": "campaign", "subject_id": 123}
    payload = action.payload_json or {}
    code = payload.get("recommendation_code")
    subject_type = payload.get("subject_type")
    subject_id = payload.get("subject_id")

    try:
        if code == "NO_CONVERSIONS_SPEND" and subject_type == "campaign":
            # Action: Stop Campaign
            _execute_stop_campaign(db, action, subject_id)
        else:
            # Not supported for auto-execution yet
            action.status = "skipped"
            action.description += "\n[System] Auto-execution not supported for this rule."
    
    except Exception as e:
        action.status = "failed"
        action.description += f"\n[System] Execution failed: {str(e)}"
        log_org_event(
            db, 
            organization_id=action.organization_id,
            actor_user_id=user_id,
            action="automation_action_failed",
            subject_type="automation_action",
            subject_id=action.id,
            meta={"error": str(e)}
        )
        db.commit() # Save failure state
        raise e

    action.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(action)
    
    if action.status == "executed":
        log_org_event(
            db,
            organization_id=action.organization_id,
            actor_user_id=user_id,
            action="automation_action_executed",
            subject_type="automation_action",
            subject_id=action.id,
            meta={"code": code}
        )

    return action

def _execute_stop_campaign(db: Session, action: OrgAutomationAction, campaign_id: int):
    # 1. Load Campaign
    campaign = db.get(AdCampaign, campaign_id)
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    # 2. Start Execution
    action.status = "running"
    db.commit()

    # 3. Load Connection
    connection = db.get(Connection, campaign.connection_id)
    if not connection:
         raise ValueError("Connection not found")

    # 4. Call Connector
    connector = get_connector(connection.platform, connection.credentials_json or {})
    success = connector.stop_campaign(campaign.external_id)
    
    if success:
        action.status = "executed"
        # Update local state
        campaign.desired_status = "stopped"  # Sync will pick this up eventually or we trust it
        
        # Resolve associated recommendation if exists
        if action.recommendation_id:
            reco = db.get(OrgRecommendation, action.recommendation_id)
            if reco and not reco.resolved_at:
                reco.resolved_at = datetime.utcnow()
                reco.resolved_by_user_id = None # System resolved
    else:
        action.status = "failed"
        action.description += "\n[System] Connector returned failure."
