import argparse
from datetime import date

from app.db.session import SessionLocal
from app.db.models import Connection, SyncRun, SyncRunStatus, SyncRunType
from app.jobs.service import create_job
from app.workers.sync_tasks import execute_sync_run
from app.security.credentials_crypto import (
    CredentialsCryptoError,
    encryption_enabled,
    is_encrypted,
    maybe_encrypt,
    rotate_wrapper,
)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def run_connection_sync(args: argparse.Namespace) -> int:
    session = SessionLocal()
    try:
        connection = session.get(Connection, args.connection_id)
        if not connection:
            raise SystemExit(f"Connection not found: {args.connection_id}")

        context = {
            "connection_id": connection.id,
            "date_from": args.date_from.isoformat(),
            "date_to": args.date_to.isoformat(),
            "force": args.force,
        }
        job = create_job(
            session,
            job_type="connection_sync",
            context=context,
            organization_id=connection.organization_id,
            connection_id=connection.id,
        )

        params = dict(context)
        params["job_run_id"] = job.id

        run = SyncRun(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            platform=connection.platform,
            run_type=SyncRunType.metrics,
            status=SyncRunStatus.queued,
            params_json=params,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        if args.inline:
            execute_sync_run(run.id)
        else:
            execute_sync_run.delay(run.id)

        print(f"sync_run_id={run.id} job_run_id={job.id}")
        return 0
    finally:
        session.close()


def rotate_credentials(args: argparse.Namespace) -> int:
    if not encryption_enabled():
        raise SystemExit("Credentials encryption keys are not configured.")
    session = SessionLocal()
    updated = 0
    skipped = 0
    failed = 0
    try:
        connections = session.query(Connection).order_by(Connection.id).all()
        for connection in connections:
            try:
                current = connection.credentials_json or {}
                if is_encrypted(current):
                    rotated = rotate_wrapper(current)
                else:
                    rotated = maybe_encrypt(current)
                if rotated != current:
                    connection.credentials_json = rotated
                    updated += 1
                else:
                    skipped += 1
            except CredentialsCryptoError:
                failed += 1
        session.commit()
    finally:
        session.close()
    print(f"rotate_credentials updated={updated} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="parser2 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Run connection sync")
    sync_parser.add_argument("--connection-id", type=int, required=True)
    sync_parser.add_argument("--date-from", type=_parse_date, required=True)
    sync_parser.add_argument("--date-to", type=_parse_date, required=True)
    sync_parser.add_argument("--force", action="store_true")
    sync_parser.add_argument("--inline", action="store_true", help="Run sync inline without Celery")
    sync_parser.set_defaults(func=run_connection_sync)

    rotate_parser = subparsers.add_parser("rotate-credentials", help="Rotate encrypted credentials")
    rotate_parser.set_defaults(func=rotate_credentials)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
