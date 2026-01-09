"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { getDashboardSummary, getMetrics, listConnections } from "../../lib/api";
import { ru } from "../../lib/ru";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

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
  const [loading, setLoading] = useState(false);

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
    load();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  const refresh = async () => {
    if (!selected) {
      const message = "Выберите подключение";
      setError(message);
      toast.error(message);
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
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.metrics}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
          <div className="grid gap-3 md:grid-cols-5">
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
            <Button onClick={refresh}>{ru.actions.refresh}</Button>
          </div>
        </CardContent>
      </Card>

      {summary && (
        <Card>
          <CardHeader>
            <CardTitle>Итоги периода</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-4 text-sm">
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">Показы: {summary.impressions}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">Клики: {summary.clicks}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">Расход: {summary.spend}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">Покупки: {summary.purchases ?? 0}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">Выручка: {summary.revenue ?? 0}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">CTR: {summary.ctr ?? "—"}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">CPC: {summary.cpc ?? "—"}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">CPM: {summary.cpm ?? "—"}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">CPA: {summary.cpa ?? "—"}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">ROAS: {summary.roas ?? "—"}</div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Ежедневные метрики</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && (
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
                    <TableCell colSpan={4} className="text-center text-slate-400">{ru.messages.noMetrics}</TableCell>
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
