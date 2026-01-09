import { clearOrgId, clearRefreshToken, clearToken, getOrgId, getToken } from "./session";
import { ru } from "./ru";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const apiBase = `${baseUrl}/api`;

type ApiError = {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
};

const statusMessageMap: Record<number, string> = {
  400: "Некорректный запрос.",
  401: "Требуется вход.",
  403: "Недостаточно прав.",
  404: "Не найдено.",
  409: "Конфликт запроса.",
  422: "Ошибка валидации данных.",
  500: "Ошибка сервера. Попробуйте позже."
};

function resolveErrorMessage(status: number, serverMessage?: string | null) {
  if (serverMessage && serverMessage.trim().length > 0) {
    return serverMessage;
  }
  return statusMessageMap[status] || ru.messages.error;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const orgId = getOrgId();
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(orgId ? { "X-Org-Id": orgId } : {}),
        ...(options?.headers || {})
      },
      ...options
    });
  } catch {
    throw new Error("Сервер недоступен. Проверьте адрес API и состояние сервисов.");
  }

  if (!response.ok) {
    let error: ApiError | null = null;
    try {
      error = (await response.json()) as ApiError;
    } catch {
      error = null;
    }
    if (response.status === 401 && typeof window !== "undefined") {
      clearToken();
      clearRefreshToken();
      clearOrgId();
      window.location.href = "/login";
    }
    if (response.status === 409 && typeof window !== "undefined") {
      const message = error?.error?.message || "";
      if (message.toLowerCase().includes("select organization") || message.toLowerCase().includes("выберите организацию")) {
        window.location.href = "/orgs";
      }
    }
    const message = resolveErrorMessage(response.status, error?.error?.message || null);
    throw new Error(message);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

export type ConnectionResponse = {
  id: number;
  organization_id: number;
  advertiser_id: number | null;
  platform: string;
  status: string;
  name?: string | null;
  credentials_present?: boolean;
  last_sync_status?: string | null;
  last_sync_finished_at?: string | null;
  auto_sync_enabled?: boolean;
  auto_sync_every_minutes?: number;
  auto_sync_window_days?: number;
  last_auto_sync_at?: string | null;
};

export type PlanResponse = {
  id: number;
  url: string;
  internal_code: string | null;
};

export type ExperimentListItem = {
  id: number;
  status: string;
  plan_id: number | null;
  project_id: number | null;
  total_budget: number | null;
};

export type ExperimentReport = {
  experiment_id: number;
  status: string;
  rounds: Array<{ round_index: number; budget_plan: Record<string, number>; started_at: string | null; ended_at: string | null }>;
  metrics: Array<{ date: string; platform: string; impressions: number; clicks: number; spend: number }>;
};

export type JobRunItem = {
  id: number;
  job_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  error_text?: string | null;
  result_json?: Record<string, unknown> | null;
};

export type AuthToken = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
};

export type UserMe = {
  id: number;
  email: string;
  is_active: boolean;
  active_organization_id: number | null;
};

export type Organization = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
};

export type OrgInvite = {
  id: number;
  organization_id: number;
  invited_email: string;
  role: string;
  status: string;
  expires_at: string;
  accepted_at: string | null;
  accepted_by_user_id?: number | null;
  revoked_at?: string | null;
  revoked_by_user_id?: number | null;
  created_by_user_id?: number | null;
  sent_at?: string | null;
  send_count?: number;
  last_error?: string | null;
};

export type OrgMember = {
  user_id: number;
  email: string;
  role: string;
  joined_at: string;
  is_you: boolean;
};

export type OrgAuditEvent = {
  id: number;
  organization_id: number;
  actor_user_id: number | null;
  action: string;
  subject_type: string | null;
  subject_id: number | null;
  meta: Record<string, unknown>;
  ip: string | null;
  user_agent: string | null;
  created_at: string;
};

export async function listConnections() {
  return request<{ items: ConnectionResponse[] }>("/connections");
}

