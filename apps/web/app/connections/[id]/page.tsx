"use client";

import { useEffect, useMemo, useState } from "react";
import { getDashboardSummary, listConnectionSnapshots, listConnectionSyncRuns, listJobRuns, syncConnection } from "../../../lib/api";

type Run = { id: number; status: string; run_type: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null };
type JobRun = { id: number; job_type: string; status: string; created_at: string; result_json?: Record<string, unknown> | null; error_text?: string | null };

export default function ConnectionDetailPage({ params }: { params: { id: string } }) {
  const connectionId = Number(params.id);
  const [runs, setRuns] = useState<Run[]>([]);
  const [metrics, setMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [summary, setSummary] = useState<{
    impressions: number;
    clicks: number;
    spend: number;
    ctr?: number | null;
    cpc?: number | null;
    cpm?: number | null;
    cpa?: number | null;
    roas?: number | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [jobRuns, setJobRuns] = useState<JobRun[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 13);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  const load = async () => {
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const runData = await listConnectionSyncRuns(connectionId);
      setRuns(runData);
      const jobData = await listJobRuns({ connection_id: connectionId, limit: 20 });
      setJobRuns(jobData.items);
      const snapshotsData = await listConnectionSnapshots({
        connection_id: connectionId,
        date_from: defaultDateRange.from,
        date_to: defaultDateRange.to,
      });
      setMetrics(snapshotsData.items);
      const summaryData = await getDashboardSummary({
        connection_id: connectionId,
        date_from: defaultDateRange.from,
        date_to: defaultDateRange.to,
      });
      setSummary({
        impressions: summaryData.totals.impressions,
        clicks: summaryData.totals.clicks,
        spend: summaryData.totals.spend,
        ctr: summaryData.totals.ctr ?? null,
        cpc: summaryData.totals.cpc ?? null,
        cpm: summaryData.totals.cpm ?? null,
        cpa: summaryData.totals.cpa ?? null,
        roas: summaryData.totals.roas ?? null,
      });
      setDateFrom(defaultDateRange.from);
      setDateTo(defaultDateRange.to);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const hasActive = runs.some((run) => run.status === "queued" || run.status === "running");
    if (!Number.isFinite(connectionId) || !hasActive) {
      return;
    }
    const interval = setInterval(async () => {
      try {
      const runData = await listConnectionSyncRuns(connectionId);
      setRuns(runData);
      const jobData = await listJobRuns({ connection_id: connectionId, limit: 20 });
      setJobRuns(jobData.items);
    } catch (err) {
      setError((err as Error).message);
    }
  }, 2500);
    return () => clearInterval(interval);
  }, [connectionId, runs]);

  const handleSync = async () => {
    setError(null);
    setNotice(null);
    try {
      const run = await syncConnection({
        connection_id: connectionId,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
      });
      setNotice(`Sync queued (run #${run.id})`);
      const runData = await listConnectionSyncRuns(connectionId);
      setRuns(runData);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const refreshMetrics = async () => {
    setError(null);
    try {
      const snapshotsData = await listConnectionSnapshots({
        connection_id: connectionId,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
      });
      setMetrics(snapshotsData.items);
      const summaryData = await getDashboardSummary({
        connection_id: connectionId,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
      });
      setSummary({
        impressions: summaryData.totals.impressions,
        clicks: summaryData.totals.clicks,
        spend: summaryData.totals.spend,
        ctr: summaryData.totals.ctr ?? null,
        cpc: summaryData.totals.cpc ?? null,
        cpm: summaryData.totals.cpm ?? null,
        cpa: summaryData.totals.cpa ?? null,
        roas: summaryData.totals.roas ?? null,
      });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    if (Number.isFinite(connectionId)) {
      load();
    }
  }, [connectionId]);

  return (
    <div className="space-y-6">
      <div className="card space-y-2">
        <h1 className="text-xl font-semibold">Connection #{connectionId}</h1>
        <p className="text-slate-400 text-sm">Last 7 days summary</p>
        {error && <div className="text-red-400">{error}</div>}
        {notice && <div className="text-green-400">{notice}</div>}
        {loading && <div className="text-slate-400 text-sm">Loading…</div>}
        {summary && (
          <div className="grid gap-3 md:grid-cols-3 text-sm">
            <div className="rounded bg-slate-900/60 p-3">Impressions: {summary.impressions}</div>
            <div className="rounded bg-slate-900/60 p-3">Clicks: {summary.clicks}</div>
            <div className="rounded bg-slate-900/60 p-3">Spend: {summary.spend}</div>
            <div className="rounded bg-slate-900/60 p-3">CTR: {summary.ctr ?? "n/a"}</div>
            <div className="rounded bg-slate-900/60 p-3">CPC: {summary.cpc ?? "n/a"}</div>
            <div className="rounded bg-slate-900/60 p-3">CPM: {summary.cpm ?? "n/a"}</div>
            <div className="rounded bg-slate-900/60 p-3">CPA: {summary.cpa ?? "n/a"}</div>
            <div className="rounded bg-slate-900/60 p-3">ROAS: {summary.roas ?? "n/a"}</div>
          </div>
        )}
        <div className="grid gap-3 md:grid-cols-4 text-sm">
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          <button onClick={handleSync}>Sync</button>
          <button onClick={refreshMetrics} className="bg-slate-700 hover:bg-slate-600">
            Refresh metrics
          </button>
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Sync runs</h2>
        <div className="grid gap-2 text-sm">
          {runs.map((run) => (
            <div key={run.id} className="grid grid-cols-5 gap-2 border-b border-slate-800 pb-2">
              <span>#{run.id}</span>
              <span>{run.status}</span>
              <span>{new Date(run.created_at).toLocaleString()}</span>
              <span>
                {run.result_json && "inserted" in run.result_json
                  ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                  : "-"}
              </span>
              <span className="text-xs text-slate-400">
                {run.error_text ? String(run.error_text).slice(0, 80) : ""}
              </span>
            </div>
          ))}
          {runs.length === 0 && <div className="text-slate-400">No sync runs yet.</div>}
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Job runs</h2>
        <div className="grid gap-2 text-sm">
          {jobRuns.map((job) => (
            <div key={job.id} className="grid grid-cols-4 gap-2 border-b border-slate-800 pb-2">
              <span>#{job.id}</span>
              <span>{job.job_type}</span>
              <span>{job.status}</span>
              <span className="text-xs text-slate-400">
                {job.error_text ? String(job.error_text).slice(0, 80) : ""}
              </span>
            </div>
          ))}
          {jobRuns.length === 0 && <div className="text-slate-400">No job runs yet.</div>}
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Daily metrics</h2>
        <div className="grid gap-2 text-sm">
          {metrics.map((row, idx) => (
            <div key={idx} className="grid grid-cols-4 gap-2 border-b border-slate-800 pb-2">
              <span>{String(row.date || "")}</span>
              <span>impressions: {String(row.impressions || 0)}</span>
              <span>clicks: {String(row.clicks || 0)}</span>
              <span>spend: {String(row.spend || 0)}</span>
            </div>
          ))}
          {metrics.length === 0 && <div className="text-slate-400">No metrics yet.</div>}
        </div>
      </div>
    </div>
  );
}
