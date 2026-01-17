"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Plus, Play, Pause, Trophy, BarChart3, TrendingUp, Percent } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

// Mock API - will be replaced with real API
const mockTests = [
    {
        id: 1,
        name: "Тест заголовков - зимняя акция",
        status: "running",
        primary_metric: "ctr",
        confidence_level: 0.95,
        started_at: "2026-01-15T10:00:00Z",
        variants: [
            { id: 1, name: "Вариант A", title: "Зимняя распродажа -50%!", impressions: 5420, clicks: 312, ctr: 5.76 },
            { id: 2, name: "Вариант B", title: "Скидки до 50% на зимнюю коллекцию", impressions: 5380, clicks: 298, ctr: 5.54 }
        ],
        significance: { significant: true, p_value: 0.04, winner_name: "Вариант A", confidence: 96 }
    },
    {
        id: 2,
        name: "Тест CTA кнопок",
        status: "draft",
        primary_metric: "conversions",
        confidence_level: 0.95,
        variants: [
            { id: 3, name: "Вариант A", title: "Купить сейчас", impressions: 0, clicks: 0, ctr: 0 },
            { id: 4, name: "Вариант B", title: "Заказать со скидкой", impressions: 0, clicks: 0, ctr: 0 }
        ]
    }
];

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
    draft: { label: "Черновик", color: "bg-gray-500/20 text-gray-400" },
    running: { label: "Активен", color: "bg-green-500/20 text-green-400" },
    paused: { label: "Пауза", color: "bg-yellow-500/20 text-yellow-400" },
    completed: { label: "Завершён", color: "bg-blue-500/20 text-blue-400" },
    winner_selected: { label: "Победитель выбран", color: "bg-purple-500/20 text-purple-400" }
};

const METRIC_LABELS: Record<string, string> = {
    ctr: "CTR",
    conversions: "Конверсии",
    roas: "ROAS"
};

