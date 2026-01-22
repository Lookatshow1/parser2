from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import (
    OrgAutomationAction,
    OrgRecommendation,
    Connection,
    OrgAuditEvent,
    AdCampaign
)
from app.services.sync_service import get_connector
from app.services.audit import log_org_event

def execute_action(db: Session, action_id: int, actor_user_id: int | None) -> OrgAutomationAction:
    """
    Executes an automation action. 
    Currently supports: 'stop_campaign'.
    """
    action = db.query(OrgAutomationAction).filter(OrgAutomationAction.id == action_id).first()
    if not action:
        raise ValueError("Action not found")
        
    if action.status not in ("draft", "pending", "failed"):
        raise ValueError(f"Action in status {action.status} cannot be executed")

    # Lock row? For now rely on optimistic flow or caller lock
    
    # 1. Resolve context
    # Recommendation links to subject (e.g. Campaign)
    # But we need Connection to get Connector.
    rec = db.query(OrgRecommendation).filter(OrgRecommendation.id == action.recommendation_id).first()
    if not rec:
         # Fallback: maybe action has context payload?
         pass

    # We need connection_id.
    # Recommendation has connection_id
    connection_id = rec.connection_id if rec else None
    
    if not connection_id:
        # Try to infer from subject if it's a campaign
        # But subject_id is internal ID.
        pass # TODO: handle missing connection in reco

    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        return _mark_failed(db, action, "Connection not found")

    # 2. Identify Action Type
    # action.action_type corresponds to recommendation code? 
    # Or we parse action instruction?
    # Usually recommendation code implies action. e.g. LOW_CTR -> "stop_campaign" or just "notify"
    # Actually, the implementation plan says we focus on "Pause Campaign".
    # Let's assume the payload or a specific mapping logic tells us what to do.
    # For MVP, let's look at the method call: stop_campaign. 
    # We need to know WHICH campaign.
    
    # Subject: campaign
    if rec.subject_type != "campaign":
         return _mark_failed(db, action, f"Unsupported subject type: {rec.subject_type}")
    
    campaign = db.query(AdCampaign).filter(AdCampaign.id == rec.subject_id).first()
    if not campaign:
         return _mark_failed(db, action, "Campaign not found")

    # 3. Initialize Connector
    try:
        connector = get_connector(db, connection)
    except Exception as e:
        return _mark_failed(db, action, f"Connector init failed: {e}")

    # 4. Execute
    action.status = "applying"
    db.commit()

    success = False
    error_msg = None
    
    try:
        # We generally want "stop_campaign" for now for high severity rules
        # Or check what the recommendation implies.
        # Let's assume ANY execution request for a campaign recommendation means STOP/PAUSE 
        # unless specified otherwise.
        # Ideally, action.action_type should be "stop_campaign".
        # Current generator puts "LOW_CTR" etc as code.
        
        # NOTE: For this task, we assume we want to STOP.
        
        success = connector.stop_campaign(campaign.external_id)
        if not success:
            error_msg = "Connector returned failure"
            
    except Exception as exc:
        error_msg = str(exc)
        success = False

    # 5. Update Result
    if success:
        action.status = "applied"
        action.updated_at = datetime.utcnow()
        # Also resolve recommendation?
        if rec:
            rec.resolved_at = datetime.utcnow()
            rec.resolved_by_user_id = actor_user_id
    else:
        action.status = "failed"
        action.payload_json["last_error"] = error_msg

    db.commit()
    
    # Audit
    log_org_event(
        db,
        organization_id=action.organization_id,
        actor_user_id=actor_user_id,
        action="automation_action_applied" if success else "automation_action_failed",
        subject_type="automation_action",
        subject_id=action.id,
        meta={"success": success, "error": error_msg}
    )
    
    return action

def _mark_failed(db, action, reason):
    action.status = "failed"
    action.payload_json = action.payload_json or {}
    action.payload_json["error"] = reason
    db.commit()
    return action
