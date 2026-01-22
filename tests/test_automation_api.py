from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from app.db.models import (
    OrgAutomationAction, OrgRecommendation, Connection, 
    Platform, AdCampaign, OrgAutomationRun, Membership, MembershipRole
)
from app.services.automation_executor import execute_action

# Using fixtures from conftest.py: db_session, org_a, user_a

def test_execute_action_flow(db_session, org_a, user_a):
    # Setup Data
    # user_a is already in org_a as owner
    
    # Connection
    conn = Connection(
        organization_id=org_a.id,
        platform=Platform.yandex,
        name="Yandex Mock",
        credentials_json={"mock": True, "login": "test"},
        status="active"
    )
    db_session.add(conn)
    db_session.flush()
    
    # Campaign
    camp = AdCampaign(
        organization_id=org_a.id,
        connection_id=conn.id,
        platform=Platform.yandex,
        external_id="12345",
        name="Test Campaign"
    )
    db_session.add(camp)
    db_session.flush()
    
    # Recommendation
    rec = OrgRecommendation(
        organization_id=org_a.id,
        connection_id=conn.id,
        subject_type="campaign",
        subject_id=camp.id,
        code="LOW_CTR",
        severity="warn",
        title="Low CTR",
        description="Fix it",
        action="Stop campaign",
        valid_from=date.today(),
        valid_to=date.today()
    )
    db_session.add(rec)
    db_session.flush()
    
    # Action
    run = OrgAutomationRun(organization_id=org_a.id, status="running")
    db_session.add(run)
    db_session.flush()
    
    action = OrgAutomationAction(
        organization_id=org_a.id,
        run_id=run.id,
        recommendation_id=rec.id,
        action_type="stop_campaign",
        status="draft",
        title="Stop Campaign",
        description="Stopping...",
        payload_json={}
    )
    db_session.add(action)
    db_session.commit()
    
    # 2. Execute with mocked connector
    with patch("app.services.automation_executor.get_connector") as mock_get_conn:
        mock_connector = MagicMock()
        mock_connector.stop_campaign.return_value = True
        mock_get_conn.return_value = mock_connector
        
        updated_action = execute_action(db_session, action.id, user_a.id)
        
        # Verify
        assert updated_action.status == "applied"
        assert updated_action.updated_at is not None
        
        # Verify call
        mock_connector.stop_campaign.assert_called_once_with("12345")
        
        # Verify recommendation is resolved
        db_session.refresh(rec)
        assert rec.resolved_at is not None
        assert rec.resolved_by_user_id == user_a.id

def test_execute_action_not_found(db_session):
    with pytest.raises(ValueError, match="Action not found"):
        execute_action(db_session, 99999, 1)

def test_execute_action_wrong_status(db_session, org_a, user_a):
    action = OrgAutomationAction(
        organization_id=org_a.id,
        action_type="stop",
        title="Already Applied",
        description="...",
        status="applied"
    )
    db_session.add(action)
    db_session.commit()
    
    with pytest.raises(ValueError, match="cannot be executed"):
        execute_action(db_session, action.id, user_a.id)
