"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { getMetricsTimeseries, listConnections, ConnectionResponse } from "../../lib/api";
import { getOrgId, getToken } from "../../lib/session";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

type SeriesPoint = { date: string; value: number };

const metricOptions = ["spend", "clicks", "impressions"] as const;
const metricLabels: Record<(typeof metricOptions)[number], string> = {
  spend: "Расход",
  clicks: "Клики",
  impressions: "Показы",
};

const formatStatus = (value?: string | null) => {
  if (!value) return "—";
  return STR.statuses[value as keyof typeof STR.statuses] || value;
};

export default function DashboardPage() {
  const router = useRouter();
  const [metric, setMetric] = useState<(typeof metricOptions)[number]>("spend");
  const [items, setItems] = useState<Array<{
    date: string;
    impressions: number;
    clicks: number;
    spend: number;
    leads: number;
    purchases: number;
    revenue: number;
  }>>([]);
  const [totals, setTotals] = useState<Record<string, number | null>>({});
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
      setItems(data.items || []);
      setTotals(data.totals || {});
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
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
  const series = items.map((item) => ({
    date: item.date,
    value: Number(item[metric] ?? 0),
  })) as SeriesPoint[];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{STR.nav.dashboard}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
            <div>Организация: {getOrgId() || "не выбрана"}</div>
            {!getToken() && <Badge variant="warning">{STR.messages.loginRequired}</Badge>}
            {getToken() && !getOrgId() && <Badge variant="warning">{STR.messages.selectOrg}</Badge>}
          </div>
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
          <div className="grid gap-3 md:grid-cols-4 text-sm">
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <select value={metric} onChange={(event) => setMetric(event.target.value as typeof metric)} className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm">
              {metricOptions.map((item) => (
                <option key={item} value={item}>
                  {metricLabels[item]}
                </option>
              ))}
            </select>
            <Button onClick={load}>{STR.actions.refresh}</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Обзор периода</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading && <Skeleton className="h-24 w-full" />}
          {!loading && (
            <div className="grid gap-3 md:grid-cols-3 text-sm">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                Сумма {metricLabels[metric]}: <span className="text-slate-100">{totalValue}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                Точек: <span className="text-slate-100">{series.length}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                Период: {dateFrom} → {dateTo}
              </div>
            </div>
          )}
          {!loading && series.length === 0 && (
            <div className="text-sm text-slate-400">{STR.messages.noMetrics}</div>
          )}
          {!loading && series.length > 0 && (
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.connections}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && connections.length === 0 && <div className="text-sm text-slate-400">{STR.messages.noConnections}</div>}
          {!loading && connections.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>{STR.labels.platform}</TableHead>
                  <TableHead>{STR.labels.status}</TableHead>
                  <TableHead>Последний запуск</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {connections.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>#{item.id}</TableCell>
                    <TableCell>{item.platform}</TableCell>
                    <TableCell>
                      <Badge variant={item.last_sync_status === "success" ? "success" : item.last_sync_status === "failed" ? "danger" : "muted"}>
                        {formatStatus(item.last_sync_status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400">{item.last_sync_finished_at ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="secondary" size="sm" onClick={() => router.push(`/connections/${item.id}`)}>
                        {STR.actions.open}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
