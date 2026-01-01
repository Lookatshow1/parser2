from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    BudgetAllocation,
    Experiment,
    ExperimentRound,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    MetricSnapshot,
    Platform,
    CreativeVariant,
)


class ExperimentService:
    def create_experiment(self, session: Session, project_id: int, total_budget: int, platforms: list[str]) -> Experiment:
        existing = session.scalar(
            select(Experiment).where(
                Experiment.project_id == project_id,
                Experiment.status.in_([ExperimentStatus.planned, ExperimentStatus.running]),
            )
        )
        if existing:
            return existing

        experiment = Experiment(
            plan_id=None,
            project_id=project_id,
            total_budget=total_budget,
            platforms=platforms,
            status=ExperimentStatus.planned,
        )
        session.add(experiment)
        session.commit()
        session.refresh(experiment)
        return experiment

    def start_experiment(self, session: Session, experiment_id: int) -> Experiment:
        experiment = session.get(Experiment, experiment_id)
        if experiment is None:
            raise ValueError("Experiment not found")

        if experiment.status == ExperimentStatus.running:
            return experiment

        experiment.status = ExperimentStatus.running
        experiment.started_at = experiment.started_at or datetime.utcnow()
        session.commit()

        existing_round = session.scalar(
            select(ExperimentRound).where(ExperimentRound.experiment_id == experiment.id, ExperimentRound.round_index == 1)
        )
        if not existing_round:
            self._create_round(session, experiment, round_index=1)

        session.refresh(experiment)
        return experiment

    def close_round(self, session: Session, experiment_id: int) -> ExperimentRound | None:
        experiment = session.execute(
            select(Experiment).where(Experiment.id == experiment_id).with_for_update()
        ).scalar_one_or_none()
        if experiment is None:
            raise ValueError("Experiment not found")
        if experiment.processing:
            return None
        experiment.processing = True
        session.commit()

        try:
            current_round = session.scalar(
                select(ExperimentRound)
                .where(ExperimentRound.experiment_id == experiment_id, ExperimentRound.ended_at.is_(None))
                .order_by(ExperimentRound.round_index.desc())
            )
            if current_round is None:
                return None

            if current_round.ended_at:
                return current_round

            current_round.ended_at = datetime.utcnow()
            session.commit()

            next_index = current_round.round_index + 1
            existing_next = session.scalar(
                select(ExperimentRound).where(
                    ExperimentRound.experiment_id == experiment_id, ExperimentRound.round_index == next_index
                )
            )
            if existing_next:
                return existing_next

            budget_plan = self._reallocate_budget(session, experiment, current_round)
            next_round = ExperimentRound(
                experiment_id=experiment_id,
                round_index=next_index,
                budget_plan=budget_plan,
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow() + timedelta(days=7),
            )
            session.add(next_round)
            session.flush()
            self._create_round_assets(session, experiment, next_round)
            session.commit()
            return next_round
        finally:
            experiment.processing = False
            session.commit()

    def report(self, session: Session, experiment_id: int) -> dict:
        experiment = session.get(Experiment, experiment_id)
        if experiment is None:
            raise ValueError("Experiment not found")
        rounds = session.scalars(
            select(ExperimentRound).where(ExperimentRound.experiment_id == experiment_id).order_by(ExperimentRound.round_index)
        ).all()
        return {
            "experiment_id": experiment.id,
            "status": experiment.status.value,
            "rounds": [
                {
                    "round_index": round_item.round_index,
                    "budget_plan": round_item.budget_plan,
                    "started_at": round_item.started_at,
                    "ended_at": round_item.ended_at,
                }
                for round_item in rounds
            ],
        }

    def _create_round(self, session: Session, experiment: Experiment, round_index: int) -> ExperimentRound:
        platforms = experiment.platforms or []
        if not platforms:
            raise ValueError("Platforms not defined")
        total_budget = experiment.total_budget or 0
        per_platform = total_budget // len(platforms)
        remainder = total_budget % len(platforms)
        budget_plan: dict[str, int] = {}
        for index, platform in enumerate(platforms):
            budget_plan[platform] = per_platform + (1 if index < remainder else 0)

        round_item = ExperimentRound(
            experiment_id=experiment.id,
            round_index=round_index,
            budget_plan=budget_plan,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow() + timedelta(days=7),
        )
        session.add(round_item)
        session.flush()
        self._create_round_assets(session, experiment, round_item)
        session.commit()
        return round_item

    def _create_round_assets(self, session: Session, experiment: Experiment, round_item: ExperimentRound) -> None:
        platforms = [Platform(value) for value in (experiment.platforms or [])]
        for platform in platforms:
            hypothesis = Hypothesis(
                experiment_round_id=round_item.id,
                text=f"Hypothesis for {platform.value} round {round_item.round_index}",
                segmentation_params={},
                status=HypothesisStatus.active,
            )
            session.add(hypothesis)
            session.flush()
            creatives = []
            for index in range(2):
                creative = CreativeVariant(
                    experiment_id=experiment.id,
                    hypothesis_id=hypothesis.id,
                    platform=platform,
                    title=f"Title {platform.value} {index + 1}",
                    text=f"Creative text {platform.value} {index + 1}",
                    media_url=None,
                    moderation_status="draft",
                    external_ids=None,
                    image_url=None,
                    meta_json=None,
                )
                session.add(creative)
                creatives.append(creative)

            session.flush()

            platform_budget = round_item.budget_plan.get(platform.value, 0)
            session.add(
                BudgetAllocation(
                    experiment_id=experiment.id,
                    experiment_round_id=round_item.id,
                    platform=platform,
                    creative_variant_id=None,
                    amount=platform_budget,
                )
            )
            per_creative = platform_budget // len(creatives) if creatives else 0
            remainder = platform_budget % len(creatives) if creatives else 0
            for idx, creative in enumerate(creatives):
                amount = per_creative + (1 if idx < remainder else 0)
                session.add(
                    BudgetAllocation(
                        experiment_id=experiment.id,
                        experiment_round_id=round_item.id,
                        platform=platform,
                        creative_variant_id=creative.id,
                        amount=amount,
                    )
                )

    def _reallocate_budget(self, session: Session, experiment: Experiment, round_item: ExperimentRound) -> dict[str, int]:
        platforms = [Platform(value) for value in (experiment.platforms or [])]
        total_budget = sum(round_item.budget_plan.values())
        scores: dict[str, float] = {}
        for platform in platforms:
            metrics = session.scalars(
                select(MetricSnapshot).where(MetricSnapshot.platform == platform)
            ).all()
            clicks = sum(metric.clicks for metric in metrics)
            spend = sum(metric.spend for metric in metrics)
            if clicks > 0:
                scores[platform.value] = spend / clicks
            else:
                scores[platform.value] = float("inf")

        best_platforms = sorted(scores.items(), key=lambda item: item[1])
        if not best_platforms:
            return round_item.budget_plan

        weights: dict[str, float] = {}
        total_weight = 0.0
        for platform, score in best_platforms:
            weight = 1.0 / (score + 1.0)
            weights[platform] = weight
            total_weight += weight

        new_plan: dict[str, int] = {}
        remaining = total_budget
        for idx, platform in enumerate(weights.keys()):
            if idx == len(weights) - 1:
                new_plan[platform] = remaining
            else:
                amount = int(total_budget * (weights[platform] / total_weight))
                new_plan[platform] = amount
                remaining -= amount
        return new_plan
