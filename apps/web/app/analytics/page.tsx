"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    AreaChart, Area, BarChart, Bar, LineChart, Line,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import {
    TrendingUp, Eye, MousePointer, DollarSign, Target,
    BarChart3, RefreshCw, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { toast } from "sonner";
import { listConnections, getMetricsTimeseries, ConnectionResponse } from "@/lib/api";

const PERIOD_DAYS: Record<string, number> = {
    "7d": 7,
    "14d": 14,
    "30d": 30
};

const PLATFORM_LABELS: Record<string, string> = {
    yandex: "Яндекс Директ",
    vk: "VK Реклама",
    ozon: "Ozon Performance",
    google: "Google Ads"
};

const PLATFORM_COLORS: Record<string, string> = {
    yandex: "#FF5C00",
    vk: "#0077FF",
    ozon: "#005BFF",
    google: "#34A853"
};

type MetricsSummary = {
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    revenue: number;
    ctr: number;
    cpc: number;
    conversion_rate: number;
    roas: number;
};

type DailyMetrics = {
    date: string;
    fullDate: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    revenue: number;
};

type PlatformMetrics = {
    platform: string;
    name: string;
    impressions: number;
    clicks: number;
    spend: number;
    ctr: number;
    roas: number;
    color: string;
};

const EMPTY_SUMMARY: MetricsSummary = {
    impressions: 0,
    clicks: 0,
    spend: 0,
    conversions: 0,
    revenue: 0,
    ctr: 0,
    cpc: 0,
    conversion_rate: 0,
    roas: 0
};

const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
};

const formatShortDate = (dateStr: string) => {
    const date = new Date(`${dateStr}T00:00:00`);
    return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "short" });
};

const calcChange = (current: number, previous: number) => {
    if (!Number.isFinite(previous) || previous === 0) {
        return undefined;
    }
    const diff = ((current - previous) / previous) * 100;
    return Number.isFinite(diff) ? Number(diff.toFixed(1)) : undefined;
};

const buildDateRange = (days: number) => {
    const dateTo = new Date();
    dateTo.setHours(0, 0, 0, 0);
    const dateFrom = new Date(dateTo);
    dateFrom.setDate(dateFrom.getDate() - (days - 1));

    const prevDateTo = new Date(dateFrom);
    prevDateTo.setDate(prevDateTo.getDate() - 1);
    const prevDateFrom = new Date(prevDateTo);
    prevDateFrom.setDate(prevDateFrom.getDate() - (days - 1));

    return {
        dateFrom: formatDate(dateFrom),
        dateTo: formatDate(dateTo),
        prevDateFrom: formatDate(prevDateFrom),
        prevDateTo: formatDate(prevDateTo)
    };
};

