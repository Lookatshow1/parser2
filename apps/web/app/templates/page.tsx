"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    LayoutTemplate, TrendingUp, Target, DollarSign,
    Loader2, ChevronRight, Sparkles, Copy
} from "lucide-react";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Industry {
    id: string;
    name: string;
}

interface Benchmark {
    industry: string;
    avg_ctr: number;
    avg_cpc: number;
    avg_cpa: number;
    avg_roas: number;
    conversion_rate: number;
}

interface AdTemplate {
    title: string;
    text: string;
    approach: string;
}

interface CampaignTemplate {
    name: string;
    description: string;
    recommended_budget: number;
    recommended_bid: number;
    keywords: string[];
    negative_keywords: string[];
    ads: AdTemplate[];
    tips: string[];
}

export default function TemplatesPage() {
    const [industries, setIndustries] = useState<Industry[]>([]);
    const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
    const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
    const [templates, setTemplates] = useState<CampaignTemplate[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadIndustries();
    }, []);

    useEffect(() => {
        if (selectedIndustry) {
            loadBenchmarkAndTemplates(selectedIndustry);
        }
    }, [selectedIndustry]);

    const loadIndustries = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/templates/industries`);
            if (res.ok) {
                setIndustries(await res.json());
            }
        } catch {
            console.error("Failed to load industries");
        } finally {
            setLoading(false);
        }
    };

    const loadBenchmarkAndTemplates = async (industry: string) => {
        try {
            const [benchRes, templRes] = await Promise.all([
                fetch(`${API_BASE}/api/templates/benchmarks/${industry}`),
                fetch(`${API_BASE}/api/templates/campaigns/${industry}`),
            ]);

            if (benchRes.ok) setBenchmark(await benchRes.json());
            if (templRes.ok) setTemplates(await templRes.json());
        } catch {
            console.error("Failed to load data");
        }
    };

    const copyAd = (ad: AdTemplate) => {
        navigator.clipboard.writeText(`${ad.title}\n${ad.text}`);
        toast.success("Объявление скопировано");
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-accent" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <PageHeader
                title="Шаблоны кампаний"
                subtitle="Готовые кампании и бенчмарки по отраслям"
            />

            {/* Industry Selector */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <LayoutTemplate className="h-5 w-5 text-accent" />
                        Выберите отрасль
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {industries.map(ind => (
                            <button
                                key={ind.id}
                                onClick={() => setSelectedIndustry(ind.id)}
                                className={`p-4 rounded-lg border text-left transition-all ${selectedIndustry === ind.id
                                        ? "border-accent bg-accent/10"
                                        : "border-border hover:border-accent/50"
                                    }`}
                            >
                                <span className="text-text font-medium">{ind.name}</span>
                            </button>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Benchmarks */}
            {benchmark && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-accent" />
                            Бенчмарки отрасли
                        </CardTitle>
                        <CardDescription>
                            Средние показатели для сравнения ваших кампаний
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div className="p-4 bg-panel-strong rounded-lg text-center">
                                <div className="text-2xl font-bold text-text">{benchmark.avg_ctr}%</div>
                                <div className="text-sm text-muted">CTR</div>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg text-center">
                                <div className="text-2xl font-bold text-text">₽{benchmark.avg_cpc}</div>
                                <div className="text-sm text-muted">CPC</div>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg text-center">
                                <div className="text-2xl font-bold text-text">₽{benchmark.avg_cpa}</div>
                                <div className="text-sm text-muted">CPA</div>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg text-center">
                                <div className="text-2xl font-bold text-text">{benchmark.avg_roas}x</div>
                                <div className="text-sm text-muted">ROAS</div>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg text-center">
                                <div className="text-2xl font-bold text-text">{benchmark.conversion_rate}%</div>
                                <div className="text-sm text-muted">CR</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Templates */}
            {templates.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-text">Шаблоны кампаний</h2>

                    {templates.map((template, idx) => (
                        <Card key={idx}>
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div>
                                        <CardTitle className="flex items-center gap-2">
                                            <Sparkles className="h-5 w-5 text-accent" />
                                            {template.name}
                                        </CardTitle>
                                        <CardDescription>{template.description}</CardDescription>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-muted">Бюджет/день</div>
                                        <div className="text-lg font-bold text-text">₽{template.recommended_budget}</div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Keywords */}
                                <div>
                                    <h4 className="text-sm font-medium text-text mb-2">Ключевые фразы</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {template.keywords.map((kw, i) => (
                                            <Badge key={i} variant="muted">{kw}</Badge>
                                        ))}
                                    </div>
                                </div>

                                {/* Ads */}
                                <div>
                                    <h4 className="text-sm font-medium text-text mb-2">Объявления</h4>
                                    <div className="grid md:grid-cols-3 gap-3">
                                        {template.ads.map((ad, i) => (
                                            <div
                                                key={i}
                                                className="p-3 bg-panel-strong rounded-lg relative group"
                                            >
                                                <div className="font-medium text-text text-sm">{ad.title}</div>
                                                <div className="text-xs text-muted mt-1">{ad.text}</div>
                                                <Badge variant="info" className="mt-2">{ad.approach}</Badge>
                                                <button
                                                    onClick={() => copyAd(ad)}
                                                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                                >
                                                    <Copy className="h-4 w-4 text-muted hover:text-text" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Tips */}
                                {template.tips.length > 0 && (
                                    <div className="p-3 bg-accent/10 rounded-lg">
                                        <h4 className="text-sm font-medium text-accent mb-1">💡 Советы</h4>
                                        <ul className="text-sm text-muted list-disc list-inside">
                                            {template.tips.map((tip, i) => (
                                                <li key={i}>{tip}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                <Button className="w-full">
                                    <ChevronRight className="h-4 w-4 mr-2" />
                                    Использовать шаблон
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Empty state */}
            {selectedIndustry && templates.length === 0 && (
                <Card>
                    <CardContent className="py-12 text-center">
                        <LayoutTemplate className="h-12 w-12 text-muted mx-auto mb-4" />
                        <p className="text-muted">Шаблоны для этой отрасли скоро появятся</p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
