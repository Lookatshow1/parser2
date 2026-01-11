from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import ChangePlan, ChangePlanItem, Connection, AdCampaign, AdAdGroup, AdAd
from app.workers.change_plan_tasks import apply_change_plan
from app.core.context import get_correlation_id

def create_plan(
    db: Session,
    org_id: int,
    user_id: int,
    connection_id: int,
    title: str,
    date_from: date | None = None,
    date_to: date | None = None
) -> ChangePlan:
    # Validate connection
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org_id).first()
    if not conn:
        raise ValueError("Подключение не найдено")

    plan = ChangePlan(
        organization_id=org_id,
        connection_id=connection_id,
        title=title,
        status="draft",
        date_from=date_from,
        date_to=date_to,
        created_by_user_id=user_id
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

def add_item(
    db: Session,
    org_id: int,
    plan_id: int,
    subject_type: str,
    subject_id: int,
    action_type: str,
    params: dict
) -> ChangePlanItem:
    plan = db.query(ChangePlan).filter(ChangePlan.id == plan_id, ChangePlan.organization_id == org_id).first()
    if not plan:
        raise ValueError("План не найден")
    if plan.status != "draft":
        raise ValueError("План уже зафиксирован, редактирование невозможно")

    # Validate subject belongs to connection
    if subject_type == "campaign":
        obj = db.query(AdCampaign).filter(AdCampaign.id == subject_id, AdCampaign.connection_id == plan.connection_id).first()
    elif subject_type == "ad_group":
        obj = db.query(AdAdGroup).filter(AdAdGroup.id == subject_id, AdAdGroup.connection_id == plan.connection_id).first()
    elif subject_type == "ad":
        obj = db.query(AdAd).filter(AdAd.id == subject_id, AdAd.connection_id == plan.connection_id).first()
    else:
        raise ValueError("Неверный тип объекта")

    if not obj:
        raise ValueError("Объект не найден в этом подключении")

    item = ChangePlanItem(
        plan_id=plan.id,
        subject_type=subject_type,
        subject_id=subject_id,
        action_type=action_type,
        params_json=params,
        status="pending"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def set_plan_status(db: Session, org_id: int, plan_id: int, status: str) -> ChangePlan:
    plan = db.query(ChangePlan).filter(ChangePlan.id == plan_id, ChangePlan.organization_id == org_id).first()
    if not plan:
        raise ValueError("План не найден")

    if status == "ready":
        if plan.status != "draft":
            raise ValueError("Только черновик можно перевести в статус 'Готов'")
        plan.status = "ready"
    else:
        raise ValueError("Недопустимый статус")

    db.commit()
    db.refresh(plan)
    return plan

def execute_plan(db: Session, org_id: int, plan_id: int) -> ChangePlan:
    plan = db.query(ChangePlan).filter(ChangePlan.id == plan_id, ChangePlan.organization_id == org_id).first()
    if not plan:
        raise ValueError("План не найден")

    if plan.status != "ready":
        raise ValueError("План должен быть в статусе 'Готов' для применения")

    # Launch async task
    correlation_id = get_correlation_id()
    apply_change_plan.delay(plan.id, correlation_id)

    # Optimistically set status? Or wait for task?
    # Usually we set to 'applying' or keep 'ready' until task picks it up.
    # But schema has draft|ready|applied|failed. Maybe add 'applying'?
    # For MVP let's keep 'ready' and let task update to applied/failed.
    # Or better, update to 'applied' (in progress) if we had such status.
    # Let's assume task runs fast or UI polls.

    return plan
