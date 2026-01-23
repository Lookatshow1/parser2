"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
    DollarSign, Zap,
    History, Settings, ArrowUpRight, ArrowDownRight, Loader2, Play
} from "lucide-react";
import { toast } from "sonner";
import {
    AutomationAction,
    AutomationRun,
    AutomationSettings,
    getAutomationSettings,
    updateAutomationSettings,
    listAutomationRuns,
    listAutomationActions,
    runAutomation,
    getMetricsBreakdown,
    getBudgetAllocation
} from "@/lib/api";

type BudgetRecommendation = {
    id: number;
    name: string;
    platform: string;
    current_budget: number;
    recommended_budget: number;
    change_percentage: number;
    reason: string;
    roas: number;
    status: "pending";
};

const PLATFORM_NAMES: Record<string, string> = {
    yandex: "Яндекс Директ",
    google: "Google Ads",
    vk: "VK Реклама",
    ozon: "Ozon"
};

const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
};

const buildDateRange = (days: number) => {
    const dateTo = new Date();
    dateTo.setHours(0, 0, 0, 0);
    const dateFrom = new Date(dateTo);
    dateFrom.setDate(dateFrom.getDate() - (days - 1));
    return { dateFrom: formatDate(dateFrom), dateTo: formatDate(dateTo) };
};

