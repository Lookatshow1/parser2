"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface StepAdGroupProps {
    data: any;
    onChange: (data: any) => void;
}

export function StepAdGroup({ data, onChange }: StepAdGroupProps) {
    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <Label>Название группы объявлений</Label>
                <Input
                    value={data.group_name}
                    onChange={(e) => onChange({ group_name: e.target.value })}
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label>Стратегия ставок</Label>
                    <select
                        className="w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text"
                        value={data.bid_strategy}
                        onChange={(e) => onChange({ bid_strategy: e.target.value })}
                    >
                        <option value="manual">Ручное управление</option>
                        <option value="optimize_clicks">Оптимизация кликов</option>
                        <option value="optimize_conversions">Оптимизация конверсий</option>
                    </select>
                </div>
                <div className="space-y-2">
                    <Label>Бюджет группы (дневной)</Label>
                    <Input
                        type="number"
                        value={data.group_budget_daily}
                        onChange={(e) => onChange({ group_budget_daily: e.target.value })}
                    />
                </div>
            </div>

            <div className="space-y-2">
                <Label>Ключевые слова (через Enter)</Label>
                <Textarea
                    className="min-h-[100px] font-mono text-xs"
                    placeholder="купить слона&#10;слон цена&#10;розовый слон"
                    value={data.keywords}
                    onChange={(e) => onChange({ keywords: e.target.value })}
                />
                <p className="text-xs text-muted">Каждое слово с новой строки</p>
            </div>

            <div className="space-y-2">
                <Label>Регионы (через запятую)</Label>
                <Input
                    placeholder="Москва, Санкт-Петербург, Россия"
                    value={data.regions}
                    onChange={(e) => onChange({ regions: e.target.value })}
                />
            </div>
        </div>
    );
}
