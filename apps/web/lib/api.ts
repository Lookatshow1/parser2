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
  const response = await fetch(`${apiBase}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {})
    },
    ...options
  });

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
  project_id: number | null;
  total_budget: number | null;
};

export type ExperimentReport = {
  experiment_id: number;
  status: string;
  rounds: Array<{ round_index: number; budget_plan: Record<string, number>; started_at: string | null; ended_at: string | null }>;
  metrics: Array<{ date: string; platform: string; impressions: number; clicks: number; spend: number }>;
};

export async function getConnections() {
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
  return request<{ ok: boolean }>(`/connections/${connectionId}/test`, {
    method: "POST",
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

export async function startExperiment(payload: { plan_id: number; budget: number; platforms?: string[] }) {
  return request<{ id: number; status: string }>("/experiments", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listExperiments() {
  return request<{ items: ExperimentListItem[] }>("/experiments");
}

export async function getExperimentReport(id: number) {
  return request<ExperimentReport>(`/experiments/${id}/report`);
}

export async function startExperimentRun(id: number) {
  return request<{ id: number; status: string }>(`/experiments/${id}/start`, {
    method: "POST"
  });
}