export default function BudgetOptimizerPage() {
    const [recommendations, setRecommendations] = useState<BudgetRecommendation[]>([]);
    const [loading, setLoading] = useState(false);
    const [tab, setTab] = useState<"recommendations" | "rules" | "history">("recommendations");
    const [totalBudget, setTotalBudget] = useState("50000");
    const [rangeLabel, setRangeLabel] = useState("");
    const [budgetSummary, setBudgetSummary] = useState({ current: 0, recommended: 0 });

    const [automationSettings, setAutomationSettings] = useState<AutomationSettings | null>(null);
    const [automationRuns, setAutomationRuns] = useState<AutomationRun[]>([]);
    const [automationActions, setAutomationActions] = useState<AutomationAction[]>([]);
    const [automationLoading, setAutomationLoading] = useState(false);
    const [intervalMinutes, setIntervalMinutes] = useState("60");

    const generateRecommendations = async () => {
        setLoading(true);
        try {
            const rangeDays = 14;
            const { dateFrom, dateTo } = buildDateRange(rangeDays);
            setRangeLabel(`${dateFrom} → ${dateTo}`);

            const breakdown = await getMetricsBreakdown({
                date_from: dateFrom,
                date_to: dateTo,
                dimension: "campaign",
                limit: 500,
                order_by: "spend"
            });

            const items = (breakdown.items || []).filter((item) => item.id);
            if (!items.length) {
                setRecommendations([]);
                setBudgetSummary({ current: 0, recommended: 0 });
                toast("Нет данных для расчета бюджета");
                return;
            }

            const campaignMetrics: Record<number, { impressions: number; clicks: number; conversions: number; spend: number; revenue: number }> = {};
            const currentBudgetMap: Record<number, number> = {};

            items.forEach((item) => {
                const id = item.id as number;
                const conversions = item.purchases > 0 ? item.purchases : item.leads;
                campaignMetrics[id] = {
                    impressions: item.impressions,
                    clicks: item.clicks,
                    conversions,
                    spend: item.spend,
                    revenue: item.revenue
                };
                currentBudgetMap[id] = item.spend / rangeDays;
            });

            const currentTotalBudget = Object.values(currentBudgetMap).reduce((sum, value) => sum + value, 0);
            let totalBudgetValue = Number(totalBudget);
            if (!Number.isFinite(totalBudgetValue) || totalBudgetValue <= 0) {
                totalBudgetValue = Math.round(currentTotalBudget);
                if (totalBudgetValue > 0) {
                    setTotalBudget(String(totalBudgetValue));
                }
            }

            if (totalBudgetValue <= 0) {
                toast.error("Укажите общий бюджет");
                return;
            }

            const allocation = await getBudgetAllocation({
                total_budget: totalBudgetValue,
                campaign_metrics: campaignMetrics
            });

            const allocationMap = allocation.allocations || {};
            const nextRecommendations = items.map((item) => {
                const id = item.id as number;
                const currentBudget = currentBudgetMap[id] || 0;
                const recommendedBudget = allocationMap[String(id)] ?? currentBudget;
                const changePercentage = currentBudget ? ((recommendedBudget - currentBudget) / currentBudget) * 100 : 0;
                const roas = item.roas ?? (item.spend ? item.revenue / item.spend : 0);
                const reason = roas > 0
                    ? `ROAS ${roas.toFixed(2)}x — перераспределите бюджет в пользу лучших кампаний`
                    : "Недостаточно данных для расчета ROAS";

                return {
                    id,
                    name: item.name || `Кампания #${item.external_id}`,
                    platform: String(item.platform),
                    current_budget: currentBudget,
                    recommended_budget: recommendedBudget,
                    change_percentage: Number(changePercentage.toFixed(1)),
                    reason,
                    roas,
                    status: "pending" as const
                };
            }).sort((a, b) => Math.abs(b.change_percentage) - Math.abs(a.change_percentage));

            setRecommendations(nextRecommendations);

            const totalRecommendedBudget = nextRecommendations.reduce((sum, item) => sum + item.recommended_budget, 0);
            setBudgetSummary({
                current: currentTotalBudget,
                recommended: totalRecommendedBudget
            });
        } catch (error) {
            toast.error("Не удалось сформировать рекомендации");
        } finally {
            setLoading(false);
        }
    };

    const loadAutomation = async () => {
        setAutomationLoading(true);
        try {
            const [settings, runs, actions] = await Promise.all([
                getAutomationSettings(),
                listAutomationRuns({ limit: 10 }),
                listAutomationActions({ limit: 20 })
            ]);
            setAutomationSettings(settings);
            setAutomationRuns(runs || []);
            setAutomationActions(actions || []);
        } catch (error) {
            toast.error("Не удалось загрузить автопилот");
        } finally {
            setAutomationLoading(false);
        }
    };

    useEffect(() => {
        generateRecommendations();
        loadAutomation();
    }, []);

    useEffect(() => {
        if (automationSettings) {
            setIntervalMinutes(String(automationSettings.run_interval_minutes));
        }
    }, [automationSettings]);

    const totalSavings = recommendations
        .filter((r) => r.change_percentage < 0)
        .reduce((sum, r) => sum + (r.current_budget - r.recommended_budget), 0);

    const handleToggleAutomation = async (enabled: boolean) => {
        if (!automationSettings) return;
        setAutomationLoading(true);
        try {
            const updated = await updateAutomationSettings({ is_enabled: enabled });
            setAutomationSettings(updated);
            toast.success(enabled ? "Автопилот включен" : "Автопилот выключен");
        } catch (error) {
            toast.error("Не удалось обновить настройки");
        } finally {
            setAutomationLoading(false);
        }
    };

    const handleSaveInterval = async () => {
        const value = Number(intervalMinutes);
        if (!Number.isFinite(value) || value < 5) {
            toast.error("Интервал должен быть не меньше 5 минут");
            return;
        }
        setAutomationLoading(true);
        try {
            const updated = await updateAutomationSettings({ run_interval_minutes: value });
            setAutomationSettings(updated);
            toast.success("Интервал обновлен");
        } catch (error) {
            toast.error("Не удалось сохранить интервал");
        } finally {
            setAutomationLoading(false);
        }
    };

    const handleRunAutomation = async () => {
        setAutomationLoading(true);
        try {
            await runAutomation();
            toast.success("Автопилот запущен");
            await loadAutomation();
        } catch (error) {
            toast.error("Не удалось запустить автопилот");
        } finally {
            setAutomationLoading(false);
        }
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">Бюджет-оптимизатор</h1>
                    <p className="text-gray-400 mt-1">AI-рекомендации по перераспределению бюджета</p>
                </div>
                <div className="flex items-end gap-3">
                    <div>
                        <Label className="text-xs text-gray-400">Бюджет, ₽/день</Label>
                        <Input
                            value={totalBudget}
                            onChange={(e) => setTotalBudget(e.target.value)}
                            className="w-36 bg-black/20 border-white/10 text-white"
                            inputMode="numeric"
                        />
                    </div>
                    <Button onClick={generateRecommendations} className="bg-accent hover:bg-accent/80" disabled={loading}>
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Zap className="mr-2 h-4 w-4" />}
                        Сгенерировать
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-8">
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-white">
                            ₽{budgetSummary.current.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-sm text-gray-400">Текущий дневной бюджет</div>
                    </CardContent>
                </Card>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-accent">
                            ₽{budgetSummary.recommended.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-sm text-gray-400">Рекомендованный дневной бюджет</div>
                    </CardContent>
                </Card>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-green-400">
                            ₽{totalSavings.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-sm text-gray-400">Потенциальная экономия</div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex gap-2 mb-6">
                <Button
                    variant={tab === "recommendations" ? "default" : "outline"}
                    onClick={() => setTab("recommendations")}
                >
                    <DollarSign className="mr-2 h-4 w-4" />
                    Рекомендации
                </Button>
                <Button
                    variant={tab === "rules" ? "default" : "outline"}
                    onClick={() => setTab("rules")}
                >
                    <Settings className="mr-2 h-4 w-4" />
                    Автопилот
                </Button>
                <Button
                    variant={tab === "history" ? "default" : "outline"}
                    onClick={() => setTab("history")}
                >
                    <History className="mr-2 h-4 w-4" />
                    История
                </Button>
            </div>

            {tab === "recommendations" && (
                <div className="space-y-4">
                    {rangeLabel && <div className="text-xs text-gray-500">Период анализа: {rangeLabel}</div>}
                    {recommendations.map((rec) => {
                        const isPositive = rec.change_percentage > 0;
                        const isNegative = rec.change_percentage < 0;

                        return (
                            <Card key={rec.id} className="glass-card border-white/5">
                                <CardContent className="p-6">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-3">
                                                <span className="text-xl font-bold text-white">
                                                    {rec.name}
                                                </span>
                                                <Badge className={`${isPositive ? "bg-green-500/20 text-green-400" :
                                                    isNegative ? "bg-red-500/20 text-red-400" :
                                                        "bg-gray-500/20 text-gray-400"
                                                    }`}>
                                                    {isPositive ? <ArrowUpRight className="h-3 w-3 mr-1" /> :
                                                        isNegative ? <ArrowDownRight className="h-3 w-3 mr-1" /> : null}
                                                    {rec.change_percentage > 0 ? "+" : ""}{rec.change_percentage}%
                                                </Badge>
                                                <Badge className="bg-white/10 text-gray-300">
                                                    {PLATFORM_NAMES[rec.platform] || rec.platform.toUpperCase()}
                                                </Badge>
                                            </div>

                                            <div className="flex items-center gap-8 mb-3">
                                                <div>
                                                    <div className="text-xs text-gray-500">Текущий бюджет</div>
                                                    <div className="text-lg text-white">₽{rec.current_budget.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}/день</div>
                                                </div>
                                                <div className="text-2xl text-gray-600">→</div>
                                                <div>
                                                    <div className="text-xs text-gray-500">Рекомендуемый</div>
                                                    <div className={`text-lg font-bold ${isPositive ? "text-green-400" : isNegative ? "text-red-400" : "text-white"}`}>
                                                        ₽{rec.recommended_budget.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}/день
                                                    </div>
                                                </div>
                                            </div>

                                            <p className="text-sm text-gray-400">{rec.reason}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                    {!loading && recommendations.length === 0 && (
                        <div className="text-center py-12 border border-dashed border-white/10 rounded-xl text-gray-400">
                            Нет данных для рекомендаций. Проверьте синхронизацию подключений.
                        </div>
                    )}
                </div>
            )}

            {tab === "rules" && (
                <div className="space-y-4">
                    <Card className="glass-card border-white/5">
                        <CardHeader>
                            <CardTitle className="text-white">Автопилот оптимизаций</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-white font-medium">Включить автопилот</div>
                                    <div className="text-xs text-gray-500">Автоматически генерирует действия по рекомендациям</div>
                                </div>
                                <Switch
                                    checked={automationSettings?.is_enabled ?? false}
                                    onCheckedChange={handleToggleAutomation}
                                    disabled={automationLoading}
                                />
                            </div>
                            <div className="grid md:grid-cols-3 gap-4 items-end">
                                <div>
                                    <Label className="text-xs text-gray-400">Интервал, мин</Label>
                                    <Input
                                        value={intervalMinutes}
                                        onChange={(e) => setIntervalMinutes(e.target.value)}
                                        className="bg-black/20 border-white/10 text-white"
                                        inputMode="numeric"
                                    />
                                </div>
                                <Button onClick={handleSaveInterval} variant="outline" disabled={automationLoading}>
                                    Сохранить интервал
                                </Button>
                                <Button onClick={handleRunAutomation} className="bg-accent hover:bg-accent/80" disabled={automationLoading}>
                                    <Play className="mr-2 h-4 w-4" />
                                    Запустить сейчас
                                </Button>
                            </div>
                            {automationSettings?.last_run_at && (
                                <div className="text-xs text-gray-500">
                                    Последний запуск: {new Date(automationSettings.last_run_at).toLocaleString("ru-RU")}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="glass-card border-white/5">
                        <CardHeader>
                            <CardTitle className="text-white">Последние действия автопилота</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {automationActions.slice(0, 6).map((action) => (
                                <div key={action.id} className="p-4 rounded-lg border border-white/10 bg-black/20">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-medium">{action.title}</div>
                                            <div className="text-sm text-gray-400">{action.description}</div>
                                        </div>
                                        <Badge className="bg-white/10 text-gray-300">{action.status}</Badge>
                                    </div>
                                </div>
                            ))}
                            {automationActions.length === 0 && (
                                <div className="text-sm text-gray-500">Пока нет действий автопилота.</div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}

            {tab === "history" && (
                <Card className="glass-card border-white/5">
                    <CardContent className="p-0">
                        <div className="divide-y divide-white/5">
                            {automationRuns.map((run) => (
                                <div key={run.id} className="p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                                            <History className="h-5 w-5 text-accent" />
                                        </div>
                                        <div>
                                            <div className="font-medium text-white">Запуск автопилота</div>
                                            <div className="text-xs text-gray-500">
                                                {new Date(run.created_at).toLocaleString("ru-RU")} • {run.status}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        {run.result_json?.actions_created ? `Действий: ${run.result_json.actions_created}` : "—"}
                                    </div>
                                </div>
                            ))}
                            {automationRuns.length === 0 && (
                                <div className="p-6 text-sm text-gray-500">История автопилота пуста.</div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
