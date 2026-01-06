"use client";

import { useEffect, useMemo, useState } from "react";
import { listConnections, listConnectionSyncRuns, syncConnection } from "../../lib/api";

type Connection = { id: number; platform: string; status: string };

export default function SyncRunsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [runs, setRuns] = useState<Array<{ id: number; status: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 3);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  const loadConnections = async () => {
    try {
      const data = await listConnections();
      setConnections(data.items);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const loadRuns = async (connectionId: number) => {
    try {
      const data = await listConnectionSyncRuns(connectionId);
      setRuns(data);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    loadConnections();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  useEffect(() => {
    if (selected) {
      loadRuns(selected);
    }
  }, [selected]);

  useEffect(() => {
    if (!selected) {
      return;
    }
    const hasActive = runs.some((run) => run.status === "queued" || run.status === "running");
    if (!hasActive) {
      return;
    }
    const interval = setInterval(() => loadRuns(selected), 2500);
    return () => clearInterval(interval);
  }, [runs, selected]);

  const handleSync = async () => {
    if (!selected) {
      setError("Select a connection");
      return;
    }
    setError(null);
    setNotice(null);
    try {
      const run = await syncConnection({
        connection_id: selected,
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
      });
      setNotice(`Sync queued: #${run.id}`);
      await loadRuns(selected);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Sync runs</h1>
        {error && <div className="text-red-400">{error}</div>}
        {notice && <div className="text-green-400">{notice}</div>}
        <div className="grid gap-3 md:grid-cols-4">
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
          <button onClick={handleSync}>Run sync</button>
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Runs</h2>
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
          {runs.length === 0 && <div className="text-slate-400">No runs yet.</div>}
        </div>
      </div>
    </div>
  );
}
