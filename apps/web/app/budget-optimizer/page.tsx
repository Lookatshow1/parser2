"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
    TrendingUp, TrendingDown, DollarSign, Zap, Check, X,
    History, Settings, ArrowUpRight, ArrowDownRight, Loader2, Plus
} from "lucide-react";
import { toast } from "sonner";

// Mock data
const mockRecommendations = [
    {
        id: 1,
        platform: "yandex",
        current_budget: 15000,
        recommended_budget: 17250,
        change_percentage: 15,
        reason: "ROAS 4.8x — эффективнее других платформ",
        expected_roas_improvement: 8.5,
        status: "pending"
    },
    {
        id: 2,
        platform: "google",
        current_budget: 12000,
        recommended_budget: 12000,
        change_percentage: 0,
        reason: "ROAS 4.2x — в пределах нормы",
        expected_roas_improvement: 0,
        status: "pending"
    },
    {
        id: 3,
        platform: "vk",
        current_budget: 8000,
        recommended_budget: 6800,
        change_percentage: -15,
        reason: "ROAS 2.9x — ниже среднего, рекомендуем снизить",
        expected_roas_improvement: 0,
        status: "pending"
    }
];

const mockRules = [
    {
        id: 1,
        name: "Пауза при низком CTR",
        description: "Если CTR < 1%, приостановить объявление",
        rule_type: "pause_low_ctr",
        is_enabled: true,
        trigger_count: 12
    },
    {
        id: 2,
        name: "Увеличение бюджета при высоком ROAS",
        description: "Если ROAS > 5x, увеличить дневной бюджет на 10%",
        rule_type: "increase_high_roas",
        is_enabled: true,
        trigger_count: 5
    },
    {
        id: 3,
        name: "Ночное снижение ставок",
        description: "С 23:00 до 07:00 снижать ставки на 30%",
        rule_type: "dayparting",
        is_enabled: false,
        trigger_count: 0
    }
];

const mockHistory = [
    {
        id: 1,
        action_type: "budget_change",
        description: "Увеличен бюджет Яндекс Директ",
        platform: "yandex",
        before_value: 12000,
        after_value: 15000,
        created_at: "2026-01-16T10:30:00Z"
    },
    {
        id: 2,
        action_type: "pause_campaign",
        description: "Приостановлена кампания с низким CTR",
        platform: "google",
        created_at: "2026-01-15T14:22:00Z"
    }
];

const PLATFORM_NAMES: Record<string, string> = {
    yandex: "Яндекс Директ",
    google: "Google Ads",
    vk: "VK Реклама"
};

