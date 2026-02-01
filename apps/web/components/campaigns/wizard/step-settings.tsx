"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { listConnections, ConnectionResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Loader2, AlertCircle } from "lucide-react";

interface StepSettingsProps {
    data: any;
    onChange: (data: any) => void;
}

export function StepSettings({ data, onChange }: StepSettingsProps) {
    const [connections, setConnections] = useState<ConnectionResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadConnections();
    }, []);

    const loadConnections = async () => {
        try {
            const result = await listConnections();
            setConnections(result);
        } catch (err) {
            setError("Не удалось загрузить подключения");
        } finally {
            setLoading(false);
        }
    };

    const handleConnectionChange = (connectionId: number) => {
        const connection = connections.find(c => c.id === connectionId);
        if (connection) {
            onChange({
                connection_id: connectionId,
                platform: connection.platform
            });
        }
    };

    const activeConnections = connections.filter(c => c.status === "active");

    return (
        <div className="space-y-6">
            {/* Connection Selection - NEW */}
            <div className="space-y-2">
                <Label>Рекламный кабинет *</Label>
                {loading ? (
                    <div className="flex items-center gap-2 text-muted text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Загрузка подключений...
                    </div>
                ) : error ? (
                    <div className="flex items-center gap-2 text-danger text-sm">
                        <AlertCircle className="w-4 h-4" />
                        {error}
                    </div>
                ) : activeConnections.length === 0 ? (
                    <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-200 text-sm">
                        <p className="font-medium">Нет активных подключений</p>
                        <p className="mt-1 text-amber-300/80">
                            Перейдите на страницу <a href="/connections" className="underline hover:no-underline">Подключения</a> и добавьте рекламный кабинет.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {activeConnections.map((conn) => (
                            <div
                                key={conn.id}
                                onClick={() => handleConnectionChange(conn.id)}
                                className={cn(
                                    "cursor-pointer border rounded-lg p-4 transition-all hover:bg-white/5",
                                    data.connection_id === conn.id
                                        ? "border-violet-500 bg-violet-500/10"
                                        : "border-border bg-panel"
                                )}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className={cn(
                                            "font-medium text-sm",
                                            data.connection_id === conn.id ? "text-violet-200" : "text-text"
                                        )}>
                                            {conn.name || `Кабинет #${conn.id}`}
                                        </div>
                                        <div className="text-xs text-muted mt-1 uppercase">
                                            {conn.platform}
                                        </div>
                                    </div>
                                    <div className={cn(
                                        "w-4 h-4 rounded-full border-2 flex items-center justify-center",
                                        data.connection_id === conn.id
                                            ? "border-violet-500 bg-violet-500"
                                            : "border-muted"
                                    )}>
                                        {data.connection_id === conn.id && (
                                            <div className="w-2 h-2 rounded-full bg-white" />
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label>Название кампании *</Label>
                    <Input
                        value={data.name}
                        onChange={(e) => onChange({ name: e.target.value })}
                        placeholder="Например, Распродажа Лето 2024"
                    />
                </div>

                <div className="space-y-2">
                    <Label>Платформа</Label>
                    <div className="h-10 px-3 flex items-center rounded-md border border-border bg-panel-strong text-muted text-sm">
                        {data.platform ? data.platform.toUpperCase() : "Выберите кабинет"}
                    </div>
                    <p className="text-xs text-muted">Определяется автоматически из выбранного кабинета</p>
                </div>
            </div>

            <div className="space-y-2">
                <Label>Цель кампании</Label>
                <Input
                    value={data.objective}
                    onChange={(e) => onChange({ objective: e.target.value })}
                    placeholder="Максимум кликов / Рост продаж"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label>Бюджет на период (₽)</Label>
                    <Input
                        type="number"
                        value={data.budget_total}
                        onChange={(e) => onChange({ budget_total: e.target.value })}
                        placeholder="Необязательно"
                    />
                </div>
                <div className="space-y-2">
                    <Label>Дневной лимит (₽)</Label>
                    <Input
                        type="number"
                        value={data.budget_daily}
                        onChange={(e) => onChange({ budget_daily: e.target.value })}
                        placeholder="Необязательно"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label>Дата начала</Label>
                    <Input type="date" value={data.start_date} onChange={(e) => onChange({ start_date: e.target.value })} />
                </div>
                <div className="space-y-2">
                    <Label>Дата окончания</Label>
                    <Input type="date" value={data.end_date} onChange={(e) => onChange({ end_date: e.target.value })} />
                </div>
            </div>
        </div>
    );
}
