"use client";
export const dynamic = "force-dynamic";
import { useEffect, useMemo, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { getMetricsTimeseries, listConnections, getMetricsBreakdown, MetricsBreakdownItem } from "../../lib/api";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";

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

  // Breakdown state
  const [breakdownTab, setBreakdownTab] = useState("campaign");
  const [breakdownItems, setBreakdownItems] = useState<MetricsBreakdownItem[]>([]);
  const [breakdownLoading, setBreakdownLoading] = useState(false);
  const [breakdownSort, setBreakdownSort] = useState("spend");

  // Drilldown state
  const [drilldownItem, setDrilldownItem] = useState<MetricsBreakdownItem | null>(null);
  const [drilldownSeries, setDrilldownSeries] = useState<TimeseriesItem[]>([]);
  const [drilldownLoading, setDrilldownLoading] = useState(false);

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

  const loadBreakdown = async () => {
    setBreakdownLoading(true);
    try {
      const data = await getMetricsBreakdown({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        dimension: breakdownTab,
        connection_ids: selectedConnection === "all" ? undefined : [Number(selectedConnection)],
        order_by: breakdownSort,
        limit: 50
      });
      setBreakdownItems(data.items);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBreakdownLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom && dateTo) {
      loadMetrics();
      loadBreakdown();
    }
  }, [dateFrom, dateTo, selectedConnection]);

  useEffect(() => {
    if (dateFrom && dateTo) {
      loadBreakdown();
    }
  }, [breakdownTab, breakdownSort]);

  const chartData = items.map((item) => ({
    date: item.date,
    value: Number(item[metricKey] ?? 0),
  }));

  const handleDrilldown = async (item: MetricsBreakdownItem) => {
    setDrilldownItem(item);
    setDrilldownLoading(true);
    try {
      const params: any = {
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        connection_ids: selectedConnection === "all" ? undefined : [Number(selectedConnection)],
      };

      if (item.dimension === "campaign") params.campaign_external_id = item.external_id;
      if (item.dimension === "ad_group") params.ad_group_external_id = item.external_id;
      if (item.dimension === "ad") params.ad_external_id = item.external_id;

      const data = await getMetricsTimeseries(params);
      setDrilldownSeries(data.items || []);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setDrilldownLoading(false);
    }
  };

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
            <Button onClick={() => { loadMetrics(); loadBreakdown(); }}>{STR.actions.refresh}</Button>
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

      <Tabs value={breakdownTab} onValueChange={setBreakdownTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="campaign">Кампании</TabsTrigger>
          <TabsTrigger value="ad_group">Группы</TabsTrigger>
          <TabsTrigger value="ad">Объявления</TabsTrigger>
        </TabsList>

        <Card>
          <CardContent className="p-0">
            {breakdownLoading && <div className="p-6"><Skeleton className="h-40 w-full" /></div>}
            {!breakdownLoading && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("spend")}>Расход</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("impressions")}>Показы</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("clicks")}>Клики</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("ctr")}>CTR</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("cpc")}>CPC</TableHead>
                    <TableHead className="cursor-pointer hover:text-white" onClick={() => setBreakdownSort("roas")}>ROAS</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {breakdownItems.map((item, idx) => (
                    <TableRow key={idx} className="cursor-pointer hover:bg-slate-900/50" onClick={() => handleDrilldown(item)}>
                      <TableCell>
                        <div className="font-medium">{item.name}</div>
                        <div className="text-xs text-slate-500 font-mono">{item.external_id}</div>
                      </TableCell>
                      <TableCell>{formatNumber(item.spend)}</TableCell>
                      <TableCell>{formatNumber(item.impressions)}</TableCell>
                      <TableCell>{formatNumber(item.clicks)}</TableCell>
                      <TableCell>{formatFloat(item.ctr, 4)}</TableCell>
                      <TableCell>{formatFloat(item.cpc, 2)}</TableCell>
                      <TableCell>{formatFloat(item.roas, 2)}</TableCell>
                    </TableRow>
                  ))}
                  {!breakdownItems.length && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-slate-500 py-8">Нет данных</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </Tabs>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <CardTitle>Общая динамика</CardTitle>
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

      <Dialog open={!!drilldownItem} onOpenChange={(open) => !open && setDrilldownItem(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{drilldownItem?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">Расход</div>
                <div className="text-lg font-semibold">{formatNumber(drilldownItem?.spend)}</div>
              </div>
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">Клики</div>
                <div className="text-lg font-semibold">{formatNumber(drilldownItem?.clicks)}</div>
              </div>
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">CPC</div>
                <div className="text-lg font-semibold">{formatFloat(drilldownItem?.cpc)}</div>
              </div>
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">ROAS</div>
                <div className="text-lg font-semibold">{formatFloat(drilldownItem?.roas)}</div>
              </div>
            </div>

            <div className="h-64 w-full mt-4">
              {drilldownLoading && <Skeleton className="h-full w-full" />}
              {!drilldownLoading && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={drilldownSeries.map(i => ({ date: i.date, value: i.spend }))}>
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#60a5fa" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
