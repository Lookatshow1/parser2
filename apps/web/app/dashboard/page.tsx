"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useMemo } from "react";
import { toast } from "sonner";
import {
  dashboardUnifiedTimeseries,
  dashboardChannels,
  listConnections,
  UnifiedDashboardResponse,
  DashboardChannel,
  ConnectionResponse
} from "../../lib/api";
import { STR } from "../../lib/strings";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import { Badge } from "../../components/ui/badge";

const formatNumber = (value: number | undefined) => {
  if (value === undefined) return "—";
  return new Intl.NumberFormat("ru-RU").format(value);
};

const formatFloat = (value: number | undefined | null, digits = 2) => {
  if (value === undefined || value === null) return "—";
  return value.toFixed(digits);
};

export default function DashboardPage() {
  const [data, setData] = useState<UnifiedDashboardResponse | null>(null);
  const [channels, setChannels] = useState<DashboardChannel[]>([]);
  const [connections, setConnections] = useState<ConnectionResponse[]>([]);

  // Filters
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [channel, setChannel] = useState("all");
  const [selectedConnections, setSelectedConnections] = useState<string[]>([]); // Not used in UI yet but ready

  const [loading, setLoading] = useState(false);

  // Chart toggles
  const [showClicks, setShowClicks] = useState(true);
  const [showImpressions, setShowImpressions] = useState(false);
  const [showConversions, setShowConversions] = useState(true);
  const [showSpend, setShowSpend] = useState(true);

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
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);

    const init = async () => {
      try {
        const [ch, conns] = await Promise.all([
          dashboardChannels(),
          listConnections()
        ]);
        setChannels(ch);
        setConnections(conns.items);
      } catch (err) {
        toast.error("Ошибка загрузки справочников");
      }
    };
    init();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await dashboardUnifiedTimeseries({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        channel,
        connection_ids: selectedConnections.length ? selectedConnections.map(Number) : undefined
      });
      setData(res);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom && dateTo) load();
  }, [dateFrom, dateTo, channel]); // Auto-reload on filter change

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.series.map(s => ({
      date: s.date,
      index: s.index,
      clicks: s.norm.clicks,
      impressions: s.norm.impressions,
      conversions: s.norm.conversions,
      spend: s.norm.spend,
      raw: s.raw // for tooltip
    }));
  }, [data]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const raw = payload[0].payload.raw;
      return (
        <div className="bg-slate-900 border border-slate-800 p-3 rounded shadow-lg text-xs">
          <p className="font-bold mb-2">{label}</p>
          <p className="text-blue-400">Индекс: {payload[0].payload.index}</p>
          <div className="mt-2 space-y-1 text-slate-300">
            <p>Клики: {raw.clicks}</p>
            <p>Показы: {raw.impressions}</p>
            <p>Конверсии: {raw.conversions}</p>
            <p>Расход: {raw.spend}</p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Аналитика</h1>
          <p className="text-sm text-slate-400">Единый центр управления эффективностью</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <select
            className="h-9 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm"
            value={channel}
            onChange={e => setChannel(e.target.value)}
          >
            {channels.map(c => <option key={c.key} value={c.key}>{c.title}</option>)}
          </select>
          <Input type="date" className="w-auto" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <Input type="date" className="w-auto" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          <Button onClick={load} size="sm">{STR.actions.refresh}</Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {[
          { label: "Клики", val: data?.totals.clicks },
          { label: "Показы", val: data?.totals.impressions },
          { label: "Конверсии", val: data?.totals.conversions },
          { label: "Расход", val: data?.totals.spend },
          { label: "CTR", val: formatFloat(data?.kpi.ctr ? data.kpi.ctr * 100 : 0) + "%" },
          { label: "CPC", val: formatFloat(data?.kpi.cpc) },
          { label: "CPA", val: formatFloat(data?.kpi.cpa) },
        ].map((k, i) => (
          <Card key={i} className="p-4 flex flex-col justify-between">
            <div className="text-xs text-slate-500 uppercase">{k.label}</div>
            <div className="text-lg font-semibold text-slate-100">
              {loading ? <Skeleton className="h-6 w-16" /> : (typeof k.val === 'number' ? formatNumber(k.val) : k.val)}
            </div>
          </Card>
        ))}
      </div>

      {/* Main Chart */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle>Индекс активности</CardTitle>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-2"><input type="checkbox" checked={showClicks} onChange={e => setShowClicks(e.target.checked)} /> Клики</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={showImpressions} onChange={e => setShowImpressions(e.target.checked)} /> Показы</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={showConversions} onChange={e => setShowConversions(e.target.checked)} /> Конверсии</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={showSpend} onChange={e => setShowSpend(e.target.checked)} /> Расход</label>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80 w-full">
            {loading && <Skeleton className="h-full w-full" />}
            {!loading && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="date" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} domain={[0, 1]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line type="monotone" dataKey="index" stroke="#3b82f6" strokeWidth={3} dot={false} name="Индекс" />
                  {showClicks && <Line type="monotone" dataKey="clicks" stroke="#10b981" strokeWidth={1} dot={false} strokeDasharray="3 3" name="Клики (norm)" />}
                  {showImpressions && <Line type="monotone" dataKey="impressions" stroke="#6366f1" strokeWidth={1} dot={false} strokeDasharray="3 3" name="Показы (norm)" />}
                  {showConversions && <Line type="monotone" dataKey="conversions" stroke="#f59e0b" strokeWidth={1} dot={false} strokeDasharray="3 3" name="Конверсии (norm)" />}
                  {showSpend && <Line type="monotone" dataKey="spend" stroke="#ef4444" strokeWidth={1} dot={false} strokeDasharray="3 3" name="Расход (norm)" />}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Daily Table */}
      <Card>
        <CardHeader>
          <CardTitle>Детализация по дням</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Дата</TableHead>
                <TableHead>Индекс</TableHead>
                <TableHead>Клики</TableHead>
                <TableHead>Показы</TableHead>
                <TableHead>Конверсии</TableHead>
                <TableHead>Расход</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.series.map((row, i) => (
                <TableRow key={i}>
                  <TableCell>{row.date}</TableCell>
                  <TableCell><Badge variant="outline">{row.index}</Badge></TableCell>
                  <TableCell>{formatNumber(row.raw.clicks)}</TableCell>
                  <TableCell>{formatNumber(row.raw.impressions)}</TableCell>
                  <TableCell>{formatNumber(row.raw.conversions)}</TableCell>
                  <TableCell>{formatNumber(row.raw.spend)}</TableCell>
                </TableRow>
              ))}
              {!data?.series.length && !loading && (
                <TableRow><TableCell colSpan={6} className="text-center text-slate-500">Нет данных</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
