"use client";

import { useEffect, useMemo, useState } from "react";
import { getDashboardSummary, getMetrics, listConnections } from "../../lib/api";

type Connection = { id: number; platform: string; status: string };

export default function MetricsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [summary, setSummary] = useState<{
    impressions: number;
    clicks: number;
    spend: number;
    purchases?: number;
    revenue?: number;
    ctr?: number | null;
    cpc?: number | null;
    cpm?: number | null;
    cpa?: number | null;
    roas?: number | null;
  } | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const chartWidth = 640;
  const chartHeight = 180;

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 7);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await listConnections();
        setConnections(data.items);
      } catch (err) {
        setError((err as Error).message);
      }
    };
    load();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  const refresh = async () => {
    if (!selected) {
      setError("Select a connection");
      return;
    }
    setError(null);
    try {
      const metricsData = await getMetrics({
        connection_id: selected,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        group_by: "day",
      });
      setMetrics(metricsData.items);
      const summaryData = await getDashboardSummary({
        connection_id: selected,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
      });
      setSummary({
        impressions: summaryData.totals.impressions,
        clicks: summaryData.totals.clicks,
        spend: summaryData.totals.spend,
        purchases: summaryData.totals.purchases,
        revenue: summaryData.totals.revenue,
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

  const buildSeries = (key: string) => {
    if (metrics.length === 0) {
      return "";
    }
    const values = metrics.map((row) => Number(row[key] ?? 0));
    const maxVal = Math.max(...values, 1);
    return values
      .map((val, idx) => {
        const x = (idx / Math.max(values.length - 1, 1)) * chartWidth;
        const y = chartHeight - (val / maxVal) * chartHeight;
        return `${x},${y}`;
      })
      .join(" ");
  };

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Metrics</h1>
        {error && <div className="text-red-400">{error}</div>}
        <div className="grid gap-3 md:grid-cols-5">
          <select value={selected ?? ""} onChange={(event) => setSelected(Number(event.target.value) || null)}>
            <option value="">Select connection</option>
            {connections.map((c) => (
              <option key={c.id} value={c.id}>
                #{c.id} {c.platform} ({c.status})
              </option>
            ))}
          </select>
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          <button onClick={refresh}>Refresh</button>
        </div>
      </div>

      {summary && (
        <div className="card grid gap-3 md:grid-cols-3 text-sm">
          <div className="rounded bg-slate-900/60 p-3">Impressions: {summary.impressions}</div>
          <div className="rounded bg-slate-900/60 p-3">Clicks: {summary.clicks}</div>
          <div className="rounded bg-slate-900/60 p-3">Spend: {summary.spend}</div>
          <div className="rounded bg-slate-900/60 p-3">Purchases: {summary.purchases ?? 0}</div>
          <div className="rounded bg-slate-900/60 p-3">Revenue: {summary.revenue ?? 0}</div>
          <div className="rounded bg-slate-900/60 p-3">CTR: {summary.ctr ?? "n/a"}</div>
          <div className="rounded bg-slate-900/60 p-3">CPC: {summary.cpc ?? "n/a"}</div>
          <div className="rounded bg-slate-900/60 p-3">CPM: {summary.cpm ?? "n/a"}</div>
          <div className="rounded bg-slate-900/60 p-3">CPA: {summary.cpa ?? "n/a"}</div>
          <div className="rounded bg-slate-900/60 p-3">ROAS: {summary.roas ?? "n/a"}</div>
        </div>
      )}

      {metrics.length > 0 && (
        <div className="card space-y-3">
          <h2 className="text-lg font-semibold">Trend</h2>
          <svg width={chartWidth} height={chartHeight} className="w-full bg-slate-900/40 rounded">
            <polyline
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
              points={buildSeries("spend")}
            />
            <polyline
              fill="none"
              stroke="#a3e635"
              strokeWidth="2"
              points={buildSeries("clicks")}
            />
          </svg>
          <div className="text-xs text-slate-400">Blue: spend, Green: clicks</div>
        </div>
      )}

      <div className="card space-y-2">
        <h2 className="text-lg font-semibold">Daily</h2>
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
