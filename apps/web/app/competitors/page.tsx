"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    Search, TrendingUp, Target, Eye,
    Loader2, Globe, Zap, AlertTriangle
} from "lucide-react";
import { toast } from "sonner";
import { CompetitorsApi, CompetitorAnalysis } from "@/lib/api";

export default function CompetitorsPage() {
    const [domain, setDomain] = useState("");
    const [loading, setLoading] = useState(false);
    const [analysis, setAnalysis] = useState<CompetitorAnalysis | null>(null);
    const [error, setError] = useState<string | null>(null);

    const analyzeCompetitor = async () => {
        if (!domain) {
            toast.error("Введите домен конкурента");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await CompetitorsApi.analyze(domain);
            setAnalysis(result);
            toast.success("Анализ завершён");
        } catch (err) {
            const message = (err as Error).message || "Ошибка анализа";
            setError(message);
            setAnalysis(null);
            toast.error(message);
        } finally {
            setLoading(false);
        }
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

            {error && (
                <Card>
                    <CardContent className="p-6 text-sm text-red-400">
                        {error}
                    </CardContent>
                </Card>
            )}

            {analysis && (
                <>
                    {/* Overview */}
                    <div className="grid md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{analysis.keywords?.length || 0}</div>
                                <div className="text-sm text-muted">Ключевых слов</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{analysis.profile.products?.length || 0}</div>
                                <div className="text-sm text-muted">Услуг/товаров</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{analysis.profile.trust_signals?.length || 0}</div>
                                <div className="text-sm text-muted">Сигналов доверия</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className="text-3xl font-bold text-text">{analysis.recommendations?.length || 0}</div>
                                <div className="text-sm text-muted">Рекомендаций</div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Profile */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Globe className="h-5 w-5 text-accent" />
                                Профиль сайта
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm text-muted">
                            <div>
                                <span className="text-text font-medium">Название: </span>
                                {analysis.profile.name || analysis.domain}
                            </div>
                            {analysis.profile.description && (
                                <div>
                                    <span className="text-text font-medium">Описание: </span>
                                    {analysis.profile.description}
                                </div>
                            )}
                            {(analysis.profile.social_links || []).length > 0 && (
                                <div>
                                    <span className="text-text font-medium">Соцсети: </span>
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {analysis.profile.social_links?.map((link) => (
                                            <Badge key={link} variant="muted">
                                                {link}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Keywords */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-accent" />
                                Ключевые слова конкурента
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {analysis.keywords?.length ? (
                                <div className="flex flex-wrap gap-2">
                                    {analysis.keywords.map((kw, idx) => (
                                        <Badge key={idx} variant="muted" className="text-sm py-1 px-3">
                                            {kw}
                                        </Badge>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-muted text-sm">Ключевые слова не найдены.</div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Products / Messages */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Eye className="h-5 w-5 text-accent" />
                                Основные услуги и сообщения
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {analysis.profile.products?.length ? (
                                <div className="flex flex-wrap gap-2">
                                    {analysis.profile.products.map((item, idx) => (
                                        <Badge key={idx} variant="muted" className="text-sm py-1 px-3">
                                            {item}
                                        </Badge>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-muted text-sm">Не удалось выделить услуги/сообщения.</div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Strengths / Weaknesses / Opportunities */}
                    <div className="grid md:grid-cols-3 gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm">Сильные стороны</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm text-muted">
                                {analysis.strengths?.length ? analysis.strengths.map((item, idx) => (
                                    <div key={idx} className="flex items-start gap-2">
                                        <TrendingUp className="h-4 w-4 text-green-500 mt-0.5" />
                                        <span>{item}</span>
                                    </div>
                                )) : (
                                    <span>Нет данных</span>
                                )}
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm">Слабые стороны</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm text-muted">
                                {analysis.weaknesses?.length ? analysis.weaknesses.map((item, idx) => (
                                    <div key={idx} className="flex items-start gap-2">
                                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                                        <span>{item}</span>
                                    </div>
                                )) : (
                                    <span>Нет данных</span>
                                )}
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm">Возможности</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm text-muted">
                                {analysis.opportunities?.length ? analysis.opportunities.map((item, idx) => (
                                    <div key={idx} className="flex items-start gap-2">
                                        <TrendingUp className="h-4 w-4 text-blue-500 mt-0.5" />
                                        <span>{item}</span>
                                    </div>
                                )) : (
                                    <span>Нет данных</span>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Recommendations */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-accent" />
                                Рекомендации
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {analysis.recommendations?.length ? (
                                <div className="space-y-3">
                                    {analysis.recommendations.map((rec, idx) => (
                                        <div key={idx} className="p-4 rounded-lg border bg-green-500/10 border-green-500/30">
                                            <div className="flex items-start gap-3">
                                                <TrendingUp className="h-5 w-5 text-green-500 mt-0.5" />
                                                <div>
                                                    <h4 className="font-semibold text-text">Идея</h4>
                                                    <p className="text-sm text-muted mt-0.5">{rec}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-muted text-sm">Рекомендации не сформированы.</div>
                            )}
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
