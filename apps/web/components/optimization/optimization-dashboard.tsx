"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    TrendingUp, TrendingDown, Zap, Check, X,
    Loader2, RefreshCw, Target, ArrowRight, Lightbulb
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface OptimizationRecommendation {
    id: string;
    type: "increase_bid" | "decrease_bid" | "pause_ad" | "rewrite_ad" | "add_keyword" | "remove_keyword";
    priority: "high" | "medium" | "low";
    title: string;
    description: string;
    expectedImpact: string;
    adId?: number;
    currentValue?: string;
    suggestedValue?: string;
}

// Mock recommendations
const mockRecommendations: OptimizationRecommendation[] = [
    {
        id: "1",
        type: "increase_bid",
        priority: "high",
        title: "Повысить ставку для «услуги под ключ»",
        description: "CTR 4.2%, но показы падают. Конкуренция выросла на 15%.",
        expectedImpact: "+23% показов",
        currentValue: "₽45",
        suggestedValue: "₽58"
    },
    {
        id: "2",
        type: "pause_ad",
        priority: "high",
        title: "Приостановить объявление #1247",
        description: "CTR 0.8% — ниже среднего в 3 раза. Тратит бюджет неэффективно.",
        expectedImpact: "Экономия ₽2,400/нед",
        adId: 1247
    },
    {
        id: "3",
        type: "rewrite_ad",
        priority: "medium",
        title: "Переписать заголовок объявления #892",
        description: "Заголовок слишком длинный и обрезается на мобильных.",
        expectedImpact: "+15% CTR",
        currentValue: "Профессиональные услуги организации мероприятий",
        suggestedValue: "Мероприятия под ключ — от идеи до реализации"
    },
    {
        id: "4",
        type: "add_keyword",
        priority: "medium",
        title: "Добавить ключевое слово «корпоратив под ключ»",
        description: "Высокий потенциал: 2,400 запросов/мес, низкая конкуренция.",
        expectedImpact: "+180 показов/день"
    },
    {
        id: "5",
        type: "remove_keyword",
        priority: "low",
        title: "Удалить минус-слово «бесплатно»",
        description: "Теряете 12% потенциальных клиентов. Конверсия этой аудитории 3.2%.",
        expectedImpact: "+340 кликов/мес"
    }
];

const typeIcons = {
    increase_bid: TrendingUp,
    decrease_bid: TrendingDown,
    pause_ad: X,
    rewrite_ad: Lightbulb,
    add_keyword: Target,
    remove_keyword: X
};

const priorityColors = {
    high: "bg-red-500/20 text-red-400 border-red-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-blue-500/20 text-blue-400 border-blue-500/30"
};

const priorityLabels = {
    high: "Высокий",
    medium: "Средний",
    low: "Низкий"
};

interface OptimizationCardProps {
    recommendation: OptimizationRecommendation;
    onApply: (id: string) => void;
    onDismiss: (id: string) => void;
}

