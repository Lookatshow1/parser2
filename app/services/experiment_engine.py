from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import (
    BudgetAllocation,
    CampaignPlan,
    CreativeVariant,
    Experiment,
    ExperimentStatus,
    Platform,
)


class ExperimentEngine:
    def start_test(self, session: Session, plan_id: int, budget: int) -> Experiment:
        plan = session.get(CampaignPlan, plan_id)
        if plan is None:
            raise ValueError("Plan not found")

        now = datetime.utcnow()
        experiment = Experiment(
            plan_id=plan.id,
            organization_id=plan.organization_id,
            status=ExperimentStatus.draft,
            start_at=now,
            end_at=now + timedelta(days=7),
        )
        session.add(experiment)
        session.flush()

        creatives = self._create_creatives(session, experiment.id)
        self._allocate_budget(session, experiment.id, creatives, budget)

        session.commit()
        session.refresh(experiment)
        return experiment

    def _create_creatives(self, session: Session, experiment_id: int) -> list[CreativeVariant]:
        variants: list[CreativeVariant] = []
        platforms = [Platform.yandex, Platform.ozon, Platform.vk]
        for index in range(6):
            platform = platforms[index % len(platforms)]
            variant = CreativeVariant(
                experiment_id=experiment_id,
                platform=platform,
                text=f"Placeholder creative {index + 1}",
                image_url=None,
                meta_json=None,
            )
            session.add(variant)
            variants.append(variant)
        session.flush()
        return variants

    def _allocate_budget(
        self,
        session: Session,
        experiment_id: int,
        creatives: list[CreativeVariant],
        total_budget: int,
    ) -> None:
        platforms = [Platform.yandex, Platform.ozon, Platform.vk]
        platform_budget = total_budget // len(platforms)
        platform_remainder = total_budget % len(platforms)

        for index, platform in enumerate(platforms):
            amount = platform_budget + (1 if index < platform_remainder else 0)
            session.add(
                BudgetAllocation(
                    experiment_id=experiment_id,
                    platform=platform,
                    creative_variant_id=None,
                    amount=amount,
                )
            )

            platform_creatives = [c for c in creatives if c.platform == platform]
            if not platform_creatives:
                continue
            per_variant = amount // len(platform_creatives)
            remainder = amount % len(platform_creatives)
            for creative_index, creative in enumerate(platform_creatives):
                variant_amount = per_variant + (1 if creative_index < remainder else 0)
                session.add(
                    BudgetAllocation(
                        experiment_id=experiment_id,
                        platform=platform,
                        creative_variant_id=creative.id,
                        amount=variant_amount,
                    )
                )