function MetricCard({
    title,
    value,
    change,
    icon: Icon,
    format = "number",
    prefix = "",
    suffix = ""
}: {
    title: string;
    value: number;
    change?: number;
    icon: any;
    format?: "number" | "currency" | "percent";
    prefix?: string;
    suffix?: string;
}) {
    const safeValue = Number.isFinite(value) ? value : 0;
    const formatValue = () => {
        if (format === "currency") {
            return `₽${safeValue.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}`;
        }
        if (format === "percent") {
            return `${safeValue.toFixed(2)}%`;
        }
        return safeValue.toLocaleString("ru-RU");
    };

    const isPositive = change !== undefined && change > 0;
    const isNegative = change !== undefined && change < 0;

    return (
        <Card className="glass-card border-white/5">
            <CardContent className="p-5">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-accent/20 rounded-lg">
                        <Icon className="h-5 w-5 text-accent" />
                    </div>
                    {change !== undefined && (
                        <div className={`flex items-center text-sm ${isPositive ? "text-green-400" : isNegative ? "text-red-400" : "text-gray-400"}`}>
                            {isPositive ? <ArrowUpRight className="h-4 w-4" /> : isNegative ? <ArrowDownRight className="h-4 w-4" /> : null}
                            {Math.abs(change)}%
                        </div>
                    )}
                </div>
                <div className="text-2xl font-bold text-white mb-1">
                    {prefix}{formatValue()}{suffix}
                </div>
                <div className="text-sm text-gray-400">{title}</div>
            </CardContent>
        </Card>
    );
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-gray-900 border border-white/10 rounded-lg p-3 shadow-xl">
                <p className="text-white font-medium mb-2">{label}</p>
                {payload.map((entry: any, index: number) => (
                    <p key={index} className="text-sm" style={{ color: entry.color }}>
                        {entry.name}: {Number(entry.value || 0).toLocaleString("ru-RU")}
                        {entry.name === "Расход" ? " ₽" : ""}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

export default function AnalyticsPage() {
    const [loading, setLoading] = useState(false);
    const [period, setPeriod] = useState("14d");
    const [platform, setPlatform] = useState("all");
    const [connections, setConnections] = useState<ConnectionResponse[]>([]);
    const [connectionsLoaded, setConnectionsLoaded] = useState(false);
    const [dailyData, setDailyData] = useState<DailyMetrics[]>([]);
    const [summary, setSummary] = useState<MetricsSummary>(EMPTY_SUMMARY);
    const [changes, setChanges] = useState<Record<string, number | undefined>>({});
    const [platformData, setPlatformData] = useState<PlatformMetrics[]>([]);

    useEffect(() => {
        let cancelled = false;
        const loadConnections = async () => {
            try {
                const data = await listConnections();
                if (cancelled) return;
                setConnections(data.items || []);
            } catch (error) {
                if (!cancelled) {
                    setConnections([]);
                }
            } finally {
                if (!cancelled) {
                    setConnectionsLoaded(true);
                }
            }
        };
        loadConnections();
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (!connectionsLoaded) return;
        const available = new Set(connections.map((conn) => String(conn.platform)));
        if (platform !== "all" && !available.has(platform)) {
            setPlatform("all");
        }
    }, [connectionsLoaded, connections, platform]);

    const loadMetrics = async () => {
        setLoading(true);
        try {
            const days = PERIOD_DAYS[period] ?? 14;
            const { dateFrom, dateTo, prevDateFrom, prevDateTo } = buildDateRange(days);
            const allConnectionIds = connections.map((conn) => conn.id);
            const selectedConnectionIds = platform === "all"
                ? allConnectionIds
                : connections.filter((conn) => String(conn.platform) === platform).map((conn) => conn.id);

            if (connections.length === 0 || (platform !== "all" && selectedConnectionIds.length === 0)) {
                setDailyData([]);
                setSummary(EMPTY_SUMMARY);
                setChanges({});
                setPlatformData([]);
                return;
            }

            const [currentData, previousData] = await Promise.all([
                getMetricsTimeseries({
                    date_from: dateFrom,
                    date_to: dateTo,
                    connection_ids: selectedConnectionIds
                }),
                getMetricsTimeseries({
                    date_from: prevDateFrom,
                    date_to: prevDateTo,
                    connection_ids: selectedConnectionIds
                })
            ]);

            const currentTotals = currentData.totals;
            const prevTotals = previousData.totals;

            const currentConversions = currentTotals.purchases > 0 ? currentTotals.purchases : currentTotals.leads;
            const prevConversions = prevTotals.purchases > 0 ? prevTotals.purchases : prevTotals.leads;

            const currentCtr = currentTotals.ctr ?? (currentTotals.impressions ? (currentTotals.clicks / currentTotals.impressions) * 100 : 0);
            const prevCtr = prevTotals.ctr ?? (prevTotals.impressions ? (prevTotals.clicks / prevTotals.impressions) * 100 : 0);
            const currentRoas = currentTotals.roas ?? (currentTotals.spend ? currentTotals.revenue / currentTotals.spend : 0);
            const prevRoas = prevTotals.roas ?? (prevTotals.spend ? prevTotals.revenue / prevTotals.spend : 0);
            const currentCpc = currentTotals.cpc ?? (currentTotals.clicks ? currentTotals.spend / currentTotals.clicks : 0);
            const conversionRate = currentTotals.clicks ? (currentConversions / currentTotals.clicks) * 100 : 0;

            setSummary({
                impressions: currentTotals.impressions,
                clicks: currentTotals.clicks,
                spend: currentTotals.spend,
                conversions: currentConversions,
                revenue: currentTotals.revenue,
                ctr: currentCtr,
                cpc: currentCpc,
                conversion_rate: conversionRate,
                roas: currentRoas
            });

            setChanges({
                impressions: calcChange(currentTotals.impressions, prevTotals.impressions),
                clicks: calcChange(currentTotals.clicks, prevTotals.clicks),
                spend: calcChange(currentTotals.spend, prevTotals.spend),
                conversions: calcChange(currentConversions, prevConversions),
                ctr: calcChange(currentCtr, prevCtr),
                roas: calcChange(currentRoas, prevRoas)
            });

            setDailyData(
                currentData.items.map((item) => ({
                    date: formatShortDate(item.date),
                    fullDate: item.date,
                    impressions: item.impressions,
                    clicks: item.clicks,
                    spend: item.spend,
                    conversions: item.purchases > 0 ? item.purchases : item.leads,
                    revenue: item.revenue
                }))
            );

            const platformGroups: Record<string, number[]> = {};
            if (platform === "all") {
                connections.forEach((conn) => {
                    const key = String(conn.platform);
                    platformGroups[key] = platformGroups[key] || [];
                    platformGroups[key].push(conn.id);
                });
            } else if (selectedConnectionIds.length > 0) {
                platformGroups[platform] = selectedConnectionIds;
            }

            const platformEntries = await Promise.all(
                Object.entries(platformGroups).map(async ([platformKey, ids]) => {
                    if (!ids.length) return null;
                    const data = await getMetricsTimeseries({
                        date_from: dateFrom,
                        date_to: dateTo,
                        connection_ids: ids
                    });
                    const totals = data.totals;
                    const ctr = totals.ctr ?? (totals.impressions ? (totals.clicks / totals.impressions) * 100 : 0);
                    const roas = totals.roas ?? (totals.spend ? totals.revenue / totals.spend : 0);
                    return {
                        platform: platformKey,
                        name: PLATFORM_LABELS[platformKey] || platformKey.toUpperCase(),
                        impressions: totals.impressions,
                        clicks: totals.clicks,
                        spend: totals.spend,
                        ctr,
                        roas,
                        color: PLATFORM_COLORS[platformKey] || "#22C55E"
                    };
                })
            );

            setPlatformData(platformEntries.filter((item): item is PlatformMetrics => Boolean(item)));
        } catch (error) {
            toast.error("Не удалось загрузить аналитику");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!connectionsLoaded) return;
        loadMetrics();
    }, [connectionsLoaded, period, platform]);

    const refresh = async () => {
        await loadMetrics();
        toast.success("Данные обновлены");
    };

    const platformOptions = Array.from(new Set(connections.map((conn) => String(conn.platform))));

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white">Аналитика</h1>
                    <p className="text-gray-400 mt-1">Сводные данные по всем рекламным платформам</p>
                </div>
                <div className="flex gap-3">
                    <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger className="w-32 bg-black/30 border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="7d">7 дней</SelectItem>
                            <SelectItem value="14d">14 дней</SelectItem>
                            <SelectItem value="30d">30 дней</SelectItem>
                        </SelectContent>
                    </Select>
                    <Select value={platform} onValueChange={setPlatform}>
                        <SelectTrigger className="w-44 bg-black/30 border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Все платформы</SelectItem>
                            {platformOptions.map((key) => (
                                <SelectItem key={key} value={key}>
                                    {PLATFORM_LABELS[key] || key.toUpperCase()}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={refresh} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                        Обновить
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard title="Показы" value={summary.impressions} change={changes.impressions} icon={Eye} />
                <MetricCard title="Клики" value={summary.clicks} change={changes.clicks} icon={MousePointer} />
                <MetricCard title="Расход" value={summary.spend} change={changes.spend} icon={DollarSign} format="currency" />
                <MetricCard title="Конверсии" value={summary.conversions} change={changes.conversions} icon={Target} />
            </div>

            <Card className="glass-card border-white/5">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 text-accent" />
                        Показы и клики по дням
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={dailyData}>
                                <defs>
                                    <linearGradient id="impressionsGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="clicksGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} />
                                <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={12} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                                <YAxis yAxisId="right" orientation="right" stroke="#10B981" fontSize={12} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Area
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="impressions"
                                    name="Показы"
                                    stroke="#8B5CF6"
                                    fill="url(#impressionsGradient)"
                                    strokeWidth={2}
                                />
                                <Area
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="clicks"
                                    name="Клики"
                                    stroke="#10B981"
                                    fill="url(#clicksGradient)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            <div className="grid md:grid-cols-2 gap-6">
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-accent" />
                            Расход по дням
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={dailyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                                    <YAxis stroke="#9CA3AF" fontSize={11} tickFormatter={v => `${(v / 1000).toFixed(0)}k ₽`} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar
                                        dataKey="spend"
                                        name="Расход"
                                        fill="#F59E0B"
                                        radius={[4, 4, 0, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Target className="h-5 w-5 text-accent" />
                            Конверсии по дням
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={dailyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                                    <YAxis stroke="#9CA3AF" fontSize={11} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Line
                                        type="monotone"
                                        dataKey="conversions"
                                        name="Конверсии"
                                        stroke="#EC4899"
                                        strokeWidth={3}
                                        dot={{ fill: "#EC4899", strokeWidth: 2, r: 4 }}
                                        activeDot={{ r: 6 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="glass-card border-white/5">
                <CardHeader>
                    <CardTitle className="text-white">Распределение по платформам</CardTitle>
                </CardHeader>
                <CardContent>
                    {platformData.length === 0 ? (
                        <div className="text-sm text-gray-500">Нет данных по выбранным подключениям.</div>
                    ) : (
                        <div className="space-y-6">
                            {platformData.map((p) => {
                                const totalSpend = platformData.reduce((s, pl) => s + pl.spend, 0);
                                const percentage = totalSpend ? (p.spend / totalSpend) * 100 : 0;

                                return (
                                    <div key={p.platform} className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-3">
                                                <div
                                                    className="w-3 h-3 rounded-full"
                                                    style={{ backgroundColor: p.color }}
                                                />
                                                <span className="text-white font-medium">{p.name}</span>
                                            </div>
                                            <span className="text-gray-400 text-sm">₽{p.spend.toLocaleString("ru-RU")}</span>
                                        </div>
                                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full rounded-full transition-all duration-500"
                                                style={{ width: `${percentage}%`, backgroundColor: p.color }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-xs text-gray-500">
                                            <span>CTR: {p.ctr.toFixed(2)}%</span>
                                            <span>Показы: {p.impressions.toLocaleString("ru-RU")}</span>
                                            <span>Клики: {p.clicks.toLocaleString("ru-RU")}</span>
                                            <span>ROAS: {p.roas.toFixed(2)}x</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard title="CTR" value={summary.ctr} change={changes.ctr} icon={TrendingUp} format="percent" />
                <MetricCard title="CPC" value={summary.cpc} icon={DollarSign} prefix="₽" />
                <MetricCard title="Конверсия" value={summary.conversion_rate} icon={Target} format="percent" />
                <MetricCard title="ROAS" value={summary.roas} change={changes.roas} icon={TrendingUp} suffix="x" />
            </div>
        </div>
    );
}