function OptimizationCard({ recommendation, onApply, onDismiss }: OptimizationCardProps) {
    const [applying, setApplying] = useState(false);
    const Icon = typeIcons[recommendation.type];

    const handleApply = async () => {
        setApplying(true);
        await new Promise(r => setTimeout(r, 1000));
        onApply(recommendation.id);
        setApplying(false);
    };

    return (
        <Card className="border-white/5 hover:border-accent/30 transition-colors">
            <CardContent className="p-4">
                <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={cn(
                        "p-3 rounded-lg",
                        recommendation.priority === "high" ? "bg-red-500/20" :
                            recommendation.priority === "medium" ? "bg-yellow-500/20" : "bg-blue-500/20"
                    )}>
                        <Icon className={cn(
                            "h-5 w-5",
                            recommendation.priority === "high" ? "text-red-400" :
                                recommendation.priority === "medium" ? "text-yellow-400" : "text-blue-400"
                        )} />
                    </div>

                    {/* Content */}
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-text">{recommendation.title}</h4>
                            <Badge className={priorityColors[recommendation.priority]}>
                                {priorityLabels[recommendation.priority]}
                            </Badge>
                        </div>
                        <p className="text-sm text-muted mb-2">{recommendation.description}</p>

                        {/* Value change */}
                        {recommendation.currentValue && recommendation.suggestedValue && (
                            <div className="flex items-center gap-2 text-sm mb-2">
                                <span className="text-muted line-through">{recommendation.currentValue}</span>
                                <ArrowRight className="h-4 w-4 text-muted" />
                                <span className="text-accent font-medium">{recommendation.suggestedValue}</span>
                            </div>
                        )}

                        {/* Expected impact */}
                        <div className="flex items-center gap-1 text-sm text-green-400">
                            <Zap className="h-4 w-4" />
                            <span>{recommendation.expectedImpact}</span>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => onDismiss(recommendation.id)}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                        <Button
                            size="sm"
                            onClick={handleApply}
                            disabled={applying}
                        >
                            {applying ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Check className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

export function OptimizationDashboard() {
    const [recommendations, setRecommendations] = useState<OptimizationRecommendation[]>(mockRecommendations);
    const [loading, setLoading] = useState(false);
    const [applied, setApplied] = useState<string[]>([]);
    const [dismissed, setDismissed] = useState<string[]>([]);

    const refresh = async () => {
        setLoading(true);
        await new Promise(r => setTimeout(r, 1500));
        setRecommendations(mockRecommendations);
        setLoading(false);
        toast.success("Рекомендации обновлены");
    };

    const handleApply = (id: string) => {
        setApplied(prev => [...prev, id]);
        toast.success("Рекомендация применена");
    };

    const handleDismiss = (id: string) => {
        setDismissed(prev => [...prev, id]);
    };

    const activeRecommendations = recommendations.filter(
        r => !applied.includes(r.id) && !dismissed.includes(r.id)
    );

    const highPriority = activeRecommendations.filter(r => r.priority === "high");
    const otherPriority = activeRecommendations.filter(r => r.priority !== "high");

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-text">Автооптимизация</h2>
                    <p className="text-muted">AI-рекомендации для повышения эффективности</p>
                </div>
                <Button variant="outline" onClick={refresh} disabled={loading}>
                    <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                    Обновить
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-3xl font-bold text-text">{activeRecommendations.length}</div>
                        <div className="text-sm text-muted">Рекомендаций</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-3xl font-bold text-red-400">{highPriority.length}</div>
                        <div className="text-sm text-muted">Срочных</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-3xl font-bold text-green-400">{applied.length}</div>
                        <div className="text-sm text-muted">Применено</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-lg font-bold text-text">+₽12,400</div>
                        <div className="text-sm text-muted">Потенциал/мес</div>
                    </CardContent>
                </Card>
            </div>

            {/* High Priority */}
            {highPriority.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-text mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        Требуют внимания
                    </h3>
                    <div className="space-y-3">
                        {highPriority.map(rec => (
                            <OptimizationCard
                                key={rec.id}
                                recommendation={rec}
                                onApply={handleApply}
                                onDismiss={handleDismiss}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Other */}
            {otherPriority.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-text mb-3">
                        Другие рекомендации
                    </h3>
                    <div className="space-y-3">
                        {otherPriority.map(rec => (
                            <OptimizationCard
                                key={rec.id}
                                recommendation={rec}
                                onApply={handleApply}
                                onDismiss={handleDismiss}
                            />
                        ))}
                    </div>
                </div>
            )}

            {activeRecommendations.length === 0 && (
                <Card>
                    <CardContent className="p-8 text-center">
                        <Check className="h-12 w-12 text-green-500 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-text mb-2">Всё оптимизировано!</h3>
                        <p className="text-muted">Нет активных рекомендаций. Проверьте позже.</p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
