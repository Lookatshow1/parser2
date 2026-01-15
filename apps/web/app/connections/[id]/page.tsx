"use client";
export const dynamic = "force-dynamic";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { getDashboardSummary, listConnectionSnapshots, listConnectionSyncRuns, listJobRuns, syncConnection } from "../../../lib/api";
import { ru } from "../../../lib/ru";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Skeleton } from "../../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

type Run = { id: number; status: string; run_type: string; created_at: string; result_json?: Record<string, unknown>; error_text?: string | null };
type JobRun = { id: number; job_type: string; status: string; created_at: string; result_json?: Record<string, unknown> | null; error_text?: string | null };

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
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
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
        const message = (err as Error).message;
        setError(message);
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
      setNotice(`Синхронизация поставлена в очередь (run #${run.id})`);
      toast.success("Синк запущен");
      const runData = await listConnectionSyncRuns(connectionId);
      setRuns(runData);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
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
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  useEffect(() => {
    if (Number.isFinite(connectionId)) {
      load();
    }
  }, [connectionId]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Подключение #{connectionId}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted">Сводка за последние 14 дней</p>
          {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
          {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && summary && (
            <div className="grid gap-3 md:grid-cols-4 text-sm">
              <div className="rounded-lg border border-border bg-panel-strong p-3">Показы: {summary.impressions}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">Клики: {summary.clicks}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">Расход: {summary.spend}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">CTR: {summary.ctr ?? "—"}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">CPC: {summary.cpc ?? "—"}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">CPM: {summary.cpm ?? "—"}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">CPA: {summary.cpa ?? "—"}</div>
              <div className="rounded-lg border border-border bg-panel-strong p-3">ROAS: {summary.roas ?? "—"}</div>
            </div>
          )}
          <div className="grid gap-3 md:grid-cols-4 text-sm">
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <Button onClick={handleSync}>{ru.actions.sync}</Button>
            <Button variant="secondary" onClick={refreshMetrics}>Обновить метрики</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.syncRuns}</CardTitle>
        </CardHeader>
        <CardContent>
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
                  <TableCell className="text-muted">
                    {run.result_json && "inserted" in run.result_json
                      ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                      : "—"}
                  </TableCell>
                  <TableCell className="text-muted">{run.error_text ? String(run.error_text).slice(0, 80) : "—"}</TableCell>
                </TableRow>
              ))}
              {runs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted">Синхронизаций пока нет.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Прогоны задач</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Тип</TableHead>
                <TableHead>{ru.labels.status}</TableHead>
                <TableHead>Ошибка</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobRuns.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>#{job.id}</TableCell>
                  <TableCell>{job.job_type}</TableCell>
                  <TableCell><Badge variant={statusVariant[job.status] || "muted"}>{formatStatus(job.status)}</Badge></TableCell>
                  <TableCell className="text-muted">{job.error_text ? String(job.error_text).slice(0, 80) : "—"}</TableCell>
                </TableRow>
              ))}
              {jobRuns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted">Задач пока нет.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Снимки метрик</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Дата</TableHead>
                <TableHead>Показы</TableHead>
                <TableHead>Клики</TableHead>
                <TableHead>Расход</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {metrics.map((row, idx) => (
                <TableRow key={idx}>
                  <TableCell>{String(row.date || "")}</TableCell>
                  <TableCell>{String(row.impressions || 0)}</TableCell>
                  <TableCell>{String(row.clicks || 0)}</TableCell>
                  <TableCell>{String(row.spend || 0)}</TableCell>
                </TableRow>
              ))}
              {metrics.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted">{ru.messages.noMetrics}</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
