const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const apiBase = `${baseUrl}/api`;

type ApiError = {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {})
      },
      ...options
    });
  } catch {
    throw new Error("Backend is unavailable. Check API base URL and server status.");
  }

  if (!response.ok) {
    let error: ApiError | null = null;
    try {
      error = (await response.json()) as ApiError;
    } catch {
      error = null;
    }
    const message = error?.error?.message || `Request failed with status ${response.status}`;
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

export async function listConnections() {
  return request<{ items: ConnectionResponse[] }>("/connections");
}

export async function createConnection(payload: {
  advertiser_id?: number | null;
  platform: string;
  credentials_json: Record<string, unknown>;
}) {
  return request<ConnectionResponse>("/connections", {
    method: "POST",
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
    totals: { impressions: number; clicks: number; spend: number; leads: number; purchases: number; revenue: number };
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
