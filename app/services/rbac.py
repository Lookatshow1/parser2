from app.db.models import MembershipRole


ROLE_OWNER = MembershipRole.owner.value
ROLE_ADMIN = MembershipRole.admin.value
ROLE_MEMBER = MembershipRole.member.value
ROLE_VIEWER = MembershipRole.viewer.value

ROLE_ORDER = [ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER]

PERM_ORGS_READ = "orgs.read"
PERM_ORGS_INVITE = "orgs.invite"
PERM_ORGS_MANAGE_MEMBERS = "orgs.manage_members"
PERM_ORGS_CHANGE_ROLES = "orgs.change_roles"
PERM_CONNECTIONS_READ = "connections.read"
PERM_CONNECTIONS_WRITE = "connections.write"
PERM_CONNECTIONS_SYNC = "connections.sync"
PERM_CAMPAIGNS_READ = "campaigns.read"
PERM_CAMPAIGNS_WRITE = "campaigns.write"
PERM_BILLING_READ = "billing.read"
PERM_BILLING_WRITE = "billing.write"

ROLE_PERMISSIONS = {
    ROLE_OWNER: {
        PERM_ORGS_READ,
        PERM_ORGS_INVITE,
        PERM_ORGS_MANAGE_MEMBERS,
        PERM_ORGS_CHANGE_ROLES,
        PERM_CONNECTIONS_READ,
        PERM_CONNECTIONS_WRITE,
        PERM_CONNECTIONS_SYNC,
        PERM_CAMPAIGNS_READ,
        PERM_CAMPAIGNS_WRITE,
        PERM_BILLING_READ,
        PERM_BILLING_WRITE,
    },
    ROLE_ADMIN: {
        PERM_ORGS_READ,
        PERM_ORGS_INVITE,
        PERM_ORGS_MANAGE_MEMBERS,
        PERM_CONNECTIONS_READ,
        PERM_CONNECTIONS_WRITE,
        PERM_CONNECTIONS_SYNC,
        PERM_CAMPAIGNS_READ,
        PERM_CAMPAIGNS_WRITE,
        PERM_BILLING_READ,
        PERM_BILLING_WRITE,
    },
    ROLE_MEMBER: {
        PERM_ORGS_READ,
        PERM_CONNECTIONS_READ,
        PERM_CONNECTIONS_WRITE,
        PERM_CONNECTIONS_SYNC,
        PERM_CAMPAIGNS_READ,
        PERM_CAMPAIGNS_WRITE,
        PERM_BILLING_READ,
    },
    ROLE_VIEWER: {
        PERM_ORGS_READ,
        PERM_CONNECTIONS_READ,
        PERM_CAMPAIGNS_READ,
        PERM_BILLING_READ,
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def list_role_permissions() -> dict[str, list[str]]:
    return {role: sorted(ROLE_PERMISSIONS.get(role, set())) for role in ROLE_ORDER}


def can_invite(role: str) -> bool:
    return has_permission(role, PERM_ORGS_INVITE)


def can_manage_members(role: str) -> bool:
    return has_permission(role, PERM_ORGS_MANAGE_MEMBERS)


def can_change_roles(role: str) -> bool:
    return has_permission(role, PERM_ORGS_CHANGE_ROLES)


def can_write_connections(role: str) -> bool:
    return has_permission(role, PERM_CONNECTIONS_WRITE)


def can_run_sync(role: str) -> bool:
    return has_permission(role, PERM_CONNECTIONS_SYNC)


def can_read(role: str) -> bool:
    return has_permission(role, PERM_CAMPAIGNS_READ)


def can_read_campaigns(role: str) -> bool:
    return has_permission(role, PERM_CAMPAIGNS_READ)


def can_write_campaigns(role: str) -> bool:
    return has_permission(role, PERM_CAMPAIGNS_WRITE)


def can_read_billing(role: str) -> bool:
    return has_permission(role, PERM_BILLING_READ)


def can_write_billing(role: str) -> bool:
    return has_permission(role, PERM_BILLING_WRITE)
