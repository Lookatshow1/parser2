"use client";

import { useEffect, useMemo, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { getMetricsTimeseries, listConnections } from "../../lib/api";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "../../components/ui/tabs";

const metricTabs = [
  { key: "spend", label: "Расход" },
  { key: "clicks", label: "Клики" },
  { key: "impressions", label: "Показы" },
] as const;

type MetricKey = (typeof metricTabs)[number]["key"];

type Connection = { id: number; name?: string | null; platform: string; status: string };

type TimeseriesItem = {
  date: string;
  impressions: number;
  clicks: number;
  spend: number;
  leads: number;
  purchases: number;
  revenue: number;
  ctr?: number | null;
  cpc?: number | null;
  cpm?: number | null;
  cpa?: number | null;
  roas?: number | null;
};

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("ru-RU").format(value);
};

const formatFloat = (value: number | null | undefined, digits = 2) => {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
};

export default function MetricsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>("all");
  const [metricKey, setMetricKey] = useState<MetricKey>("spend");
  const [items, setItems] = useState<TimeseriesItem[]>([]);
  const [totals, setTotals] = useState<Partial<TimeseriesItem>>({});
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 13);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  useEffect(() => {
    const loadConnections = async () => {
      try {
        const data = await listConnections();
        setConnections(data.items);
      } catch (err) {
        const message = (err as Error).message;
        toast.error(message);
      }
    };
    loadConnections();
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMetricsTimeseries({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        connection_ids: selectedConnection === "all" ? undefined : [Number(selectedConnection)],
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
    if (dateFrom && dateTo) {
      loadMetrics();
    }
  }, [dateFrom, dateTo, selectedConnection]);

  const chartData = items.map((item) => ({
    date: item.date,
    value: Number(item[metricKey] ?? 0),
  }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
          <CardTitle>{STR.labels.metrics}</CardTitle>
            <p className="text-sm text-slate-400">Обзор эффективности за выбранный период.</p>
          </div>
          <Badge variant="muted">Демо-режим</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
          <div className="grid gap-3 md:grid-cols-5">
            <select
              value={selectedConnection}
              onChange={(event) => setSelectedConnection(event.target.value)}
              className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm text-slate-100"
            >
              <option value="all">Все подключения</option>
              {connections.map((connection) => (
                <option key={connection.id} value={connection.id}>
                  {connection.name || `Подключение #${connection.id}`} · {connection.platform}
                </option>
              ))}
            </select>
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <Button onClick={loadMetrics}>{STR.actions.refresh}</Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Расход</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(totals.spend as number)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Клики</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(totals.clicks as number)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Показы</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(totals.impressions as number)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>CTR / CPC</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-slate-300">
            <div>CTR: {formatFloat(totals.ctr, 4)}</div>
            <div>CPC: {formatFloat(totals.cpc, 2)}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <CardTitle>Динамика</CardTitle>
          <Tabs value={metricKey} onValueChange={(value) => setMetricKey(value as MetricKey)}>
            <TabsList>
              {metricTabs.map((tab) => (
                <TabsTrigger key={tab.key} value={tab.key}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-64 w-full" />}
          {!loading && chartData.length === 0 && (
            <div className="text-sm text-slate-400">{STR.messages.noMetrics}</div>
          )}
          {!loading && chartData.length > 0 && (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Дневные метрики</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-24 w-full" />}
          {!loading && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Дата</TableHead>
                  <TableHead>Расход</TableHead>
                  <TableHead>Клики</TableHead>
                  <TableHead>Показы</TableHead>
                  <TableHead>Покупки</TableHead>
                  <TableHead>CTR</TableHead>
                  <TableHead>CPC</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow key={row.date}>
                    <TableCell>{row.date}</TableCell>
                    <TableCell>{formatNumber(row.spend)}</TableCell>
                    <TableCell>{formatNumber(row.clicks)}</TableCell>
                    <TableCell>{formatNumber(row.impressions)}</TableCell>
                    <TableCell>{formatNumber(row.purchases)}</TableCell>
                    <TableCell>{formatFloat(row.ctr, 4)}</TableCell>
                    <TableCell>{formatFloat(row.cpc, 2)}</TableCell>
                  </TableRow>
                ))}
                {items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-slate-400">
                      {STR.messages.noMetrics}
                    </TableCell>
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
