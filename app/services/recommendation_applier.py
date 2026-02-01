"""
Recommendation Applier Service

Applies AI recommendations to advertising platforms (Yandex Direct, VK Ads).
Supports actions: pause_ad, enable_ad, change_bid, pause_campaign, enable_campaign.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.db.models import (
    Organization,
    Connection,
    OrgRecommendation,
    OrgAutomationAction,
    Platform,
)
from app.services.connector_service import get_connector
from app.services.audit import log_org_event
from app.security.credentials_crypto import maybe_decrypt

logger = logging.getLogger(__name__)


class ApplyResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_SUPPORTED = "not_supported"


# Mapping recommendation codes to actions
ACTION_MAPPING = {
    "pause_ineffective_ad": "pause_ad",
    "pause_high_cpc_ad": "pause_ad",
    "pause_low_ctr_ad": "pause_ad",
    "pause_no_conversions": "pause_campaign",
    "increase_bid": "change_bid",
    "decrease_bid": "change_bid",
    "enable_paused_ad": "enable_ad",
}


def apply_recommendation(
    db: Session,
    recommendation_id: int,
    actor_user_id: int | None = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Apply a recommendation to the advertising platform.
    
    Args:
        db: Database session
        recommendation_id: ID of the OrgRecommendation
        actor_user_id: User who triggered the action (None = automated)
        dry_run: If True, only simulate the action
        
    Returns:
        Dict with status, message, and details
    """
    reco = db.query(OrgRecommendation).filter(OrgRecommendation.id == recommendation_id).first()
    if not reco:
        return {"status": ApplyResult.FAILED, "message": "Recommendation not found"}
    
    if reco.resolved_at:
        return {"status": ApplyResult.SKIPPED, "message": "Already resolved"}
    
    # Get the connection for this recommendation
    connection = None
    if reco.connection_id:
        connection = db.query(Connection).filter(Connection.id == reco.connection_id).first()
    
    if not connection:
        return {"status": ApplyResult.FAILED, "message": "No connection found for recommendation"}
    
    # Determine action type
    action_type = ACTION_MAPPING.get(reco.code, reco.action)
    if not action_type:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": f"Unknown action for code: {reco.code}"}
    
    # Get connector
    try:
        creds = maybe_decrypt(connection.credentials_json) if connection.credentials_json else {}
        connector = get_connector(connection.platform, creds)
    except Exception as e:
        logger.exception(f"Failed to get connector for {connection.platform}")
        return {"status": ApplyResult.FAILED, "message": f"Connector error: {str(e)}"}
    
    # Build action payload
    meta = reco.meta_json or {}
    subject_id = reco.subject_id
    
    result = {"status": ApplyResult.NOT_SUPPORTED, "message": "Action not implemented"}
    
    try:
        if action_type == "pause_ad":
            result = _apply_pause_ad(connector, subject_id, meta, dry_run)
        elif action_type == "enable_ad":
            result = _apply_enable_ad(connector, subject_id, meta, dry_run)
        elif action_type == "pause_campaign":
            result = _apply_pause_campaign(connector, subject_id, meta, dry_run)
        elif action_type == "enable_campaign":
            result = _apply_enable_campaign(connector, subject_id, meta, dry_run)
        elif action_type == "change_bid":
            new_bid = meta.get("suggested_bid") or meta.get("new_bid")
            result = _apply_change_bid(connector, subject_id, new_bid, meta, dry_run)
        else:
            result = {"status": ApplyResult.NOT_SUPPORTED, "message": f"Action {action_type} not supported"}
    except Exception as e:
        logger.exception(f"Failed to apply action {action_type}")
        result = {"status": ApplyResult.FAILED, "message": str(e)}
    
    # Log and update recommendation
    if result["status"] == ApplyResult.SUCCESS and not dry_run:
        reco.resolved_at = datetime.utcnow()
        reco.resolved_by_user_id = actor_user_id
        
        # Create automation action record
        action = OrgAutomationAction(
            organization_id=reco.organization_id,
            recommendation_id=reco.id,
            action_type=action_type,
            status="applied",
            title=reco.title,
            description=f"Auto-applied: {reco.description}",
            payload_json={
                "recommendation_code": reco.code,
                "subject_type": reco.subject_type,
                "subject_id": subject_id,
                "result": result,
            },
        )
        db.add(action)
        
        log_org_event(
            db,
            organization_id=reco.organization_id,
            actor_user_id=actor_user_id,
            action="recommendation_applied",
            subject_type="recommendation",
            subject_id=reco.id,
            meta={"action_type": action_type, "result": result["status"]},
        )
        
        db.commit()
    
    return result


