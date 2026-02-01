"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface StepSettingsProps {
    data: any;
    onChange: (data: any) => void;
}

export function StepSettings({ data, onChange }: StepSettingsProps) {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label>Название кампании</Label>
                    <Input
                        value={data.name}
                        onChange={(e) => onChange({ name: e.target.value })}
                        placeholder="Например, Распродажа Лето 2024"
                    />
                </div>

                <div className="space-y-2">
                    <Label>Рекламная платформа</Label>
                    <div className="grid grid-cols-3 gap-2">
                        {['yandex', 'vk', 'ozon'].map((p) => (
                            <div
                                key={p}
                                onClick={() => onChange({ platform: p })}
                                className={cn(
                                    "cursor-pointer border rounded-lg p-3 flex flex-col items-center justify-center gap-2 transition-all hover:bg-white/5",
                                    data.platform === p
                                        ? "border-violet-500 bg-violet-500/10 text-violet-200"
                                        : "border-border bg-panel text-muted"
                                )}
                            >
                                <div className="font-bold uppercase text-xs">{p}</div>
                            </div>
                        ))}
                    </div>
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
