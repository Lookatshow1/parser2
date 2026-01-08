"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getMetricsTimeseries, listConnections, ConnectionResponse } from "../../lib/api";
import { getOrgId, getToken } from "../../lib/session";

type SeriesPoint = { date: string; value: number };

const metricOptions = ["spend", "clicks", "impressions"] as const;

export default function DashboardPage() {
  const [metric, setMetric] = useState<(typeof metricOptions)[number]>("spend");
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [totals, setTotals] = useState<Record<string, number>>({});
  const [connections, setConnections] = useState<ConnectionResponse[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
    setError(null);
    setLoading(true);
    try {
      const connectionData = await listConnections();
      setConnections(connectionData.items);
      const data = await getMetricsTimeseries({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        metric_keys: metricOptions.slice(),
      });
      const metricSeries = data.series[metric] ?? [];
      setSeries(metricSeries);
      setTotals(data.totals || {});
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  useEffect(() => {
    if (dateFrom && dateTo) {
      load();
    }
  }, [metric, dateFrom, dateTo]);

  const totalValue = totals[metric] ?? 0;

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <div className="text-xs text-slate-400">Org: {getOrgId() || "not selected"}</div>
        </div>
        {!getToken() && <div className="text-yellow-400">Login required. Go to Login page.</div>}
        {getToken() && !getOrgId() && <div className="text-yellow-400">Select organization first.</div>}
        {error && <div className="text-red-400">{error}</div>}
        {loading && <div className="text-slate-400 text-sm">Loading…</div>}
        <div className="grid gap-3 md:grid-cols-4 text-sm">
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          <select value={metric} onChange={(event) => setMetric(event.target.value as typeof metric)}>
            {metricOptions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <button onClick={load}>Refresh</button>
        </div>
      </div>

      <div className="card space-y-3">
        <div className="grid gap-3 md:grid-cols-3 text-sm">
          <div className="rounded bg-slate-900/60 p-3">
            Total {metric}: {totalValue}
          </div>
          <div className="rounded bg-slate-900/60 p-3">
            Points: {series.length}
          </div>
          <div className="rounded bg-slate-900/60 p-3">
            Date range: {dateFrom} → {dateTo}
          </div>
        </div>
        {series.length === 0 ? (
          <div className="text-slate-400 text-sm">No data for the selected period.</div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series}>
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Connections</h2>
        <div className="grid gap-2 text-sm">
          {connections.map((item) => (
            <div key={item.id} className="grid grid-cols-5 gap-2 border-b border-slate-800 pb-2">
              <span>#{item.id}</span>
              <span>{item.platform}</span>
              <span>{item.last_sync_status ?? "n/a"}</span>
              <span className="text-xs text-slate-400">{item.last_sync_finished_at ?? "-"}</span>
              <Link
                className="text-blue-300 hover:text-blue-200"
                href={`/connections/${item.id}`}
              >
                Open
              </Link>
            </div>
          ))}
          {connections.length === 0 && <div className="text-slate-400">No connections yet.</div>}
        </div>
      </div>
    </div>
  );
}
