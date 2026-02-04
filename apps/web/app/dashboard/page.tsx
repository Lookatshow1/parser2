"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    TrendingUp, TrendingDown, DollarSign, MousePointer, Eye, Target,
    ArrowUpRight, Loader2, Calendar, RefreshCw, Sparkles, AlertCircle, HelpCircle
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { getKpiSummary, getKpiTimeseries, listConnections } from "../../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface KpiSummary {
    impressions: number;
    clicks: number;
    conversions: number;
    spend: number;
    ctr: number | null;
    cpc: number | null;
    cpa: number | null;
}

interface DailyMetric {
    date: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
}

interface TopCampaign {
    id: number;
    name: string;
    platform: string;
    spend: number;
    clicks: number;
    ctr: number;
    conversions: number;
}

// Metric card with trend and optional tooltip
function MetricCard({
    title,
    value,
    change,
    icon: Icon,
    format = "number",
    prefix = "",
    suffix = "",
    metric
}: {
    title: string;
    value: number | null;
    change?: number;
    icon: any;
    format?: "number" | "currency" | "percent";
    prefix?: string;
    suffix?: string;
    metric?: "spend" | "cpc" | "cpm" | "cpa" | "impressions" | "clicks" | "ctr" | "conversions" | "cr" | "roas";
}) {
    const formatValue = (v: number | null) => {
        if (v === null) return "—";
        if (format === "currency") return `${prefix}${v.toLocaleString("ru-RU")}${suffix}`;
        if (format === "percent") return `${v.toFixed(2)}%`;
        return `${prefix}${v.toLocaleString("ru-RU")}${suffix}`;
    };

    const isPositive = change !== undefined && change >= 0;

    return (
        <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-accent/5 rounded-bl-full" />
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    <span className="flex items-center gap-1">
                        {title}
                        {metric && (
                            <span className="relative group">
                                <HelpCircle className="h-3.5 w-3.5 text-muted/50 hover:text-accent cursor-help transition-colors" />
                                <span className="absolute z-50 left-0 top-6 hidden group-hover:block w-64 p-2 text-xs bg-panel border border-border rounded-lg shadow-xl">
                                    {metric === "ctr" && "CTR = (Клики / Показы) × 100%. Хороший: 1-5%"}
                                    {metric === "cpc" && "CPC = Расходы / Клики. Чем ниже — тем лучше."}
                                    {metric === "cpa" && "CPA = Расходы / Конверсии. Сравните с LTV."}
                                    {metric === "spend" && "Общие расходы на рекламу за период."}
                                    {metric === "impressions" && "Сколько раз показано объявление."}
                                    {metric === "clicks" && "Количество кликов по объявлениям."}
                                    {metric === "conversions" && "Целевые действия (покупки, заявки)."}
                                    {metric === "roas" && "ROAS = Доход / Расходы × 100%. >300% = прибыль"}
                                </span>
                            </span>
                        )}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-text">{formatValue(value)}</div>
                {change !== undefined && (
                    <div className={`flex items-center gap-1 text-sm mt-1 ${isPositive ? "text-success" : "text-danger"}`}>
                        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        <span>{isPositive ? "+" : ""}{change.toFixed(1)}%</span>
                        <span className="text-muted">vs прошлый период</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

// Simple sparkline chart
function SparklineChart({ data, color = "#8b5cf6" }: { data: number[]; color?: string }) {
    if (!data.length) return null;

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((v, i) => {
        const x = (i / (data.length - 1)) * 100;
        const y = 100 - ((v - min) / range) * 80;
        return `${x},${y}`;
    }).join(" ");

    return (
        <svg className="w-full h-16" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="2"
                points={points}
            />
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
            <polygon
                fill="url(#gradient)"
                points={`0,100 ${points} 100,100`}
            />
        </svg>
    );
}

export default function DashboardPage() {
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState<"7d" | "30d">("7d");
    const [summary, setSummary] = useState<KpiSummary | null>(null);
    const [dailyData, setDailyData] = useState<DailyMetric[]>([]);
    const [topCampaigns, setTopCampaigns] = useState<TopCampaign[]>([]);
    const [hasConnections, setHasConnections] = useState(true);

    useEffect(() => {
        loadDashboard();
    }, [period]);

    const loadDashboard = async () => {
        setLoading(true);
        try {
            const days = period === "7d" ? 7 : 30;
            const dateTo = new Date().toISOString().split("T")[0];
            const dateFromObj = new Date();
            dateFromObj.setDate(dateFromObj.getDate() - days);
            const dateFrom = dateFromObj.toISOString().split("T")[0];

            const [summaryData, timeseriesData, connData] = await Promise.all([
                getKpiSummary({ date_from: dateFrom, date_to: dateTo }),
                getKpiTimeseries({ date_from: dateFrom, date_to: dateTo, mode: "absolute" }),
                listConnections()
            ]);

            setSummary({
                ...summaryData,
                ctr: summaryData.ctr,
                cpc: summaryData.cpc,
                cpa: summaryData.cpa
            });
            setDailyData(timeseriesData.items || []);
            setHasConnections(connData.items?.length > 0);

        } catch (err) {
            console.error("Dashboard load error:", err);
            toast.error("Не удалось загрузить данные дашборда");
        } finally {
            setLoading(false);
        }
    };

    const spendData = useMemo(() => dailyData.map(d => d.spend), [dailyData]);
    const clicksData = useMemo(() => dailyData.map(d => d.clicks), [dailyData]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-accent" />
            </div>
        );
    }

    // Onboarding state
    if (!hasConnections) {
        return (
            <div className="space-y-6">
                <PageHeader title="Добро пожаловать в Reklai!" />

                <Card className="border-accent/30 bg-accent/5">
                    <CardContent className="py-12 text-center">
                        <Sparkles className="h-16 w-16 text-accent mx-auto mb-6" />
                        <h2 className="text-2xl font-bold text-text mb-4">
                            Начните с подключения рекламного кабинета
                        </h2>
                        <p className="text-muted max-w-md mx-auto mb-8">
                            Подключите Яндекс.Директ, чтобы увидеть статистику,
                            получать рекомендации и автоматизировать управление рекламой.
                        </p>
                        <Button size="lg" asChild>
                            <Link href="/connections">
                                <ArrowUpRight className="mr-2 h-5 w-5" />
                                Подключить Яндекс.Директ
                            </Link>
                        </Button>
                    </CardContent>
                </Card>

                {/* Quick actions */}
                <div className="grid md:grid-cols-3 gap-4">
                    <Card className="hover:border-accent/50 transition-colors cursor-pointer" onClick={() => window.location.href = "/magic-launch"}>
                        <CardContent className="py-6 text-center">
                            <Sparkles className="h-8 w-8 text-accent mx-auto mb-3" />
                            <h3 className="font-medium text-text">🚀 Запуск рекламы</h3>
                            <p className="text-sm text-muted mt-1">Один клик — реклама работает</p>
                        </CardContent>
                    </Card>
                    <Card className="hover:border-accent/50 transition-colors cursor-pointer" onClick={() => window.location.href = "/campaigns"}>
                        <CardContent className="py-6 text-center">
                            <Target className="h-8 w-8 text-accent mx-auto mb-3" />
                            <h3 className="font-medium text-text">Кампании</h3>
                            <p className="text-sm text-muted mt-1">Управление рекламой</p>
                        </CardContent>
                    </Card>
                    <Card className="hover:border-accent/50 transition-colors cursor-pointer" onClick={() => window.location.href = "/billing"}>
                        <CardContent className="py-6 text-center">
                            <DollarSign className="h-8 w-8 text-accent mx-auto mb-3" />
                            <h3 className="font-medium text-text">Баланс</h3>
                            <p className="text-sm text-muted mt-1">Пополнить счёт</p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <PageHeader title="Дашборд" subtitle="Сводка по всем кампаниям" />
                <div className="flex items-center gap-2">
                    <div className="flex bg-panel-strong rounded-lg p-1">
                        <button
                            onClick={() => setPeriod("7d")}
                            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${period === "7d" ? "bg-accent text-white" : "text-muted hover:text-text"
                                }`}
                        >
                            7 дней
                        </button>
                        <button
                            onClick={() => setPeriod("30d")}
                            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${period === "30d" ? "bg-accent text-white" : "text-muted hover:text-text"
                                }`}
                        >
                            30 дней
                        </button>
                    </div>
                    <Button variant="outline" size="sm" onClick={loadDashboard}>
                        <RefreshCw className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                    title="Расходы"
                    value={summary?.spend ?? 0}
                    icon={DollarSign}
                    format="currency"
                    suffix=" ₽"
                    metric="spend"
                />
                <MetricCard
                    title="Показы"
                    value={summary?.impressions ?? 0}
                    icon={Eye}
                    metric="impressions"
                />
                <MetricCard
                    title="Клики"
                    value={summary?.clicks ?? 0}
                    icon={MousePointer}
                    metric="clicks"
                />
                <MetricCard
                    title="CTR"
                    value={summary?.ctr ?? null}
                    icon={TrendingUp}
                    format="percent"
                    metric="ctr"
                />
            </div>

            {/* Charts Row */}
            <div className="grid md:grid-cols-2 gap-4">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Расходы за период</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {spendData.length > 0 ? (
                            <SparklineChart data={spendData} color="#8b5cf6" />
                        ) : (
                            <div className="h-16 flex items-center justify-center text-muted text-sm">
                                Нет данных
                            </div>
                        )}
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Клики за период</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {clicksData.length > 0 ? (
                            <SparklineChart data={clicksData} color="#06b6d4" />
                        ) : (
                            <div className="h-16 flex items-center justify-center text-muted text-sm">
                                Нет данных
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-4 gap-4">
                <Card className="hover:border-accent/50 transition-colors">
                    <Link href="/magic-launch" className="block">
                        <CardContent className="py-4 flex items-center gap-3">
                            <div className="p-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-lg">
                                <Sparkles className="h-5 w-5 text-yellow-500" />
                            </div>
                            <div>
                                <div className="font-medium text-text">🚀 Запустить</div>
                                <div className="text-xs text-muted">Новая кампания</div>
                            </div>
                        </CardContent>
                    </Link>
                </Card>
                <Card className="hover:border-accent/50 transition-colors">
                    <Link href="/campaigns" className="block">
                        <CardContent className="py-4 flex items-center gap-3">
                            <div className="p-2 bg-accent/10 rounded-lg">
                                <Target className="h-5 w-5 text-accent" />
                            </div>
                            <div>
                                <div className="font-medium text-text">Кампании</div>
                                <div className="text-xs text-muted">Управление</div>
                            </div>
                        </CardContent>
                    </Link>
                </Card>
                <Card className="hover:border-accent/50 transition-colors">
                    <Link href="/drafts" className="block">
                        <CardContent className="py-4 flex items-center gap-3">
                            <div className="p-2 bg-accent/10 rounded-lg">
                                <AlertCircle className="h-5 w-5 text-accent" />
                            </div>
                            <div>
                                <div className="font-medium text-text">Черновики</div>
                                <div className="text-xs text-muted">Незапущенные</div>
                            </div>
                        </CardContent>
                    </Link>
                </Card>
                <Card className="hover:border-accent/50 transition-colors">
                    <Link href="/connections" className="block">
                        <CardContent className="py-4 flex items-center gap-3">
                            <div className="p-2 bg-accent/10 rounded-lg">
                                <TrendingUp className="h-5 w-5 text-accent" />
                            </div>
                            <div>
                                <div className="font-medium text-text">Подключения</div>
                                <div className="text-xs text-muted">Рекламные площадки</div>
                            </div>
                        </CardContent>
                    </Link>
                </Card>
            </div>
        </div>
    );
}