export async function createConnection(payload: {
  advertiser_id?: number | null;
  platform: string;
  name?: string | null;
  credentials_json: Record<string, unknown>;
  auto_sync_enabled?: boolean;
  auto_sync_every_minutes?: number;
  auto_sync_window_days?: number;
}) {
  return request<ConnectionResponse>("/connections", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateConnection(connectionId: number, payload: {
  name?: string | null;
  auto_sync_enabled?: boolean;
  auto_sync_every_minutes?: number;
  auto_sync_window_days?: number;
}) {
  return request<ConnectionResponse>(`/connections/${connectionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function testConnection(connectionId: number) {
  return request<{ ok: boolean; message?: string | null; error_code?: string | null }>(`/connections/${connectionId}/check`, {
    method: "POST",
  });
}

export async function syncConnection(payload: { connection_id: number; date_from: string; date_to: string; force?: boolean }) {
  return request<{ id: number; status: string }>(`/connections/${payload.connection_id}/sync`, {
    method: "POST",
    body: JSON.stringify({
      date_from: payload.date_from,
      date_to: payload.date_to,
      force: payload.force ?? false,
    }),
  });
}

export async function getSyncRun(runId: number) {
  return request<{
    id: number;
    status: string;
    platform: string;
    run_type: string;
    connection_id: number | null;
    experiment_id: number | null;
    created_at: string;
    updated_at: string;
    error_text?: string | null;
  }>(`/sync-runs/${runId}`);
}

export async function listConnectionSyncRuns(connectionId: number) {
  return request<Array<{ id: number; status: string; run_type: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null }>>(
    `/sync-runs?connection_id=${connectionId}`
  );
}

export async function listConnectionSnapshots(payload: { connection_id: number; date_from?: string; date_to?: string }) {
  const params = new URLSearchParams();
  if (payload.date_from) {
    params.set("date_from", payload.date_from);
  }
  if (payload.date_to) {
    params.set("date_to", payload.date_to);
  }
  return request<{ items: Array<Record<string, unknown>> }>(
    `/connections/${payload.connection_id}/snapshots?${params.toString()}`
  );
}

export async function getMetricsTimeseries(payload: {
  date_from?: string;
  date_to?: string;
  connection_ids?: number[];
  metric_keys?: string[];
}) {
  const params = new URLSearchParams();
  if (payload.date_from) {
    params.set("date_from", payload.date_from);
  }
  if (payload.date_to) {
    params.set("date_to", payload.date_to);
  }
  if (payload.connection_ids && payload.connection_ids.length > 0) {
    params.set("connection_ids", payload.connection_ids.join(","));
  }
  if (payload.metric_keys && payload.metric_keys.length > 0) {
    params.set("metric_keys", payload.metric_keys.join(","));
  }
  return request<{
    date_from: string;
    date_to: string;
    series: Record<string, Array<{ date: string; value: number }>>;
    totals: Record<string, number>;
  }>(`/metrics/timeseries?${params.toString()}`);
}

export async function listJobRuns(payload: { connection_id?: number; limit?: number }) {
  const params = new URLSearchParams();
  if (payload.connection_id) {
    params.set("connection_id", String(payload.connection_id));
  }
  if (payload.limit) {
    params.set("limit", String(payload.limit));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request<{ items: JobRunItem[] }>(`/job-runs${suffix}`);
}

export async function getDashboardSummary(payload: { connection_id: number; date_from: string; date_to: string }) {
  const params = new URLSearchParams({
    connection_id: String(payload.connection_id),
    date_from: payload.date_from,
    date_to: payload.date_to,
  });
  return request<{
    totals: {
      impressions: number;
      clicks: number;
      spend: number;
      leads: number;
      purchases: number;
      revenue: number;
      ctr?: number | null;
      cpc?: number | null;
      cpm?: number | null;
      cpa?: number | null;
      roas?: number | null;
    };
    daily: Array<Record<string, unknown>>;
  }>(`/dashboard/summary?${params.toString()}`);
}

export async function getMetrics(payload: {
  connection_id: number;
  date_from: string;
  date_to: string;
  group_by?: string;
}) {
  const params = new URLSearchParams({
    connection_id: String(payload.connection_id),
    date_from: payload.date_from,
    date_to: payload.date_to,
    group_by: payload.group_by || "day",
  });
  return request<{ items: Array<Record<string, unknown>> }>(`/metrics?${params.toString()}`);
}

export async function registerUser(payload: { email: string; password: string }) {
  return request<UserMe>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function registerUserWithInvite(payload: { email: string; password: string; invite_token?: string | null }) {
  return request<UserMe>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function loginUser(payload: { email: string; password: string }) {
  return request<AuthToken>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function refreshToken(payload: { refresh_token: string }) {
  return request<{ access_token: string; token_type: string; expires_in: number }>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getMe() {
  return request<UserMe>("/auth/me");
}

export async function listOrgs() {
  return request<{ items: Organization[] }>("/orgs");
}

export async function createOrg(payload: { name: string }) {
  return request<Organization>("/orgs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getActiveOrg() {
  return request<Organization>("/orgs/active");
}

export async function switchOrg(payload: { organization_id: number }) {
  return request<Organization>(`/orgs/${payload.organization_id}/activate`, {
    method: "POST",
  });
}

export async function createInvite(orgId: number, payload: { email: string; role: string; expires_in_days?: number }) {
  return request<OrgInvite & { invite_token: string; join_url?: string | null }>(`/orgs/${orgId}/invites`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listInvites(orgId: number, status?: string) {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<{ items: OrgInvite[] }>(`/orgs/${orgId}/invites${suffix}`);
}

export async function acceptInvite(payload: { token: string }) {
  return request<{ organization_id: number; organization_name: string; role: string; active_organization_id?: number | null }>("/invites/accept", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function previewInvite(token: string) {
  const response = await fetch(`${apiBase}/invites/${encodeURIComponent(token)}/preview`, {
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await response.json();
  if (!response.ok && response.status !== 404) {
    const message = data?.error?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return data as {
    organization_id?: number | null;
    organization_name?: string | null;
    invited_email?: string | null;
    role?: string | null;
    expires_at?: string | null;
    status: string;
  };
}

export async function listMembers(orgId: number) {
  return request<OrgMember[]>(`/orgs/${orgId}/members`);
}

export async function listAuditEvents(orgId: number, payload?: { limit?: number; offset?: number }) {
  const params = new URLSearchParams();
  if (payload?.limit) params.set("limit", String(payload.limit));
  if (payload?.offset) params.set("offset", String(payload.offset));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request<{ items: OrgAuditEvent[]; total: number }>(`/orgs/${orgId}/audit${suffix}`);
}

export async function updateMemberRole(orgId: number, userId: number, payload: { role: string }) {
  return request<OrgMember>(`/orgs/${orgId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteMember(orgId: number, userId: number) {
  return request<void>(`/orgs/${orgId}/members/${userId}`, {
    method: "DELETE"
  });
}

export async function revokeInvite(orgId: number, inviteId: number) {
  return request<{ ok: boolean }>(`/orgs/${orgId}/invites/${inviteId}/revoke`, {
    method: "POST"
  });
}

export async function resendInvite(orgId: number, inviteId: number, payload?: { expires_in_days?: number }) {
  return request<{ id: number; sent_at?: string | null; send_count: number; last_error?: string | null }>(
    `/orgs/${orgId}/invites/${inviteId}/resend`,
    {
      method: "POST",
      body: JSON.stringify(payload ?? {})
    }
  );
}

export async function leaveOrg(orgId: number) {
  return request<{ active_organization_id: number | null }>(`/orgs/${orgId}/leave`, {
    method: "POST"
  });
}

export async function createPlan(payload: { url: string; business_description?: string | null; kpi?: string | null; internal_code?: string | null }) {
  return request<PlanResponse>("/plans", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listPlans() {
  return request<{ items: PlanResponse[] }>("/plans");
}

export async function getPlan(planId: number) {
  return request<PlanResponse>(`/plans/${planId}`);
}

export async function createExperiment(payload: { plan_id: number; budget: number; platforms?: string[] }) {
  return request<{ id: number; status: string }>("/experiments", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function startExperiment(experimentId: number) {
  return request<{ id: number; status: string }>(`/experiments/${experimentId}/start`, {
    method: "POST"
  });
}

export async function listExperiments() {
  return request<{ items: ExperimentListItem[] }>("/experiments");
}

export async function getExperiment(experimentId: number) {
  return request<ExperimentListItem & { platforms?: string[] }>(`/experiments/${experimentId}`);
}

export async function getExperimentReport(experimentId: number) {
  return request<ExperimentReport>(`/experiments/${experimentId}/report`);
}

export async function seedDev() {
  return request<{ advertiser_id: number; plan_id: number; experiment_id: number }>("/dev/seed", {
    method: "POST"
  });
}