def _apply_pause_ad(connector, ad_id: int, meta: dict, dry_run: bool) -> Dict[str, Any]:
    """Pause a specific ad."""
    if dry_run:
        return {"status": ApplyResult.SUCCESS, "message": f"Would pause ad {ad_id}", "dry_run": True}
    
    if hasattr(connector, "pause_ad"):
        connector.pause_ad(ad_id)
        return {"status": ApplyResult.SUCCESS, "message": f"Paused ad {ad_id}"}
    elif hasattr(connector, "set_ad_status"):
        connector.set_ad_status(ad_id, "paused")
        return {"status": ApplyResult.SUCCESS, "message": f"Paused ad {ad_id}"}
    else:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": "Connector doesn't support pause_ad"}


def _apply_enable_ad(connector, ad_id: int, meta: dict, dry_run: bool) -> Dict[str, Any]:
    """Enable a paused ad."""
    if dry_run:
        return {"status": ApplyResult.SUCCESS, "message": f"Would enable ad {ad_id}", "dry_run": True}
    
    if hasattr(connector, "enable_ad"):
        connector.enable_ad(ad_id)
        return {"status": ApplyResult.SUCCESS, "message": f"Enabled ad {ad_id}"}
    elif hasattr(connector, "set_ad_status"):
        connector.set_ad_status(ad_id, "active")
        return {"status": ApplyResult.SUCCESS, "message": f"Enabled ad {ad_id}"}
    else:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": "Connector doesn't support enable_ad"}


def _apply_pause_campaign(connector, campaign_id: int, meta: dict, dry_run: bool) -> Dict[str, Any]:
    """Pause a campaign."""
    if dry_run:
        return {"status": ApplyResult.SUCCESS, "message": f"Would pause campaign {campaign_id}", "dry_run": True}
    
    if hasattr(connector, "pause_campaign"):
        connector.pause_campaign(campaign_id)
        return {"status": ApplyResult.SUCCESS, "message": f"Paused campaign {campaign_id}"}
    elif hasattr(connector, "set_campaign_status"):
        connector.set_campaign_status(campaign_id, "paused")
        return {"status": ApplyResult.SUCCESS, "message": f"Paused campaign {campaign_id}"}
    else:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": "Connector doesn't support pause_campaign"}


def _apply_enable_campaign(connector, campaign_id: int, meta: dict, dry_run: bool) -> Dict[str, Any]:
    """Enable a paused campaign."""
    if dry_run:
        return {"status": ApplyResult.SUCCESS, "message": f"Would enable campaign {campaign_id}", "dry_run": True}
    
    if hasattr(connector, "enable_campaign"):
        connector.enable_campaign(campaign_id)
        return {"status": ApplyResult.SUCCESS, "message": f"Enabled campaign {campaign_id}"}
    elif hasattr(connector, "set_campaign_status"):
        connector.set_campaign_status(campaign_id, "active")
        return {"status": ApplyResult.SUCCESS, "message": f"Enabled campaign {campaign_id}"}
    else:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": "Connector doesn't support enable_campaign"}


def _apply_change_bid(connector, ad_id: int, new_bid: float, meta: dict, dry_run: bool) -> Dict[str, Any]:
    """Change bid for an ad or keyword."""
    if not new_bid:
        return {"status": ApplyResult.FAILED, "message": "No bid value provided"}
    
    if dry_run:
        return {"status": ApplyResult.SUCCESS, "message": f"Would change bid to {new_bid}", "dry_run": True}
    
    if hasattr(connector, "set_bid"):
        connector.set_bid(ad_id, new_bid)
        return {"status": ApplyResult.SUCCESS, "message": f"Changed bid to {new_bid}"}
    else:
        return {"status": ApplyResult.NOT_SUPPORTED, "message": "Connector doesn't support set_bid"}


def apply_all_pending_for_org(
    db: Session,
    org_id: int,
    actor_user_id: int | None = None,
    dry_run: bool = False,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Apply all pending (unresolved) recommendations for an organization.
    
    Returns summary of applied actions.
    """
    recos = (
        db.query(OrgRecommendation)
        .filter(
            OrgRecommendation.organization_id == org_id,
            OrgRecommendation.resolved_at.is_(None),
        )
        .order_by(OrgRecommendation.severity.desc())  # Critical first
        .limit(limit)
        .all()
    )
    
    results = {
        "total": len(recos),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "not_supported": 0,
        "details": [],
    }
    
    for reco in recos:
        result = apply_recommendation(db, reco.id, actor_user_id, dry_run)
        status = result.get("status", ApplyResult.FAILED)
        
        if status == ApplyResult.SUCCESS:
            results["success"] += 1
        elif status == ApplyResult.FAILED:
            results["failed"] += 1
        elif status == ApplyResult.SKIPPED:
            results["skipped"] += 1
        else:
            results["not_supported"] += 1
        
        results["details"].append({
            "recommendation_id": reco.id,
            "code": reco.code,
            "result": result,
        })
    
    return results
