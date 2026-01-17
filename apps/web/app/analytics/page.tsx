"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    TrendingUp, TrendingDown, Eye, MousePointer, DollarSign, Target,
    BarChart3, Loader2, RefreshCw, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { toast } from "sonner";

// Mock data - will be replaced with API calls
const mockSummary = {
    impressions: 458920,
    clicks: 18540,
    spend: 542890.50,
    conversions: 1245,
    revenue: 2456780.00,
    ctr: 4.04,
    cpc: 29.28,
    conversion_rate: 6.72,
    roas: 4.52
};

const mockChanges = {
    impressions: 12.5,
    clicks: 8.3,
    spend: -5.2,
    conversions: 15.8,
    ctr: -3.4,
    roas: 22.1
};

const mockTimeseries = [
    { date: "2026-01-01", value: 12500 },
    { date: "2026-01-02", value: 14200 },
    { date: "2026-01-03", value: 13800 },
    { date: "2026-01-04", value: 15600 },
    { date: "2026-01-05", value: 16200 },
    { date: "2026-01-06", value: 15800 },
    { date: "2026-01-07", value: 17200 },
];

const mockPlatforms = [
    { platform: "yandex", impressions: 245000, clicks: 10200, spend: 298500, roas: 4.8, ctr: 4.16 },
    { platform: "google", impressions: 148000, clicks: 5800, spend: 178200, roas: 4.2, ctr: 3.92 },
    { platform: "vk", impressions: 65920, clicks: 2540, spend: 66190, roas: 3.9, ctr: 3.85 },
];

const PLATFORM_NAMES: Record<string, string> = {
    yandex: "Яндекс Директ",
    google: "Google Ads",
    vk: "VK Реклама"
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
    const formatValue = () => {
        if (format === "currency") return `₽${value.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}`;
        if (format === "percent") return `${value.toFixed(2)}%`;
        return value.toLocaleString('ru-RU');
    };

    const isPositive = change && change > 0;
    const isNegative = change && change < 0;

    return (
        <Card className="glass-card border-white/5">
            <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                    <div className="p-2 bg-accent/20 rounded-lg">
                        <Icon className="h-5 w-5 text-accent" />
                    </div>
                    {change !== undefined && (
                        <div className={`flex items-center text-sm ${isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-gray-400'}`}>
                            {isPositive ? <ArrowUpRight className="h-4 w-4" /> : isNegative ? <ArrowDownRight className="h-4 w-4" /> : null}
                            {Math.abs(change)}%
                        </div>
                    )}
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                    {prefix}{formatValue()}{suffix}
                </div>
                <div className="text-sm text-gray-400">{title}</div>
            </CardContent>
        </Card>
    );
}

function MiniChart({ data }: { data: Array<{ date: string; value: number }> }) {
    const maxValue = Math.max(...data.map(d => d.value));

    return (
        <div className="flex items-end gap-1 h-16">
            {data.map((point, idx) => (
                <div
                    key={idx}
                    className="flex-1 bg-accent/60 rounded-t hover:bg-accent transition-colors"
                    style={{ height: `${(point.value / maxValue) * 100}%` }}
                    title={`${point.date}: ${point.value.toLocaleString()}`}
                />
            ))}
        </div>
    );
}

export default function AnalyticsPage() {
    const [loading, setLoading] = useState(false);
    const [period, setPeriod] = useState("30d");
    const [platform, setPlatform] = useState("all");
    const [summary, setSummary] = useState(mockSummary);
    const [changes, setChanges] = useState(mockChanges);
    const [timeseries, setTimeseries] = useState(mockTimeseries);
    const [platforms, setPlatforms] = useState(mockPlatforms);

    const refresh = () => {
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            toast.success("Данные обновлены");
        }, 1000);
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">Аналитика</h1>
                    <p className="text-gray-400 mt-1">Сводные данные по всем рекламным платформам</p>
                </div>
                <div className="flex gap-3">
                    <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger className="w-32 bg-black/30 border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="7d">7 дней</SelectItem>
                            <SelectItem value="30d">30 дней</SelectItem>
                            <SelectItem value="90d">90 дней</SelectItem>
                        </SelectContent>
                    </Select>
                    <Select value={platform} onValueChange={setPlatform}>
                        <SelectTrigger className="w-40 bg-black/30 border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Все платформы</SelectItem>
                            <SelectItem value="yandex">Яндекс Директ</SelectItem>
                            <SelectItem value="google">Google Ads</SelectItem>
                            <SelectItem value="vk">VK Реклама</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={refresh} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Обновить
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                    title="Показы"
                    value={summary.impressions}
                    change={changes.impressions}
                    icon={Eye}
                />
                <MetricCard
                    title="Клики"
                    value={summary.clicks}
                    change={changes.clicks}
                    icon={MousePointer}
                />
                <MetricCard
                    title="Расход"
                    value={summary.spend}
                    change={changes.spend}
                    icon={DollarSign}
                    format="currency"
                />
                <MetricCard
                    title="Конверсии"
                    value={summary.conversions}
                    change={changes.conversions}
                    icon={Target}
                />
            </div>

            {/* Secondary KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                    title="CTR"
                    value={summary.ctr}
                    change={changes.ctr}
                    icon={TrendingUp}
                    format="percent"
                />
                <MetricCard
                    title="CPC"
                    value={summary.cpc}
                    icon={DollarSign}
                    prefix="₽"
                />
                <MetricCard
                    title="Конверсия"
                    value={summary.conversion_rate}
                    icon={Target}
                    format="percent"
                />
                <MetricCard
                    title="ROAS"
                    value={summary.roas}
                    change={changes.roas}
                    icon={TrendingUp}
                    suffix="x"
                />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
                {/* Chart */}
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <BarChart3 className="h-5 w-5 text-accent" />
                            Показы за период
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <MiniChart data={timeseries} />
                        <div className="flex justify-between text-xs text-gray-500 mt-2">
                            <span>{timeseries[0]?.date}</span>
                            <span>{timeseries[timeseries.length - 1]?.date}</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Platform Breakdown */}
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle className="text-white">По платформам</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {platforms.map((p) => {
                                const totalSpend = platforms.reduce((s, pl) => s + pl.spend, 0);
                                const percentage = (p.spend / totalSpend) * 100;

                                return (
                                    <div key={p.platform} className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <span className="text-white font-medium">{PLATFORM_NAMES[p.platform]}</span>
                                            <span className="text-gray-400 text-sm">₽{p.spend.toLocaleString()}</span>
                                        </div>
                                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-accent to-accent-2 rounded-full"
                                                style={{ width: `${percentage}%` }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-xs text-gray-500">
                                            <span>CTR: {p.ctr}%</span>
                                            <span>ROAS: {p.roas}x</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
