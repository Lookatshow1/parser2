"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import {
    TrendingUp, TrendingDown, Eye, MousePointer, DollarSign, Target,
    BarChart3, RefreshCw, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { toast } from "sonner";

// Дневные данные за последние 14 дней
const generateDailyData = () => {
    const data = [];
    const today = new Date();

    for (let i = 13; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);

        data.push({
            date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
            fullDate: date.toISOString().split('T')[0],
            impressions: Math.floor(30000 + Math.random() * 15000),
            clicks: Math.floor(900 + Math.random() * 600),
            spend: Math.floor(35000 + Math.random() * 20000),
            conversions: Math.floor(80 + Math.random() * 60),
        });
    }
    return data;
};

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

const mockPlatforms = [
    { platform: "yandex", name: "Яндекс Директ", impressions: 245000, clicks: 10200, spend: 298500, roas: 4.8, ctr: 4.16, color: "#FF5C00" },
    { platform: "vk", name: "VK Реклама", impressions: 148000, clicks: 5800, spend: 178200, roas: 4.2, ctr: 3.92, color: "#0077FF" },
    { platform: "ozon", name: "Ozon Performance", impressions: 65920, clicks: 2540, spend: 66190, roas: 3.9, ctr: 3.85, color: "#005BFF" },
];

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
            <CardContent className="p-5">
                <div className="flex justify-between items-start mb-3">
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
                        {entry.name}: {entry.value.toLocaleString('ru-RU')}
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
    const [dailyData, setDailyData] = useState(generateDailyData());

    const refresh = () => {
        setLoading(true);
        setTimeout(() => {
            setDailyData(generateDailyData());
            setLoading(false);
            toast.success("Данные обновлены");
        }, 1000);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
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
                        <SelectTrigger className="w-40 bg-black/30 border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Все платформы</SelectItem>
                            <SelectItem value="yandex">Яндекс Директ</SelectItem>
                            <SelectItem value="vk">VK Реклама</SelectItem>
                            <SelectItem value="ozon">Ozon</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={refresh} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Обновить
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard title="Показы" value={mockSummary.impressions} change={mockChanges.impressions} icon={Eye} />
                <MetricCard title="Клики" value={mockSummary.clicks} change={mockChanges.clicks} icon={MousePointer} />
                <MetricCard title="Расход" value={mockSummary.spend} change={mockChanges.spend} icon={DollarSign} format="currency" />
                <MetricCard title="Конверсии" value={mockSummary.conversions} change={mockChanges.conversions} icon={Target} />
            </div>

            {/* Main Chart - Impressions & Clicks */}
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
                {/* Spend Chart */}
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

                {/* Conversions Chart */}
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

            {/* Platform Breakdown */}
            <Card className="glass-card border-white/5">
                <CardHeader>
                    <CardTitle className="text-white">Распределение по платформам</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-6">
                        {mockPlatforms.map((p) => {
                            const totalSpend = mockPlatforms.reduce((s, pl) => s + pl.spend, 0);
                            const percentage = (p.spend / totalSpend) * 100;

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
                                        <span className="text-gray-400 text-sm">₽{p.spend.toLocaleString()}</span>
                                    </div>
                                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-500"
                                            style={{ width: `${percentage}%`, backgroundColor: p.color }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-500">
                                        <span>CTR: {p.ctr}%</span>
                                        <span>Показы: {p.impressions.toLocaleString()}</span>
                                        <span>Клики: {p.clicks.toLocaleString()}</span>
                                        <span>ROAS: {p.roas}x</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* Secondary KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard title="CTR" value={mockSummary.ctr} change={mockChanges.ctr} icon={TrendingUp} format="percent" />
                <MetricCard title="CPC" value={mockSummary.cpc} icon={DollarSign} prefix="₽" />
                <MetricCard title="Конверсия" value={mockSummary.conversion_rate} icon={Target} format="percent" />
                <MetricCard title="ROAS" value={mockSummary.roas} change={mockChanges.roas} icon={TrendingUp} suffix="x" />
            </div>
        </div>
    );
}
