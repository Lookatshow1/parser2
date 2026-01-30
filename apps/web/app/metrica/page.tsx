"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    BarChart3, Link2, CheckCircle2, ExternalLink,
    Loader2, RefreshCw, Target, TrendingUp, Globe
} from "lucide-react";
import { toast } from "sonner";
import { getOrgId, getToken } from "@/lib/session";

const API_BASE = ""; // Use relative path for proxying

interface Counter {
    id: number;
    name: string;
    site: string;
    status: string;
}

interface Goal {
    id: number;
    name: string;
    type: string;
}

export default function MetricaPage() {
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState(false);
    const [counters, setCounters] = useState<Counter[]>([]);
    const [goals, setGoals] = useState<Record<number, Goal[]>>({});
    const [selectedCounter, setSelectedCounter] = useState<number | null>(null);

    useEffect(() => {
        checkStatus();
    }, []);

    const buildHeaders = () => {
        const token = getToken();
        const orgId = getOrgId();
        return {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(orgId ? { "X-Org-Id": orgId } : {}),
        };
    };

    const checkStatus = async () => {
        try {
            const token = getToken();
            if (!token) {
                setConnected(false);
                return;
            }
            const res = await fetch(`${API_BASE}/api/metrica/status`, {
                headers: buildHeaders()
            });
            const data = await res.json();
            setConnected(data.connected);

            if (data.connected) {
                loadCounters();
            }
        } catch {
            setConnected(false);
        } finally {
            setLoading(false);
        }
    };

    const startOAuth = async () => {
        setConnecting(true);
        try {
            const token = getToken();
            if (!token) {
                toast.error("Нужно войти в систему");
                setConnecting(false);
                return;
            }
            const res = await fetch(`${API_BASE}/api/metrica/auth-url`, {
                headers: buildHeaders()
            });
            if (!res.ok) {
                const error = await res.json().catch(() => ({}));
                throw new Error(error?.detail || "Ошибка подключения");
            }
            const data = await res.json();

            // Open OAuth window
            const width = 500;
            const height = 600;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            const popup = window.open(
                data.auth_url,
                "metrica_oauth",
                `width=${width},height=${height},left=${left},top=${top}`
            );

            // Listen for OAuth completion
            const checkPopup = setInterval(() => {
                if (popup?.closed) {
                    clearInterval(checkPopup);
                    setConnecting(false);
                    checkStatus();
                }
            }, 1000);

        } catch (err) {
            toast.error((err as Error).message || "Ошибка подключения");
            setConnecting(false);
        }
    };

    const loadCounters = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/metrica/counters`, {
                headers: buildHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setCounters(data);
            }
        } catch {
            console.error("Failed to load counters");
        }
    };

    const loadGoals = async (counterId: number) => {
        try {
            const res = await fetch(`${API_BASE}/api/metrica/counters/${counterId}/goals`, {
                headers: buildHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setGoals(prev => ({ ...prev, [counterId]: data }));
            }
        } catch {
            console.error("Failed to load goals");
        }
    };

    const selectCounter = (counterId: number) => {
        setSelectedCounter(counterId);
        if (!goals[counterId]) {
            loadGoals(counterId);
        }
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
                title="Яндекс Метрика"
                subtitle="Сквозная аналитика и отслеживание конверсий"
            />

            {/* Connection Status */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 text-accent" />
                        Подключение
                    </CardTitle>
                    <CardDescription>
                        Подключите Яндекс Метрику для отслеживания конверсий и сквозной аналитики
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {connected ? (
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 text-green-500">
                                <CheckCircle2 className="h-5 w-5" />
                                <span className="font-medium">Подключено</span>
                            </div>
                            <Button variant="outline" size="sm" onClick={checkStatus}>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Обновить
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <p className="text-muted text-sm">
                                Для работы необходимо авторизоваться через Яндекс OAuth.
                                Мы получим доступ только к чтению статистики.
                            </p>
                            <Button onClick={startOAuth} disabled={connecting}>
                                {connecting ? (
                                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Подключение...</>
                                ) : (
                                    <><Link2 className="h-4 w-4 mr-2" /> Подключить Метрику</>
                                )}
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Counters List */}
            {connected && counters.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Globe className="h-5 w-5 text-accent" />
                            Счётчики (сайты)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-3">
                            {counters.map(counter => (
                                <div
                                    key={counter.id}
                                    className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedCounter === counter.id
                                        ? "border-accent bg-accent/10"
                                        : "border-border hover:border-accent/50"
                                        }`}
                                    onClick={() => selectCounter(counter.id)}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h4 className="font-medium text-text">{counter.name}</h4>
                                            <p className="text-sm text-muted">{counter.site}</p>
                                        </div>
                                        <Badge variant={counter.status === "Active" ? "default" : "muted"}>
                                            #{counter.id}
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Goals for Selected Counter */}
            {selectedCounter && goals[selectedCounter] && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Target className="h-5 w-5 text-accent" />
                            Цели (конверсии)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {goals[selectedCounter].length === 0 ? (
                            <p className="text-muted text-sm">Нет целей для этого счётчика</p>
                        ) : (
                            <div className="grid gap-2">
                                {goals[selectedCounter].map(goal => (
                                    <div
                                        key={goal.id}
                                        className="flex items-center justify-between p-3 bg-panel-strong rounded-lg"
                                    >
                                        <div className="flex items-center gap-3">
                                            <TrendingUp className="h-4 w-4 text-green-500" />
                                            <span className="text-text">{goal.name}</span>
                                        </div>
                                        <Badge variant="muted">{goal.type}</Badge>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Features Coming Soon */}
            {connected && (
                <Card>
                    <CardHeader>
                        <CardTitle>Возможности</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-3 gap-4">
                            <div className="p-4 bg-panel-strong rounded-lg">
                                <h4 className="font-medium text-text mb-1">ROI кампаний</h4>
                                <p className="text-sm text-muted">Автоматический расчёт ROI на основе данных Метрики</p>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg">
                                <h4 className="font-medium text-text mb-1">Атрибуция</h4>
                                <p className="text-sm text-muted">Какие объявления приносят конверсии</p>
                            </div>
                            <div className="p-4 bg-panel-strong rounded-lg">
                                <h4 className="font-medium text-text mb-1">Автоставки</h4>
                                <p className="text-sm text-muted">Автоматическая оптимизация ставок по CPA</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
