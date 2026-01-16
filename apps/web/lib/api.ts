import { clearOrgId, clearRefreshToken, clearToken, getOrgId, getToken } from "./session";
import { ru } from "./ru";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ""; // Default to relative path
const apiBase = baseUrl ? `${baseUrl}/api` : "/api";

type ApiError = {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
};

const statusMessageMap: Record<number, string> = {
  400: "Некорректный запрос.",
  401: "Сессия истекла. Войдите заново.",
  403: "Недостаточно прав.",
  404: "Объект не найден.",
  409: "Синхронизация уже идёт. Попробуйте позже.",
  422: "Проверьте введённые данные.",
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
    // Use relative path for client-side requests to leverage Next.js proxy
    // If running on server (SSR), we might need absolute URL if not handled by Next.js internal fetch
    // But we use "use client" mostly.
    // If apiBase is relative (/api), fetch works in browser.

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
      // Only redirect if not already on login page to avoid loops
      if (!window.location.pathname.startsWith("/login")) {
        clearToken();
        clearRefreshToken();
        clearOrgId();
        window.location.href = "/login";
      }
      throw new Error("Требуется авторизация");
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

export type Campaign = {
  id: number;
  organization_id: number;
  platform: string;
  name: string;
  status: string;
  objective: string | null;
  budget_total: number | null;
  budget_daily: number | null;
  start_date: string | null;
  end_date: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type CampaignSummary = Campaign & {
  ad_groups_count: number;
  ads_count: number;
};

export type CampaignAdGroup = {
  id: number;
  campaign_id: number;
  name: string;
  status: string;
  bid_strategy: string | null;
  budget_daily: number | null;
  targeting_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CampaignAd = {
  id: number;
  ad_group_id: number;
  name: string;
  status: string;
  creative_json: Record<string, unknown>;
  landing_url: string | null;
  created_at: string;
  updated_at: string;
};

export type CampaignTree = Campaign & {
  ad_groups: Array<CampaignAdGroup & { ads: CampaignAd[] }>;
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

export type AutomationSettings = {
  organization_id: number;
  is_enabled: boolean;
  run_interval_minutes: number;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AutomationRun = {
  id: number;
  organization_id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  result_json: Record<string, unknown>;
  error_text: string | null;
  created_at: string;
};

export type AutomationAction = {
  id: number;
  organization_id: number;
  run_id: number | null;
  recommendation_id: number | null;
  action_type: string;
  status: string;
  title: string;
  description: string;
  payload_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
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

export type OrgProfile = {
  organization_id: number;
  legal_type: string | null;
  legal_name: string | null;
  inn: string | null;
  kpp: string | null;
  ogrn: string | null;
  ogrnip: string | null;
  legal_address: string | null;
  email_for_docs: string | null;
  phone: string | null;
  timezone: string;
  currency: string;
  created_at: string;
  updated_at: string;
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

export type DemoSeedResponse = {
  demo_user_email: string;
  demo_password: string | null;
  org_id: number;
  connection_ids: number[];
  period_from: string;
  period_to: string;
};

export type BuilderTreeAd = {
  id: number;
  ad_group_id: number;
  name: string;
  title?: string | null;
  text?: string | null;
  base_url?: string | null;
  utm_json: Record<string, any>;
  final_url?: string | null;
  status: string;
  external_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type BuilderTreeAdGroup = {
  id: number;
  campaign_id: number;
  name: string;
  status: string;
  external_id?: string | null;
  created_at: string;
  updated_at: string;
  ads: BuilderTreeAd[];
};

export type BuilderTreeCampaign = {
  id: number;
  experiment_id: number;
  platform: string;
  name: string;
  status: string;
  external_id?: string | null;
  created_at: string;
  updated_at: string;
  ad_groups: BuilderTreeAdGroup[];
};

export type BuilderTreeResponse = {
  campaigns: BuilderTreeCampaign[];
};

export type AdCampaignOut = {
  id: number;
  connection_id: number;
  platform: string;
  external_id: string;
  name: string;
  updated_at: string;
};

export type AdAdGroupOut = {
  id: number;
  connection_id: number;
  platform: string;
  external_id: string;
  campaign_external_id: string;
  name: string;
  updated_at: string;
};

export type AdAdOut = {
  id: number;
  connection_id: number;
  platform: string;
  external_id: string;
  ad_group_external_id: string;
  campaign_external_id: string;
  name: string;
  updated_at: string;
};

export type UtmSettingsOut = {
  organization_id: number;
  utm_source: string;
  utm_medium: string;
  utm_campaign_tpl: string;
  utm_content_tpl: string;
  utm_term_tpl?: string | null;
};

export type UtmBuildResponse = {
  final_url: string;
};

export type MetricsBreakdownItem = {
  dimension: string;
  id?: number | null;
  external_id: string;
  name?: string | null;
  platform: string;
  spend: number;
  impressions: number;
  clicks: number;
  leads: number;
  purchases: number;
  revenue: number;
  ctr?: number | null;
  cpc?: number | null;
  cpm?: number | null;
  cpa?: number | null;
  roas?: number | null;
};

export type MetricsBreakdownResponse = {
  items: MetricsBreakdownItem[];
  total: number;
};

export type RecommendationOut = {
  id: number;
  organization_id: number;
  connection_id?: number | null;
  subject_type: string;
  subject_id?: number | null;
  subject_name?: string | null;
  code: string;
  severity: string;
  title: string;
  description: string;
  action: string;
  meta_json: Record<string, any>;
  valid_from: string;
  valid_to: string;
  created_at: string;
  resolved_at?: string | null;
};

export type RecommendationListResponse = {
  items: RecommendationOut[];
  total: number;
};

export type ChangePlanItemOut = {
  id: number;
  subject_type: string;
  subject_id: number;
  action_type: string;
  params_json: Record<string, any>;
  status: string;
  error?: string | null;
};

export type ChangePlanOut = {
  id: number;
  organization_id: number;
  connection_id: number;
  title: string;
  status: string;
  date_from?: string | null;
  date_to?: string | null;
  created_at: string;
  applied_at?: string | null;
  items: ChangePlanItemOut[];
};

export type KpiTimeseriesItem = {
  date: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  impressions_index: number | null;
  clicks_index: number | null;
  conversions_index: number | null;
  spend_index: number | null;
};

export type KpiTimeseriesResponse = {
  items: KpiTimeseriesItem[];
  meta: {
    date_from: string;
    date_to: string;
    mode: string;
    platform: string | null;
    connection_ids: number[];
  };
};

export type KpiSummaryResponse = {
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  ctr: number | null;
  cpc: number | null;
  cpa: number | null;
  currency: string;
};

export type DashboardChannel = {
  key: string;
  title: string;
};

export type UnifiedDashboardResponse = {
  date_from: string;
  date_to: string;
  channel: string;
  available_channels: DashboardChannel[];
  series: Array<{
    date: string;
    raw: Record<string, number>;
    norm: Record<string, number>;
    index: number;
  }>;
  totals: Record<string, number>;
  kpi: Record<string, number | null>;
};

export async function listConnections() {
  return request<{ items: ConnectionResponse[] }>("/connections");
}

export async function listCampaigns(params?: { platform?: string; status?: string; search?: string }) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  const q = new URLSearchParams();
  if (params?.platform) q.set("platform", params.platform);
  if (params?.status) q.set("status", params.status);
  if (params?.search) q.set("search", params.search);
  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<{ items: Campaign[]; total: number }>(`/orgs/${orgId}/campaigns${suffix}`);
}

export async function createCampaign(payload: {
  platform: string;
  name: string;
  status?: string;
  objective?: string | null;
  budget_total?: number | null;
  budget_daily?: number | null;
  start_date?: string | null;
  end_date?: string | null;
}) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<Campaign>(`/orgs/${orgId}/campaigns`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCampaign(campaignId: number) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<CampaignSummary>(`/orgs/${orgId}/campaigns/${campaignId}`);
}

export async function getCampaignTree(campaignId: number) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<{ campaign: CampaignTree }>(`/orgs/${orgId}/campaigns/${campaignId}/tree`);
}

export async function updateCampaign(campaignId: number, payload: Partial<Campaign>) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<Campaign>(`/orgs/${orgId}/campaigns/${campaignId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCampaign(campaignId: number) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<{ ok: boolean }>(`/orgs/${orgId}/campaigns/${campaignId}`, {
    method: "DELETE",
  });
}

export async function publishCampaign(campaignId: number, action: "publish" | "pause" | "archive") {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<Campaign>(`/orgs/${orgId}/campaigns/${campaignId}/${action}`, {
    method: "POST",
  });
}

export async function listCampaignEvents(campaignId: number) {
  const orgId = getOrgId();
  if (!orgId) throw new Error(ru.messages.selectOrg);
  return request<Array<{
    id: number;
    entity_type: string;
    entity_id: number;
    action: string;
    payload_json: Record<string, unknown>;
    created_at: string;
    created_by_user_id: number | null;
  }>>(`/orgs/${orgId}/campaigns/${campaignId}/events`);
}

export async function listCampaignAdGroups(params?: { campaign_id?: number }) {
  const q = new URLSearchParams();
  if (params?.campaign_id) q.set("campaign_id", String(params.campaign_id));
  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<{ items: CampaignAdGroup[]; total: number }>(`/ad-groups${suffix}`);
}

export async function createCampaignAdGroup(payload: { campaign_id: number; name: string; status?: string; bid_strategy?: string | null; budget_daily?: number | null; targeting_json?: Record<string, unknown> }) {
  return request<CampaignAdGroup>("/ad-groups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCampaignAdGroup(groupId: number, payload: Partial<CampaignAdGroup>) {
  return request<CampaignAdGroup>(`/ad-groups/${groupId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCampaignAdGroup(groupId: number) {
  return request<{ ok: boolean }>(`/ad-groups/${groupId}`, {
    method: "DELETE",
  });
}

export async function listCampaignAds(params?: { ad_group_id?: number }) {
  const q = new URLSearchParams();
  if (params?.ad_group_id) q.set("ad_group_id", String(params.ad_group_id));
  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<{ items: CampaignAd[]; total: number }>(`/ads${suffix}`);
}

export async function createCampaignAd(payload: { ad_group_id: number; name: string; status?: string; creative_json?: Record<string, unknown>; landing_url?: string | null }) {
  return request<CampaignAd>("/ads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCampaignAd(adId: number, payload: Partial<CampaignAd>) {
  return request<CampaignAd>(`/ads/${adId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCampaignAd(adId: number) {
  return request<{ ok: boolean }>(`/ads/${adId}`, {
    method: "DELETE",
  });
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
    items: Array<{
      date: string;
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
    }>;
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

export async function getAutomationSettings() {
  return request<AutomationSettings>("/automation/settings");
}

export async function updateAutomationSettings(payload: Partial<AutomationSettings>) {
  return request<AutomationSettings>("/automation/settings", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function runAutomation() {
  return request<AutomationRun>("/automation/run", { method: "POST" });
}

export async function listAutomationRuns(payload: { status?: string; limit?: number; offset?: number } = {}) {
  const params = new URLSearchParams();
  if (payload.status) {
    params.set("status", payload.status);
  }
  if (payload.limit) {
    params.set("limit", String(payload.limit));
  }
  if (payload.offset) {
    params.set("offset", String(payload.offset));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request<AutomationRun[]>(`/automation/runs${suffix}`);
}

export async function listAutomationActions(payload: { status?: string; limit?: number; offset?: number } = {}) {
  const params = new URLSearchParams();
  if (payload.status) {
    params.set("status", payload.status);
  }
  if (payload.limit) {
    params.set("limit", String(payload.limit));
  }
  if (payload.offset) {
    params.set("offset", String(payload.offset));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request<AutomationAction[]>(`/automation/actions${suffix}`);
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

export async function getOrgProfile() {
  return request<OrgProfile>("/settings/org-profile");
}

export async function updateOrgProfile(payload: Partial<OrgProfile>) {
  return request<OrgProfile>("/settings/org-profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
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
  if (typeof window === "undefined") {
    // Server-side: return empty/mock or throw to avoid fetch
    return { status: "unknown" } as any;
  }
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

export async function demoSeed() {
  return request<DemoSeedResponse>("/dev/demo/seed", {
    method: "POST"
  });
}

// --- Builder API ---

export async function listBuilderCampaigns(experimentId: number) {
  return request<any[]>(`/experiments/${experimentId}/builder/campaigns`);
}

export async function createBuilderCampaign(experimentId: number, payload: { name: string; platform: string; status: string }) {
  return request<any>(`/experiments/${experimentId}/builder/campaigns`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateBuilderCampaign(campaignId: number, payload: { name?: string; status?: string }) {
  return request<any>(`/builder/campaigns/${campaignId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteBuilderCampaign(campaignId: number) {
  return request<void>(`/builder/campaigns/${campaignId}`, {
    method: "DELETE"
  });
}

export async function listBuilderAdGroups(campaignId: number) {
  return request<any[]>(`/builder/campaigns/${campaignId}/ad-groups`);
}

export async function createBuilderAdGroup(campaignId: number, payload: { name: string; status: string }) {
  return request<any>(`/builder/campaigns/${campaignId}/ad-groups`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateBuilderAdGroup(groupId: number, payload: { name?: string; status?: string }) {
  return request<any>(`/builder/ad-groups/${groupId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteBuilderAdGroup(groupId: number) {
  return request<void>(`/builder/ad-groups/${groupId}`, {
    method: "DELETE"
  });
}

export async function listBuilderAds(groupId: number) {
  return request<any[]>(`/builder/ad-groups/${groupId}/ads`);
}

export async function createBuilderAd(groupId: number, payload: { name: string; status: string; title?: string; text?: string; base_url?: string; utm_json?: any }) {
  return request<any>(`/builder/ad-groups/${groupId}/ads`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateBuilderAd(adId: number, payload: { name?: string; status?: string; title?: string; text?: string; base_url?: string; utm_json?: any }) {
  return request<any>(`/builder/ads/${adId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteBuilderAd(adId: number) {
  return request<void>(`/builder/ads/${adId}`, {
    method: "DELETE"
  });
}

export async function getBuilderTree(experimentId: number) {
  return request<BuilderTreeResponse>(`/experiments/${experimentId}/builder/tree`);
}

// --- Catalog API ---

export async function listCatalogCampaigns(connectionId: number, params?: { query?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams();
  if (params?.query) q.set("query", params.query);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  return request<AdCampaignOut[]>(`/connections/${connectionId}/campaigns?${q.toString()}`);
}

export async function listCatalogAdGroups(connectionId: number, params?: { query?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams();
  if (params?.query) q.set("query", params.query);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  return request<AdAdGroupOut[]>(`/connections/${connectionId}/ad-groups?${q.toString()}`);
}

export async function listCatalogAds(connectionId: number, params?: { query?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams();
  if (params?.query) q.set("query", params.query);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  return request<AdAdOut[]>(`/connections/${connectionId}/ads?${q.toString()}`);
}

export async function buildUtmLink(payload: { url: string; platform?: string; campaign_external_id?: string; ad_group_external_id?: string; ad_external_id?: string }) {
  return request<UtmBuildResponse>("/utm/build", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getMetricsBreakdown(payload: {
  date_from: string;
  date_to: string;
  dimension: string;
  connection_ids?: number[];
  limit?: number;
  offset?: number;
  query?: string;
  order_by?: string;
}) {
  const params = new URLSearchParams({
    date_from: payload.date_from,
    date_to: payload.date_to,
    dimension: payload.dimension,
  });
  if (payload.connection_ids && payload.connection_ids.length > 0) {
    params.set("connection_ids", payload.connection_ids.join(","));
  }
  if (payload.limit) params.set("limit", String(payload.limit));
  if (payload.offset) params.set("offset", String(payload.offset));
  if (payload.query) params.set("query", payload.query);
  if (payload.order_by) params.set("order_by", payload.order_by);

  return request<MetricsBreakdownResponse>(`/metrics/breakdown?${params.toString()}`);
}

// --- Recommendations API ---

export async function listRecommendations(params: { date_from: string; date_to: string; connection_id?: number; severity?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams({
    date_from: params.date_from,
    date_to: params.date_to,
  });
  if (params.connection_id) q.set("connection_id", String(params.connection_id));
  if (params.severity) q.set("severity", params.severity);
  if (params.limit) q.set("limit", String(params.limit));
  if (params.offset) q.set("offset", String(params.offset));
  return request<RecommendationListResponse>(`/recommendations?${q.toString()}`);
}

export async function recomputeRecommendations(payload: { date_from: string; date_to: string; connection_ids?: number[] }) {
  return request<{ status: string; created: number; updated: number }>("/recommendations/recompute", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function resolveRecommendation(recoId: number) {
  return request<{ status: string }>(`/recommendations/${recoId}/resolve`, {
    method: "POST"
  });
}

// --- Change Plans API ---

export async function listChangePlans(params: { connection_id?: number; status?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams();
  if (params.connection_id) q.set("connection_id", String(params.connection_id));
  if (params.status) q.set("status", params.status);
  if (params.limit) q.set("limit", String(params.limit));
  if (params.offset) q.set("offset", String(params.offset));
  return request<ChangePlanOut[]>(`/change-plans?${q.toString()}`);
}

export async function createChangePlan(payload: { connection_id: number; title: string; date_from?: string; date_to?: string }) {
  return request<ChangePlanOut>("/change-plans", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getChangePlan(planId: number) {
  return request<ChangePlanOut>(`/change-plans/${planId}`);
}

export async function addChangePlanItem(planId: number, payload: { subject_type: string; subject_id: number; action_type: string; params: any }) {
  return request<ChangePlanItemOut>(`/change-plans/${planId}/items`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function markPlanReady(planId: number) {
  return request<{ status: string }>(`/change-plans/${planId}/ready`, {
    method: "POST"
  });
}

export async function applyPlan(planId: number) {
  return request<{ status: string }>(`/change-plans/${planId}/apply`, {
    method: "POST"
  });
}

export async function getKpiTimeseries(payload: {
  date_from: string;
  date_to: string;
  connection_ids?: number[];
  platform?: string;
  mode?: "index" | "absolute";
}): Promise<KpiTimeseriesResponse> {
  const params = new URLSearchParams({
    date_from: payload.date_from,
    date_to: payload.date_to,
  });
  if (payload.connection_ids && payload.connection_ids.length > 0) {
    params.set("connection_ids", payload.connection_ids.join(","));
  }
  if (payload.platform) {
    params.set("platform", payload.platform);
  }
  if (payload.mode) {
    params.set("mode", payload.mode);
  }
  return request<KpiTimeseriesResponse>(`/dashboard/kpi-timeseries?${params.toString()}`);
}

export async function getKpiSummary(payload: {
  date_from: string;
  date_to: string;
  connection_ids?: number[];
  platform?: string;
}): Promise<KpiSummaryResponse> {
  const params = new URLSearchParams({
    date_from: payload.date_from,
    date_to: payload.date_to,
  });
  if (payload.connection_ids && payload.connection_ids.length > 0) {
    params.set("connection_ids", payload.connection_ids.join(","));
  }
  if (payload.platform) {
    params.set("platform", payload.platform);
  }
  return request<KpiSummaryResponse>(`/dashboard/kpi-summary?${params.toString()}`);
}

export async function dashboardChannels(): Promise<DashboardChannel[]> {
  return request<DashboardChannel[]>("/dashboard/channels");
}

export async function dashboardUnifiedTimeseries(payload: {
  date_from: string;
  date_to: string;
  channel: string;
  connection_ids?: number[];
}): Promise<UnifiedDashboardResponse> {
  const params = new URLSearchParams({
    date_from: payload.date_from,
    date_to: payload.date_to,
    channel: payload.channel,
  });
  if (payload.connection_ids && payload.connection_ids.length > 0) {
    params.set("connection_ids", payload.connection_ids.join(","));
  }
  return request<UnifiedDashboardResponse>(`/dashboard/unified-timeseries?${params.toString()}`);
}

// --- Magic API ---

export type MagicRun = {
  id: number;
  organization_id: number;
  status: 'pending' | 'running' | 'success' | 'failed';
  input_json: any;
  result_json: any;
  error?: string;
  created_at: string;
};

export const MagicApi = {
  createRun: (data: { landing_url: string; description?: string }) =>
    request<MagicRun>('/magic/runs', { method: 'POST', body: JSON.stringify(data) }),

  getRun: (id: number) =>
    request<MagicRun>(`/magic/runs/${id}`),
};

// --- Drafts API ---

export type DraftAd = {
  id: number;
  ad_group_id: number;
  title?: string;
  text?: string;
  landing_url?: string;
  payload_json?: any;
};

export type DraftAdGroup = {
  id: number;
  campaign_id: number;
  name: string;
  ads: DraftAd[];
};

export type DraftCampaign = {
  id: number;
  name: string;
  platform: string;
  status: string;
  magic_run_id?: number;
  ad_groups: DraftAdGroup[];
  created_at: string;
};

export const DraftsApi = {
  list: () => request<DraftCampaign[]>('/drafts/'),
  get: (id: number) => request<DraftCampaign>(`/drafts/${id}`),
  delete: (id: number) => request<void>(`/drafts/${id}`, { method: 'DELETE' }),
  publish: (id: number) => request<{ ok: boolean; external_id: string }>(`/drafts/${id}/publish`, { method: 'POST' }),
};


// --- Billing API ---

export type BillingAccount = {
  id: number;
  balance: number;
  status: string;
};

export const BillingApi = {
  getBalance: () => request<BillingAccount>('/billing/balance'),
  topTop: (amount: number) => request<BillingAccount>('/billing/topup', { method: 'POST', body: JSON.stringify({ amount }) }),
  invoice: (amount: number) => request<{ url: string }>('/billing/invoice', { method: 'POST', body: JSON.stringify({ amount }) }),
};



