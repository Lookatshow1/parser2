"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  createConnection,
  listConnections,
  testConnection,
  syncConnection,
  listConnectionSyncRuns,
  getMetrics,
  ConnectionResponse,
} from "../../lib/api";

const platforms = ["stub", "yandex", "ozon", "vk"];

export default function ConnectionsPage() {
  const [items, setItems] = useState<ConnectionResponse[]>([]);
  const [platform, setPlatform] = useState("stub");
  const [credentialsJson, setCredentialsJson] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedConnectionId, setSelectedConnectionId] = useState<number | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [syncRuns, setSyncRuns] = useState<Array<{ id: number; status: string; run_type: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null }>>([]);
  const [metrics, setMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 7);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  const load = async () => {
    try {
      const data = await listConnections();
      setItems(data.items);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    load();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  useEffect(() => {
    if (!selectedConnectionId) {
      return;
    }
    const hasActive = syncRuns.some((run) => run.status === "queued" || run.status === "running");
    if (!hasActive) {
      return;
    }
    const interval = setInterval(() => {
      refreshSyncRuns(selectedConnectionId);
      refreshMetrics(selectedConnectionId);
    }, 2500);
    return () => clearInterval(interval);
  }, [selectedConnectionId, syncRuns]);

  const handleCreate = async () => {
    setError(null);
    setNotice(null);
    try {
      const credentials = JSON.parse(credentialsJson);
      await createConnection({ platform, credentials_json: credentials });
      setNotice("Connection created");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleTest = async (connectionId: number) => {
    setError(null);
    setNotice(null);
    try {
      const result = await testConnection(connectionId);
      if (result.ok) {
        setNotice(result.message ? `Connection OK: ${result.message}` : "Connection OK");
      } else {
        setError(result.message || result.error_code || "Connection failed");
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const refreshSyncRuns = async (connectionId: number) => {
    setLoadingRuns(true);
    try {
      const data = await listConnectionSyncRuns(connectionId);
      setSyncRuns(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingRuns(false);
    }
  };

  const refreshMetrics = async (connectionId: number) => {
    setLoadingMetrics(true);
    try {
      const data = await getMetrics({
        connection_id: connectionId,
        date_from: dateFrom,
        date_to: dateTo,
        group_by: "day",
      });
      setMetrics(data.items);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleSync = async () => {
    if (!selectedConnectionId) {
      setError("Select a connection to sync");
      return;
    }
    setError(null);
    setNotice(null);
    try {
      const run = await syncConnection({
        connection_id: selectedConnectionId,
        date_from: dateFrom,
        date_to: dateTo,
      });
      setNotice(`Sync queued (run #${run.id})`);
      await refreshSyncRuns(selectedConnectionId);
      await refreshMetrics(selectedConnectionId);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-xl font-semibold mb-4">Connections</h1>
        {error && <div className="text-red-400 mb-2">{error}</div>}
        {notice && <div className="text-green-400 mb-2">{notice}</div>}
        <div className="grid gap-3 md:grid-cols-3">
          <select value={platform} onChange={(event) => setPlatform(event.target.value)}>
            {platforms.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <input
            value={credentialsJson}
            onChange={(event) => setCredentialsJson(event.target.value)}
            placeholder='{"token":"..."}'
          />
          <div className="flex gap-2">
            <button onClick={handleCreate}>Create</button>
            <button
              onClick={() => {
                if (!selectedConnectionId) {
                  setError("Select a connection to test");
                  return;
                }
                handleTest(selectedConnectionId);
              }}
              className="bg-slate-700 hover:bg-slate-600"
            >
              Test
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Existing connections</h2>
        <div className="grid gap-2 text-sm">
          {items.map((item) => (
            <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
              <span>#{item.id}</span>
              <span>{item.platform}</span>
              <span>{item.status}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setSelectedConnectionId(item.id);
                    refreshSyncRuns(item.id);
                    refreshMetrics(item.id);
                  }}
                  className="bg-slate-700 hover:bg-slate-600 text-xs px-3 py-1 rounded"
                >
                  View
                </button>
                <Link
                  href={`/connections/${item.id}`}
                  className="bg-slate-800 hover:bg-slate-700 text-xs px-3 py-1 rounded"
                >
                  Details
                </Link>
                <button
                  onClick={() => handleTest(item.id)}
                  className="bg-slate-700 hover:bg-slate-600 text-xs px-3 py-1 rounded"
                >
                  Test
                </button>
              </div>
            </div>
          ))}
          {items.length === 0 && <div className="text-slate-400">No connections yet.</div>}
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="text-lg font-semibold">Sync runs</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <input
            type="number"
            placeholder="Connection ID"
            value={selectedConnectionId ?? ""}
            onChange={(event) => setSelectedConnectionId(Number(event.target.value) || null)}
          />
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        </div>
        <div className="flex gap-2">
          <button onClick={handleSync}>Run sync</button>
          {selectedConnectionId && (
            <>
              <button onClick={() => refreshSyncRuns(selectedConnectionId)} className="bg-slate-700 hover:bg-slate-600">
                Refresh runs
              </button>
              <button onClick={() => refreshMetrics(selectedConnectionId)} className="bg-slate-700 hover:bg-slate-600">
                Refresh metrics
              </button>
            </>
          )}
        </div>
        {loadingRuns ? (
          <div className="text-slate-400 text-sm">Loading sync runs…</div>
        ) : (
          <div className="grid gap-2 text-sm">
            {syncRuns.map((run) => (
              <div key={run.id} className="grid grid-cols-5 gap-2 border-b border-slate-800 pb-2">
                <span>#{run.id}</span>
                <span>{run.run_type}</span>
                <span>{run.status}</span>
                <span>{new Date(run.created_at).toLocaleString()}</span>
                <span>
                  {run.result_json && "inserted" in run.result_json
                    ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                    : run.error_text
                    ? String(run.error_text).slice(0, 80)
                    : "-"}
                </span>
              </div>
            ))}
            {syncRuns.length === 0 && <div className="text-slate-400">No sync runs yet.</div>}
          </div>
        )}
      </div>

      <div className="card space-y-4">
        <h2 className="text-lg font-semibold">Metrics</h2>
        {loadingMetrics ? (
          <div className="text-slate-400 text-sm">Loading metrics…</div>
        ) : (
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
        )}
      </div>
    </div>
  );
}
