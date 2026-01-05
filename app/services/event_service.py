from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    CampaignPlan,
    ConversionEvent,
    ConversionEventType,
    Experiment,
    MetricSnapshot,
    Platform,
)


class EventService:
    def handle_event(self, session: Session, event_type: ConversionEventType, payload) -> tuple[ConversionEvent, bool]:
        existing = session.scalar(select(ConversionEvent).where(ConversionEvent.event_id == str(payload.event_id)))
        if existing:
            return existing, True

        plan = None
        experiment = None
        if payload.utm_campaign:
            plan = session.scalar(
                select(CampaignPlan).where(CampaignPlan.internal_code == payload.utm_campaign)
            )
            if plan:
                experiment = session.scalar(
                    select(Experiment)
                    .where(Experiment.plan_id == plan.id)
                    .order_by(Experiment.created_at.desc())
                )

        event = ConversionEvent(
            event_id=str(payload.event_id),
            event_type=event_type,
            occurred_at=payload.occurred_at,
            landing_url=payload.landing_url,
            utm_source=payload.utm_source,
            utm_medium=payload.utm_medium,
            utm_campaign=payload.utm_campaign,
            utm_content=payload.utm_content,
            utm_term=payload.utm_term,
            contact_phone=payload.contact.phone if payload.contact else None,
            contact_email=payload.contact.email if payload.contact else None,
            value=getattr(payload, "value", None),
            plan_id=plan.id if plan else None,
            experiment_id=experiment.id if experiment else None,
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        if plan:
            self._update_metrics(session, event, plan, experiment)

        return event, False

    def _update_metrics(
        self,
        session: Session,
        event: ConversionEvent,
        plan: CampaignPlan,
        experiment: Experiment | None,
    ) -> None:
        if not plan.internal_code:
            return

        platform = self._resolve_platform(event.utm_source)
        if platform is None:
            return

        snapshot = session.scalar(
            select(MetricSnapshot).where(
                MetricSnapshot.date == event.occurred_at.date(),
                MetricSnapshot.platform == platform,
                MetricSnapshot.campaign_external_id == plan.internal_code,
                MetricSnapshot.organization_id == plan.organization_id,
                MetricSnapshot.level == "campaign",
            )
        )

        if snapshot is None:
            snapshot = MetricSnapshot(
                organization_id=plan.organization_id,
                connection_id=plan.connection_id,
                plan_id=plan.id,
                experiment_id=experiment.id if experiment else None,
                date=event.occurred_at.date(),
                platform=platform,
                level="campaign",
                campaign_external_id=plan.internal_code,
                clicks=0,
                impressions=0,
                spend=0,
                leads=0,
                purchases=0,
                revenue=0,
            )
            session.add(snapshot)

        if event.event_type == ConversionEventType.lead:
            snapshot.leads += 1
        elif event.event_type == ConversionEventType.purchase:
            snapshot.purchases += 1
            if event.value:
                snapshot.revenue += event.value

        session.commit()

    @staticmethod
    def _resolve_platform(utm_source: str | None) -> Platform | None:
        if not utm_source:
            return None
        try:
            return Platform(utm_source)
        except ValueError:
            return None
