"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    Search, TrendingUp, TrendingDown, Target, Eye,
    Loader2, BarChart3, Globe, Zap, AlertTriangle
} from "lucide-react";
import { toast } from "sonner";

interface CompetitorData {
    domain: string;
    title: string;
    description: string;
    keywords: string[];
    adCount: number;
    estimatedBudget: string;
    topAds: Array<{
        title: string;
        text: string;
        keywords: string[];
    }>;
}

interface Recommendation {
    type: "opportunity" | "warning" | "insight";
    title: string;
    description: string;
}

// Mock data for demo
const mockCompetitorData: CompetitorData = {
    domain: "competitor.ru",
    title: "Конкурент — Услуги и товары",
    description: "Качественные услуги по доступным ценам",
    keywords: ["услуги", "доставка", "скидки", "акции", "премиум"],
    adCount: 24,
    estimatedBudget: "₽150,000 — ₽300,000/мес",
    topAds: [
        { title: "Скидки до 50%!", text: "Только сегодня специальные цены на все услуги.", keywords: ["скидки", "акции"] },
        { title: "Бесплатная доставка", text: "Закажите сейчас и получите доставку бесплатно.", keywords: ["доставка", "бесплатно"] },
        { title: "Премиум качество", text: "Лучшие материалы от проверенных поставщиков.", keywords: ["качество", "премиум"] },
    ]
};

const mockRecommendations: Recommendation[] = [
    {
        type: "opportunity",
        title: "Используйте ключ «бесплатная консультация»",
        description: "Конкуренты не используют этот запрос, но он имеет высокий объём поиска."
    },
    {
        type: "warning",
        title: "Высокая конкуренция по «скидки»",
        description: "3 из 5 конкурентов активно используют этот ключ. Рассмотрите альтернативы."
    },
    {
        type: "insight",
        title: "Конкуренты делают ставку на эмоции",
        description: "80% объявлений используют эмоциональные триггеры. Попробуйте рациональный подход."
    }
];

export default function CompetitorsPage() {
    const [domain, setDomain] = useState("");
    const [loading, setLoading] = useState(false);
    const [competitor, setCompetitor] = useState<CompetitorData | null>(null);
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

    const analyzeCompetitor = async () => {
        if (!domain) {
            toast.error("Введите домен конкурента");
            return;
        }

        setLoading(true);

        // Simulate API call
        await new Promise(r => setTimeout(r, 2000));

        setCompetitor(mockCompetitorData);
        setRecommendations(mockRecommendations);
        setLoading(false);
        toast.success("Анализ завершён");
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="Анализ конкурентов"
                subtitle="Изучите рекламные стратегии ваших конкурентов"
            />

            {/* Search */}
            <Card>
                <CardContent className="p-6">
                    <div className="flex gap-4">
                        <div className="flex-1 relative">
                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted" />
                            <Input
                                value={domain}
                                onChange={e => setDomain(e.target.value)}
                                placeholder="Введите домен конкурента (например: competitor.ru)"
                                className="pl-10 h-12"
                            />
                        </div>
                        <Button
                            onClick={analyzeCompetitor}
                            disabled={loading}
                            className="h-12 px-8"
                        >
                            {loading ? (
                                <><Loader2 className="h-5 w-5 mr-2 animate-spin" /> Анализируем...</>
                            ) : (
                                <><Search className="h-5 w-5 mr-2" /> Анализировать</>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {competitor && (
                <>
                    {/* Overview */}
                    <div className="grid md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{competitor.adCount}</div>
                                <div className="text-sm text-muted">Активных объявлений</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{competitor.keywords.length}</div>
                                <div className="text-sm text-muted">Ключевых слов</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-lg font-bold text-text">{competitor.estimatedBudget}</div>
                                <div className="text-sm text-muted">Оценка бюджета</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-green-500">A</div>
                                <div className="text-sm text-muted">Оценка качества</div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Keywords */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-accent" />
                                Ключевые слова конкурента
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-wrap gap-2">
                                {competitor.keywords.map((kw, idx) => (
                                    <Badge key={idx} variant="muted" className="text-sm py-1 px-3">
                                        {kw}
                                    </Badge>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Top Ads */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Eye className="h-5 w-5 text-accent" />
                                Топ объявлений конкурента
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {competitor.topAds.map((ad, idx) => (
                                    <div key={idx} className="p-4 bg-panel-strong rounded-lg border border-border">
                                        <h4 className="font-semibold text-text mb-1">{ad.title}</h4>
                                        <p className="text-sm text-muted mb-2">{ad.text}</p>
                                        <div className="flex gap-1">
                                            {ad.keywords.map((kw, i) => (
                                                <Badge key={i} variant="muted" className="text-xs">
                                                    {kw}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Recommendations */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-accent" />
                                Рекомендации
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {recommendations.map((rec, idx) => (
                                    <div
                                        key={idx}
                                        className={`p-4 rounded-lg border ${rec.type === "opportunity" ? "bg-green-500/10 border-green-500/30" :
                                                rec.type === "warning" ? "bg-yellow-500/10 border-yellow-500/30" :
                                                    "bg-blue-500/10 border-blue-500/30"
                                            }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            {rec.type === "opportunity" ? (
                                                <TrendingUp className="h-5 w-5 text-green-500 mt-0.5" />
                                            ) : rec.type === "warning" ? (
                                                <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                                            ) : (
                                                <BarChart3 className="h-5 w-5 text-blue-500 mt-0.5" />
                                            )}
                                            <div>
                                                <h4 className="font-semibold text-text">{rec.title}</h4>
                                                <p className="text-sm text-muted mt-0.5">{rec.description}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Actions */}
                    <div className="flex gap-4">
                        <Button variant="secondary">
                            Экспортировать отчёт
                        </Button>
                        <Button variant="secondary">
                            Создать объявления на основе анализа
                        </Button>
                    </div>
                </>
            )}
        </div>
    );
}
