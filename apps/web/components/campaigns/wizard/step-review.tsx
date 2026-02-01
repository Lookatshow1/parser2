"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StepReviewProps {
    data: any;
}

export function StepReview({ data }: StepReviewProps) {
    return (
        <div className="space-y-6">
            <div className="bg-panel-strong rounded-xl p-4 border border-border">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <span className="uppercase text-violet-400">{data.platform}</span>
                    <span className="text-muted">/</span>
                    {data.name}
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-muted mb-4">
                    <div>
                        <div className="mb-1">Бюджет всего</div>
                        <div className="text-text font-medium text-sm">{data.budget_total || "—"} ₽</div>
                    </div>
                    <div>
                        <div className="mb-1">Бюджет в день</div>
                        <div className="text-text font-medium text-sm">{data.budget_daily || "—"} ₽</div>
                    </div>
                    <div>
                        <div className="mb-1">Начало</div>
                        <div className="text-text font-medium text-sm">{data.start_date || "—"}</div>
                    </div>
                    <div>
                        <div className="mb-1">Окончание</div>
                        <div className="text-text font-medium text-sm">{data.end_date || "—"}</div>
                    </div>
                </div>
            </div>

            <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted uppercase">Группа объявлений</h4>
                <Card className="bg-panel rounded-xl border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex justify-between mb-4">
                            <span className="font-semibold">{data.group_name}</span>
                            <Badge variant="outline">{data.bid_strategy}</Badge>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div>
                                <div className="text-xs text-muted mb-2">Ключевые слова</div>
                                <div className="flex flex-wrap gap-1">
                                    {data.keywords?.split("\n").filter(Boolean).map((k: string, i: number) => (
                                        <Badge key={i} variant="secondary" className="text-[10px] bg-white/5">{k}</Badge>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-muted mb-2">Регионы</div>
                                <div className="text-sm">{data.regions}</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted uppercase">Объявления ({data.ads.length})</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {data.ads.map((ad: any) => (
                        <div key={ad.id} className="flex gap-4 p-3 rounded-lg border border-white/5 bg-panel-strong/50">
                            {ad.image_url && (
                                <div className="w-16 h-16 rounded-md bg-black/20 overflow-hidden flex-shrink-0">
                                    <img src={ad.image_url} alt="" className="w-full h-full object-cover" />
                                </div>
                            )}
                            <div className="min-w-0">
                                <div className="font-semibold text-violet-300 truncate">{ad.title || "Без заголовка"}</div>
                                <div className="text-xs text-muted line-clamp-2 mb-1">{ad.text || "Текст не указан"}</div>
                                <div className="text-[10px] text-muted truncate opacity-50">{ad.link}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
