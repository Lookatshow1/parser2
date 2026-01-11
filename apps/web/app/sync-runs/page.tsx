"use client";
export const dynamic = "force-dynamic";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { listConnections, listConnectionSyncRuns, syncConnection } from "../../lib/api";
import { ru } from "../../lib/ru";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

type Connection = { id: number; platform: string; status: string };

const statusVariant: Record<string, "success" | "danger" | "warning" | "muted"> = {
  success: "success",
  failed: "danger",
  queued: "warning",
  running: "warning",
};

const formatStatus = (value?: string | null) => {
  if (!value) return "—";
  return ru.statuses[value as keyof typeof ru.statuses] || value;
};

export default function SyncRunsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [runs, setRuns] = useState<Array<{ id: number; status: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(false);

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
    setLoading(true);
    try {
      const data = await listConnections();
      setConnections(data.items);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async (connectionId: number) => {
    try {
      const data = await listConnectionSyncRuns(connectionId);
      setRuns(data);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
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
    if (!selected) return;
    const hasActive = runs.some((run) => run.status === "queued" || run.status === "running");
    if (!hasActive) return;
    const interval = setInterval(() => loadRuns(selected), 2500);
    return () => clearInterval(interval);
  }, [runs, selected]);

  const handleSync = async () => {
    if (!selected) {
      const message = "Выберите подключение";
      setError(message);
      toast.error(message);
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
      setNotice(`Синхронизация поставлена в очередь: #${run.id}`);
      toast.success("Синк запущен");
      await loadRuns(selected);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.syncRuns}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
          {notice && <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{notice}</div>}
          <div className="grid gap-3 md:grid-cols-4">
            <select value={selected ?? ""} onChange={(event) => setSelected(Number(event.target.value) || null)} className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm">
              <option value="">Выберите подключение</option>
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  #{c.id} {c.platform} ({c.status})
                </option>
              ))}
            </select>
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <Button onClick={handleSync}>{ru.actions.sync}</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>История запусков</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>{ru.labels.status}</TableHead>
                  <TableHead>Создан</TableHead>
                  <TableHead>Результат</TableHead>
                  <TableHead>Ошибка</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>#{run.id}</TableCell>
                    <TableCell><Badge variant={statusVariant[run.status] || "muted"}>{formatStatus(run.status)}</Badge></TableCell>
                    <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                    <TableCell className="text-slate-400">
                      {run.result_json && "inserted" in run.result_json
                        ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                        : "—"}
                    </TableCell>
                    <TableCell className="text-slate-400">{run.error_text ? String(run.error_text).slice(0, 80) : "—"}</TableCell>
                  </TableRow>
                ))}
                {runs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-slate-400">Запусков пока нет.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