export default function BudgetOptimizerPage() {
    const [recommendations, setRecommendations] = useState(mockRecommendations);
    const [rules, setRules] = useState(mockRules);
    const [history, setHistory] = useState(mockHistory);
    const [loading, setLoading] = useState(false);
    const [tab, setTab] = useState<"recommendations" | "rules" | "history">("recommendations");

    const applyRecommendation = (id: number) => {
        setRecommendations(recs => recs.map(r =>
            r.id === id ? { ...r, status: "applied" } : r
        ));
        toast.success("Рекомендация применена!");
    };

    const rejectRecommendation = (id: number) => {
        setRecommendations(recs => recs.map(r =>
            r.id === id ? { ...r, status: "rejected" } : r
        ));
        toast.success("Рекомендация отклонена");
    };

    const toggleRule = (id: number) => {
        setRules(rs => rs.map(r =>
            r.id === id ? { ...r, is_enabled: !r.is_enabled } : r
        ));
        toast.success("Правило обновлено");
    };

    const generateRecommendations = () => {
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            toast.success("Новые рекомендации сгенерированы!");
        }, 2000);
    };

    const totalSavings = recommendations
        .filter(r => r.status === "pending" && r.change_percentage < 0)
        .reduce((sum, r) => sum + (r.current_budget - r.recommended_budget), 0);

    const totalGrowth = recommendations
        .filter(r => r.status === "pending" && r.change_percentage > 0)
        .reduce((sum, r) => sum + r.expected_roas_improvement, 0);

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">Бюджет-оптимизатор</h1>
                    <p className="text-gray-400 mt-1">AI-рекомендации по распределению бюджета</p>
                </div>
                <Button onClick={generateRecommendations} className="bg-accent hover:bg-accent/80" disabled={loading}>
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Zap className="mr-2 h-4 w-4" />}
                    Сгенерировать рекомендации
                </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-4 mb-8">
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-green-400">
                            ₽{totalSavings.toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-400">Потенциальная экономия</div>
                    </CardContent>
                </Card>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-accent">
                            +{totalGrowth.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-400">Ожидаемый рост ROAS</div>
                    </CardContent>
                </Card>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-6">
                        <div className="text-3xl font-bold text-white">
                            {rules.filter(r => r.is_enabled).length}
                        </div>
                        <div className="text-sm text-gray-400">Активных правил</div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabs */}
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
                    Правила ({rules.length})
                </Button>
                <Button
                    variant={tab === "history" ? "default" : "outline"}
                    onClick={() => setTab("history")}
                >
                    <History className="mr-2 h-4 w-4" />
                    История
                </Button>
            </div>

            {/* Recommendations Tab */}
            {tab === "recommendations" && (
                <div className="space-y-4">
                    {recommendations.map((rec) => {
                        const isPositive = rec.change_percentage > 0;
                        const isNegative = rec.change_percentage < 0;
                        const isPending = rec.status === "pending";

                        return (
                            <Card key={rec.id} className={`glass-card border-white/5 ${!isPending && 'opacity-60'}`}>
                                <CardContent className="p-6">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-3">
                                                <span className="text-xl font-bold text-white">
                                                    {PLATFORM_NAMES[rec.platform]}
                                                </span>
                                                <Badge className={`${isPositive ? 'bg-green-500/20 text-green-400' :
                                                        isNegative ? 'bg-red-500/20 text-red-400' :
                                                            'bg-gray-500/20 text-gray-400'
                                                    }`}>
                                                    {isPositive ? <ArrowUpRight className="h-3 w-3 mr-1" /> :
                                                        isNegative ? <ArrowDownRight className="h-3 w-3 mr-1" /> : null}
                                                    {rec.change_percentage > 0 ? '+' : ''}{rec.change_percentage}%
                                                </Badge>
                                                {rec.status !== "pending" && (
                                                    <Badge className={rec.status === "applied" ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'}>
                                                        {rec.status === "applied" ? 'Применено' : 'Отклонено'}
                                                    </Badge>
                                                )}
                                            </div>

                                            <div className="flex items-center gap-8 mb-3">
                                                <div>
                                                    <div className="text-xs text-gray-500">Текущий бюджет</div>
                                                    <div className="text-lg text-white">₽{rec.current_budget.toLocaleString()}/день</div>
                                                </div>
                                                <div className="text-2xl text-gray-600">→</div>
                                                <div>
                                                    <div className="text-xs text-gray-500">Рекомендуемый</div>
                                                    <div className={`text-lg font-bold ${isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-white'}`}>
                                                        ₽{rec.recommended_budget.toLocaleString()}/день
                                                    </div>
                                                </div>
                                            </div>

                                            <p className="text-sm text-gray-400">{rec.reason}</p>

                                            {rec.expected_roas_improvement > 0 && (
                                                <div className="mt-2 text-sm text-green-400">
                                                    Ожидаемый рост ROAS: +{rec.expected_roas_improvement}%
                                                </div>
                                            )}
                                        </div>

                                        {isPending && (
                                            <div className="flex gap-2">
                                                <Button
                                                    size="sm"
                                                    onClick={() => applyRecommendation(rec.id)}
                                                    className="bg-green-600 hover:bg-green-500"
                                                >
                                                    <Check className="h-4 w-4 mr-1" /> Применить
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => rejectRecommendation(rec.id)}
                                                >
                                                    <X className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}

            {/* Rules Tab */}
            {tab === "rules" && (
                <div className="space-y-4">
                    {rules.map((rule) => (
                        <Card key={rule.id} className="glass-card border-white/5">
                            <CardContent className="p-6 flex justify-between items-center">
                                <div>
                                    <h3 className="text-lg font-medium text-white">{rule.name}</h3>
                                    <p className="text-sm text-gray-400 mt-1">{rule.description}</p>
                                    <div className="text-xs text-gray-500 mt-2">
                                        Сработало: {rule.trigger_count} раз
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <Badge className={rule.is_enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}>
                                        {rule.is_enabled ? 'Активно' : 'Выключено'}
                                    </Badge>
                                    <Switch
                                        checked={rule.is_enabled}
                                        onCheckedChange={() => toggleRule(rule.id)}
                                    />
                                </div>
                            </CardContent>
                        </Card>
                    ))}

                    <Card className="glass-card border-dashed border-white/20 cursor-pointer hover:border-accent/50 transition-colors">
                        <CardContent className="p-6 text-center text-gray-400">
                            <Plus className="h-8 w-8 mx-auto mb-2" />
                            <div>Создать новое правило</div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* History Tab */}
            {tab === "history" && (
                <Card className="glass-card border-white/5">
                    <CardContent className="p-0">
                        <div className="divide-y divide-white/5">
                            {history.map((item) => (
                                <div key={item.id} className="p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                                            <History className="h-5 w-5 text-accent" />
                                        </div>
                                        <div>
                                            <div className="font-medium text-white">{item.description}</div>
                                            <div className="text-xs text-gray-500">
                                                {item.platform && PLATFORM_NAMES[item.platform]} • {new Date(item.created_at).toLocaleString('ru-RU')}
                                            </div>
                                        </div>
                                    </div>
                                    {item.before_value !== undefined && item.after_value !== undefined && (
                                        <div className="text-sm text-gray-400">
                                            ₽{item.before_value.toLocaleString()} → ₽{item.after_value.toLocaleString()}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
