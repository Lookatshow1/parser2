"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useMemo } from "react";
import { toast } from "sonner";
import {
  getKpiTimeseries,
  getKpiSummary,
  dashboardChannels,
  listConnections,
  KpiTimeseriesResponse,
  KpiSummaryResponse,
  DashboardChannel,
  ConnectionResponse
} from "../../lib/api";
import { STR } from "../../lib/strings";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import { Badge } from "../../components/ui/badge";

const formatNumber = (value: number | undefined | null) => {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("ru-RU").format(value);
};

const formatFloat = (value: number | undefined | null, digits = 2) => {
  if (value === undefined || value === null) return "—";
  return value.toFixed(digits);
};

const formatCurrency = (value: number | undefined | null) => {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export default function DashboardPage() {
  const [timeseriesData, setTimeseriesData] = useState<KpiTimeseriesResponse | null>(null);
  const [summaryData, setSummaryData] = useState<KpiSummaryResponse | null>(null);
  const [channels, setChannels] = useState<DashboardChannel[]>([]);
  const [connections, setConnections] = useState<ConnectionResponse[]>([]);

  // Filters
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [channel, setChannel] = useState("all");
  const [selectedConnections, setSelectedConnections] = useState<number[]>([]);
  const [mode, setMode] = useState<"index" | "absolute">("index");
  const [showConnectionsPopup, setShowConnectionsPopup] = useState(false);

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
    if (!dateFrom || !dateTo) return;
    
    setLoading(true);
    setError(null);
    try {
      const [timeseries, summary] = await Promise.all([
        getKpiTimeseries({
          date_from: dateFrom,
          date_to: dateTo,
          connection_ids: selectedConnections.length > 0 ? selectedConnections : undefined,
          platform: channel !== "all" ? channel : undefined,
          mode: mode
        }),
        getKpiSummary({
          date_from: dateFrom,
          date_to: dateTo,
          connection_ids: selectedConnections.length > 0 ? selectedConnections : undefined,
          platform: channel !== "all" ? channel : undefined
        })
      ]);
      setTimeseriesData(timeseries);
      setSummaryData(summary);
    } catch (err) {
      const message = (err as Error).message || "Ошибка загрузки данных";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom && dateTo) load();
  }, [dateFrom, dateTo, channel, selectedConnections, mode]);

  const chartData = useMemo(() => {
    if (!timeseriesData) return [];
    return timeseriesData.items.map(item => ({
      date: item.date,
      impressions: mode === "index" ? (item.impressions_index ?? 0) : item.impressions,
      clicks: mode === "index" ? (item.clicks_index ?? 0) : item.clicks,
      conversions: mode === "index" ? (item.conversions_index ?? 0) : item.conversions,
      spend: mode === "index" ? (item.spend_index ?? 0) : item.spend,
      // Raw values for tooltip
      raw_impressions: item.impressions,
      raw_clicks: item.clicks,
      raw_conversions: item.conversions,
      raw_spend: item.spend,
    }));
  }, [timeseriesData, mode]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="rounded-lg border border-border bg-panel px-3 py-2 text-xs text-text shadow-card">
          <p className="mb-2 font-semibold">{label}</p>
          <div className="space-y-1 text-muted">
            <p className="text-text">
              Показы: {mode === "index" ? `${data.impressions.toFixed(1)}%` : formatNumber(data.raw_impressions)}
            </p>
            <p className="text-text">
              Клики: {mode === "index" ? `${data.clicks.toFixed(1)}%` : formatNumber(data.raw_clicks)}
            </p>
            <p className="text-text">
              Конверсии: {mode === "index" ? `${data.conversions.toFixed(1)}%` : formatNumber(data.raw_conversions)}
            </p>
            <p className="text-text">
              Расход: {mode === "index" ? `${data.spend.toFixed(1)}%` : formatCurrency(data.raw_spend)}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const toggleConnection = (connId: number) => {
    setSelectedConnections(prev =>
      prev.includes(connId)
        ? prev.filter(id => id !== connId)
        : [...prev, connId]
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={STR.pages.dashboardTitle}
        subtitle={STR.pages.dashboardSubtitle}
        actions={
          <>
            <select
              className="h-9 rounded-md border border-border bg-panel-strong px-3 text-sm text-text"
              value={channel}
              onChange={e => setChannel(e.target.value)}
            >
              {channels.map(c => <option key={c.key} value={c.key}>{c.title}</option>)}
            </select>
            <div className="relative">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowConnectionsPopup(!showConnectionsPopup)}
              >
                Подключения {selectedConnections.length > 0 && `(${selectedConnections.length})`}
              </Button>
              {showConnectionsPopup && (
                <div className="absolute top-full right-0 z-10 mt-2 w-64 rounded-xl border border-border bg-panel p-3 shadow-card">
                  <div className="mb-2 text-xs text-muted">Выберите подключения</div>
                  <div className="max-h-64 space-y-2 overflow-y-auto text-sm text-text">
                    {connections.map(conn => (
                      <label key={conn.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedConnections.includes(conn.id)}
                          onChange={() => toggleConnection(conn.id)}
                          className="rounded border-border bg-panel-strong"
                        />
                        {conn.name || `Подключение ${conn.id}`}
                      </label>
                    ))}
                    {connections.length === 0 && (
                      <div className="text-xs text-muted">Нет подключений</div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <Input
              type="date"
              className="w-auto"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
            />
            <Input
              type="date"
              className="w-auto"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
            />
            <div className="flex items-center gap-1 rounded-md border border-border bg-panel-strong p-1">
              <button
                onClick={() => setMode("index")}
                className={`px-3 py-1 text-sm rounded ${mode === "index" ? "bg-accent text-white" : "text-muted"}`}
              >
                Индекс
              </button>
              <button
                onClick={() => setMode("absolute")}
                className={`px-3 py-1 text-sm rounded ${mode === "absolute" ? "bg-accent text-white" : "text-muted"}`}
              >
                Абсолютные
              </button>
            </div>
            <Button onClick={load} size="sm">{STR.actions.refresh}</Button>
          </>
        }
      />

      {error && (
        <Card className="border-danger/40 bg-danger/10">
          <CardContent className="pt-6">
            <div className="text-sm text-danger">{error}</div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-7">
        {[
          { label: "Показы", val: summaryData?.impressions },
          { label: "Клики", val: summaryData?.clicks },
          { label: "Конверсии", val: summaryData?.conversions },
          { label: "Расход", val: summaryData?.spend, formatter: formatCurrency },
          { label: "CTR", val: summaryData?.ctr ? `${summaryData.ctr}%` : null },
          { label: "CPC", val: summaryData?.cpc ? formatCurrency(summaryData.cpc) : null },
          { label: "CPA", val: summaryData?.cpa ? formatCurrency(summaryData.cpa) : null },
        ].map((k, i) => (
          <Card key={i} className="flex flex-col justify-between p-4">
            <div className="text-xs uppercase text-muted">{k.label}</div>
            <div className="text-lg font-semibold text-text">
              {loading ? (
                <Skeleton className="h-6 w-16" />
              ) : (
                k.formatter ? (k.formatter(k.val as number) || "—") : (typeof k.val === 'number' ? formatNumber(k.val) : (k.val || "—"))
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Main Chart */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle>График метрик</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {!timeseriesData?.items.length && !loading ? (
            <EmptyState
              title={STR.pages.dashboardEmptyTitle}
              description={STR.pages.dashboardEmptyDesc}
              className="h-80"
            />
          ) : (
            <div className="h-80 w-full">
              {loading && <Skeleton className="h-full w-full" />}
              {!loading && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis
                      dataKey="date"
                      stroke="hsl(var(--muted))"
                      fontSize={12}
                      tickFormatter={(value) => value.slice(5)} // Show MM-DD
                    />
                    {mode === "index" ? (
                      <YAxis
                        stroke="hsl(var(--muted))"
                        fontSize={12}
                        domain={[0, 100]}
                        label={{ value: "Индекс (0-100)", angle: -90, position: "insideLeft" }}
                      />
                    ) : (
                      <>
                        <YAxis
                          yAxisId="left"
                          stroke="hsl(var(--muted))"
                          fontSize={12}
                          label={{ value: "Показы / Клики / Конверсии", angle: -90, position: "insideLeft" }}
                        />
                        <YAxis
                          yAxisId="right"
                          orientation="right"
                          stroke="hsl(var(--danger))"
                          fontSize={12}
                          label={{ value: "Расход (₽)", angle: 90, position: "insideRight" }}
                        />
                      </>
                    )}
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {mode === "index" ? (
                      <>
                        <Line
                          type="monotone"
                          dataKey="impressions"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                          name="Показы"
                          yAxisId={0}
                        />
                        <Line
                          type="monotone"
                          dataKey="clicks"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={false}
                          name="Клики"
                          yAxisId={0}
                        />
                        <Line
                          type="monotone"
                          dataKey="conversions"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          dot={false}
                          name="Конверсии"
                          yAxisId={0}
                        />
                        <Line
                          type="monotone"
                          dataKey="spend"
                          stroke="#ef4444"
                          strokeWidth={2}
                          dot={false}
                          name="Расход"
                          yAxisId={0}
                        />
                      </>
                    ) : (
                      <>
                        <Line
                          type="monotone"
                          dataKey="impressions"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                          name="Показы"
                          yAxisId="left"
                        />
                        <Line
                          type="monotone"
                          dataKey="clicks"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={false}
                          name="Клики"
                          yAxisId="left"
                        />
                        <Line
                          type="monotone"
                          dataKey="conversions"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          dot={false}
                          name="Конверсии"
                          yAxisId="left"
                        />
                        <Line
                          type="monotone"
                          dataKey="spend"
                          stroke="#ef4444"
                          strokeWidth={2}
                          dot={false}
                          name="Расход"
                          yAxisId="right"
                        />
                      </>
                    )}
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          )}
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
                <TableHead>Показы</TableHead>
                <TableHead>Клики</TableHead>
                <TableHead>Конверсии</TableHead>
                <TableHead>Расход</TableHead>
                {mode === "index" && (
                  <>
                    <TableHead>Индекс показов</TableHead>
                    <TableHead>Индекс кликов</TableHead>
                    <TableHead>Индекс конверсий</TableHead>
                    <TableHead>Индекс расхода</TableHead>
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {timeseriesData?.items.map((row, i) => (
                <TableRow key={i}>
                  <TableCell>{row.date}</TableCell>
                  <TableCell>{formatNumber(row.impressions)}</TableCell>
                  <TableCell>{formatNumber(row.clicks)}</TableCell>
                  <TableCell>{formatNumber(row.conversions)}</TableCell>
                  <TableCell>{formatCurrency(row.spend)}</TableCell>
                  {mode === "index" && (
                    <>
                      <TableCell>{row.impressions_index !== null ? `${row.impressions_index.toFixed(1)}%` : "—"}</TableCell>
                      <TableCell>{row.clicks_index !== null ? `${row.clicks_index.toFixed(1)}%` : "—"}</TableCell>
                      <TableCell>{row.conversions_index !== null ? `${row.conversions_index.toFixed(1)}%` : "—"}</TableCell>
                      <TableCell>{row.spend_index !== null ? `${row.spend_index.toFixed(1)}%` : "—"}</TableCell>
                    </>
                  )}
                </TableRow>
              ))}
              {!timeseriesData?.items.length && !loading && (
                <TableRow>
                  <TableCell colSpan={mode === "index" ? 9 : 5} className="text-center text-muted">
                    Нет данных
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
