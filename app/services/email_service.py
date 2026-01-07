from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone

from app.core.config import get_settings


def _build_invite_subject(org_name: str) -> str:
    return f"Invitation to join {org_name}"


def _build_invite_body(
    org_name: str,
    role: str,
    expires_at: datetime,
    join_url: str | None,
    raw_token: str,
) -> str:
    expires_local = expires_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"You have been invited to join {org_name}.",
        f"Role: {role}",
        f"Expires at: {expires_local}",
        "",
    ]
    if join_url:
        lines.append(f"Accept invite: {join_url}")
    else:
        lines.append("Accept invite with this token:")
        lines.append(raw_token)
    lines.append("")
    lines.append("If you did not expect this invitation, you can ignore this email.")
    return "\n".join(lines)


def send_invite_email(
    to_email: str,
    org_name: str,
    role: str,
    expires_at: datetime,
    join_url: str | None,
    raw_token: str,
) -> tuple[bool, str | None]:
    settings = get_settings()
    if settings.email_send_mode.lower() == "noop" or os.getenv("PYTEST_CURRENT_TEST"):
        return True, None
    if not settings.smtp_host:
        return False, "smtp_not_configured"

    message = EmailMessage()
    message["Subject"] = _build_invite_subject(org_name)
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        _build_invite_body(org_name, role, expires_at, join_url, raw_token)
    )

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(message)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(message)
        return True, None
    except Exception as exc:  # pragma: no cover - runtime-specific
        return False, str(exc)
