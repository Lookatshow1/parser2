from app.db.models import MembershipRole


ROLE_OWNER = MembershipRole.owner.value
ROLE_ADMIN = MembershipRole.admin.value
ROLE_MEMBER = MembershipRole.member.value
ROLE_VIEWER = MembershipRole.viewer.value


def can_invite(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ADMIN}


def can_manage_members(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ADMIN}


def can_write_connections(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER}


def can_run_sync(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER}


def can_read(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER}