export default function ABTestsPage() {
    const [tests, setTests] = useState(mockTests);
    const [loading, setLoading] = useState(false);
    const [showCreate, setShowCreate] = useState(false);
    const [newTestName, setNewTestName] = useState("");
    const [variantA, setVariantA] = useState("");
    const [variantB, setVariantB] = useState("");

    const handleCreate = () => {
        if (!newTestName || !variantA || !variantB) {
            toast.error("Заполните все поля");
            return;
        }

        const newTest = {
            id: tests.length + 1,
            name: newTestName,
            status: "draft",
            primary_metric: "ctr",
            confidence_level: 0.95,
            variants: [
                { id: 100, name: "Вариант A", title: variantA, impressions: 0, clicks: 0, ctr: 0 },
                { id: 101, name: "Вариант B", title: variantB, impressions: 0, clicks: 0, ctr: 0 }
            ]
        };

        setTests([newTest, ...tests]);
        setShowCreate(false);
        setNewTestName("");
        setVariantA("");
        setVariantB("");
        toast.success("A/B тест создан!");
    };

    const startTest = (id: number) => {
        setTests(tests.map(t => t.id === id ? { ...t, status: "running", started_at: new Date().toISOString() } : t));
        toast.success("Тест запущен!");
    };

    const pauseTest = (id: number) => {
        setTests(tests.map(t => t.id === id ? { ...t, status: "paused" } : t));
        toast.success("Тест приостановлен");
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">A/B Тестирование</h1>
                    <p className="text-gray-400 mt-1">Тестируйте варианты объявлений и находите лучшие</p>
                </div>
                <Button onClick={() => setShowCreate(true)} className="bg-accent hover:bg-accent/80">
                    <Plus className="mr-2 h-4 w-4" /> Новый тест
                </Button>
            </div>

            {/* Create Test Form */}
            {showCreate && (
                <Card className="glass-card border-white/10 mb-8">
                    <CardHeader>
                        <CardTitle>Создать A/B тест</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label>Название теста</Label>
                            <Input
                                value={newTestName}
                                onChange={(e) => setNewTestName(e.target.value)}
                                placeholder="Тест заголовков - январь 2026"
                                className="bg-black/20 border-white/10 text-white"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label>Вариант A (контроль)</Label>
                                <Input
                                    value={variantA}
                                    onChange={(e) => setVariantA(e.target.value)}
                                    placeholder="Текущий заголовок"
                                    className="bg-black/20 border-white/10 text-white"
                                />
                            </div>
                            <div>
                                <Label>Вариант B (тест)</Label>
                                <Input
                                    value={variantB}
                                    onChange={(e) => setVariantB(e.target.value)}
                                    placeholder="Новый заголовок"
                                    className="bg-black/20 border-white/10 text-white"
                                />
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="gap-2">
                        <Button variant="outline" onClick={() => setShowCreate(false)}>Отмена</Button>
                        <Button onClick={handleCreate} className="bg-accent hover:bg-accent/80">Создать тест</Button>
                    </CardFooter>
                </Card>
            )}

            {/* Tests Grid */}
            <div className="grid gap-6">
                {tests.map((test) => {
                    const status = STATUS_LABELS[test.status] || STATUS_LABELS.draft;
                    const metricLabel = METRIC_LABELS[test.primary_metric] || test.primary_metric;

                    return (
                        <Card key={test.id} className="glass-card border-white/5">
                            <CardHeader>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <CardTitle className="text-xl text-white">{test.name}</CardTitle>
                                        <div className="flex items-center gap-3 mt-2">
                                            <Badge className={status.color}>{status.label}</Badge>
                                            <span className="text-xs text-gray-500">
                                                Метрика: <span className="text-white">{metricLabel}</span>
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                Доверие: <span className="text-white">{test.confidence_level * 100}%</span>
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {test.status === "draft" && (
                                            <Button size="sm" onClick={() => startTest(test.id)} className="bg-green-600 hover:bg-green-500">
                                                <Play className="h-4 w-4 mr-1" /> Запустить
                                            </Button>
                                        )}
                                        {test.status === "running" && (
                                            <Button size="sm" variant="outline" onClick={() => pauseTest(test.id)}>
                                                <Pause className="h-4 w-4 mr-1" /> Пауза
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {/* Variants Comparison */}
                                <div className="grid grid-cols-2 gap-4">
                                    {test.variants.map((variant, idx) => {
                                        const isWinner = test.significance?.winner_name === variant.name;
                                        return (
                                            <div
                                                key={variant.id}
                                                className={`p-4 rounded-lg border ${isWinner ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 bg-black/20'}`}
                                            >
                                                <div className="flex justify-between items-center mb-3">
                                                    <span className="font-medium text-white">{variant.name}</span>
                                                    {isWinner && (
                                                        <Badge className="bg-green-500/20 text-green-400">
                                                            <Trophy className="h-3 w-3 mr-1" /> Лидер
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-300 mb-4">{variant.title}</p>

                                                <div className="grid grid-cols-3 gap-2 text-center">
                                                    <div>
                                                        <div className="text-lg font-bold text-white">{variant.impressions.toLocaleString()}</div>
                                                        <div className="text-xs text-gray-500">Показы</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-lg font-bold text-white">{variant.clicks.toLocaleString()}</div>
                                                        <div className="text-xs text-gray-500">Клики</div>
                                                    </div>
                                                    <div>
                                                        <div className={`text-lg font-bold ${isWinner ? 'text-green-400' : 'text-white'}`}>
                                                            {variant.ctr.toFixed(2)}%
                                                        </div>
                                                        <div className="text-xs text-gray-500">CTR</div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Statistical Significance */}
                                {test.significance && (
                                    <div className={`mt-4 p-4 rounded-lg border ${test.significance.significant ? 'border-green-500/30 bg-green-500/10' : 'border-yellow-500/30 bg-yellow-500/10'}`}>
                                        <div className="flex items-center gap-2 mb-2">
                                            {test.significance.significant ? (
                                                <>
                                                    <TrendingUp className="h-5 w-5 text-green-400" />
                                                    <span className="font-medium text-green-400">Статистически значимый результат!</span>
                                                </>
                                            ) : (
                                                <>
                                                    <BarChart3 className="h-5 w-5 text-yellow-400" />
                                                    <span className="font-medium text-yellow-400">Недостаточно данных</span>
                                                </>
                                            )}
                                        </div>
                                        <div className="flex gap-6 text-sm">
                                            <div>
                                                <span className="text-gray-500">Уверенность: </span>
                                                <span className="text-white">{test.significance.confidence}%</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">p-value: </span>
                                                <span className="text-white">{test.significance.p_value}</span>
                                            </div>
                                            {test.significance.winner_name && (
                                                <div>
                                                    <span className="text-gray-500">Победитель: </span>
                                                    <span className="text-green-400">{test.significance.winner_name}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {tests.length === 0 && (
                <div className="text-center py-20 border border-dashed border-white/10 rounded-xl">
                    <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-400">Нет A/B тестов</h3>
                    <p className="text-gray-500 mt-2">Создайте первый тест, чтобы найти лучшие объявления</p>
                </div>
            )}
        </div>
    );
}
