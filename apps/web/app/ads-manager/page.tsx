"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import {
    Play, Pause, Trash2, Plus, Search, Filter,
    CheckCircle2, XCircle, Clock, Loader2
} from "lucide-react";
import { toast } from "sonner";

// Types
interface Ad {
    id: number;
    title: string;
    text: string;
    platform: string;
    campaign: string;
    status: "active" | "paused" | "draft";
    impressions: number;
    clicks: number;
    spend: number;
}

// Mock data - будет заменено на API
const mockAds: Ad[] = [
    { id: 1, title: "Look At Show — Мероприятия", text: "Корпоративы, презентации...", platform: "yandex", campaign: "Бренд Look At Show", status: "active", impressions: 12500, clicks: 340, spend: 8500 },
    { id: 2, title: "Мероприятия под ключ", text: "От идеи до реализации...", platform: "yandex", campaign: "Бренд Look At Show", status: "active", impressions: 8200, clicks: 210, spend: 5200 },
    { id: 3, title: "Корпоратив мечты", text: "Организуем незабываемый...", platform: "vk", campaign: "Таргет на предпринимателей", status: "paused", impressions: 4500, clicks: 89, spend: 2100 },
    { id: 4, title: "Звуковое оборудование", text: "Профессиональный звук...", platform: "ozon", campaign: "Аренда оборудования", status: "draft", impressions: 0, clicks: 0, spend: 0 },
    { id: 5, title: "Свадьба вашей мечты", text: "Полная организация свадьбы...", platform: "yandex", campaign: "Свадьбы премиум", status: "active", impressions: 15800, clicks: 520, spend: 12000 },
    { id: 6, title: "VIP-свадьбы", text: "Эксклюзивные мероприятия...", platform: "yandex", campaign: "Свадьбы премиум", status: "active", impressions: 6200, clicks: 180, spend: 4500 },
];

const PLATFORM_NAMES: Record<string, string> = {
    yandex: "Яндекс",
    vk: "VK",
    ozon: "Ozon",
    google: "Google",
};

const STATUS_CONFIG = {
    active: { label: "Активно", variant: "success" as const, icon: CheckCircle2 },
    paused: { label: "Пауза", variant: "warning" as const, icon: Pause },
    draft: { label: "Черновик", variant: "muted" as const, icon: Clock },
};

export default function AdsManagerPage() {
    const [ads, setAds] = useState<Ad[]>(mockAds);
    const [selected, setSelected] = useState<Set<number>>(new Set());
    const [search, setSearch] = useState("");
    const [platformFilter, setPlatformFilter] = useState("all");
    const [statusFilter, setStatusFilter] = useState("all");
    const [loading, setLoading] = useState(false);

    // Фильтрация
    const filteredAds = ads.filter(ad => {
        const matchesSearch = ad.title.toLowerCase().includes(search.toLowerCase()) ||
            ad.text.toLowerCase().includes(search.toLowerCase()) ||
            ad.campaign.toLowerCase().includes(search.toLowerCase());
        const matchesPlatform = platformFilter === "all" || ad.platform === platformFilter;
        const matchesStatus = statusFilter === "all" || ad.status === statusFilter;
        return matchesSearch && matchesPlatform && matchesStatus;
    });

    // Выделение всех
    const allSelected = filteredAds.length > 0 && filteredAds.every(ad => selected.has(ad.id));
    const someSelected = selected.size > 0;

    const toggleSelectAll = () => {
        if (allSelected) {
            setSelected(new Set());
        } else {
            setSelected(new Set(filteredAds.map(ad => ad.id)));
        }
    };

    const toggleSelect = (id: number) => {
        const next = new Set(selected);
        if (next.has(id)) {
            next.delete(id);
        } else {
            next.add(id);
        }
        setSelected(next);
    };

    // Bulk actions
    const bulkAction = async (action: "enable" | "pause" | "delete") => {
        if (selected.size === 0) {
            toast.error("Выберите объявления");
            return;
        }

        setLoading(true);

        // Simulate API call
        await new Promise(r => setTimeout(r, 800));

        if (action === "delete") {
            setAds(prev => prev.filter(ad => !selected.has(ad.id)));
            toast.success(`Удалено ${selected.size} объявлений`);
        } else {
            const newStatus = action === "enable" ? "active" : "paused";
            setAds(prev => prev.map(ad =>
                selected.has(ad.id) ? { ...ad, status: newStatus } : ad
            ));
            toast.success(`${action === "enable" ? "Включено" : "Приостановлено"} ${selected.size} объявлений`);
        }

        setSelected(new Set());
        setLoading(false);
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="Управление объявлениями"
                subtitle="Массовое управление объявлениями на всех площадках"
            />

            {/* Filters */}
            <Card>
                <CardContent className="p-4">
                    <div className="flex flex-wrap gap-4 items-center">
                        <div className="flex-1 min-w-[200px]">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
                                <Input
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                    placeholder="Поиск объявлений..."
                                    className="pl-10"
                                />
                            </div>
                        </div>

                        <Select value={platformFilter} onValueChange={setPlatformFilter}>
                            <SelectTrigger className="w-[140px]">
                                <SelectValue placeholder="Платформа" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Все платформы</SelectItem>
                                <SelectItem value="yandex">Яндекс</SelectItem>
                                <SelectItem value="vk">VK</SelectItem>
                                <SelectItem value="ozon">Ozon</SelectItem>
                            </SelectContent>
                        </Select>

                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-[140px]">
                                <SelectValue placeholder="Статус" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Все статусы</SelectItem>
                                <SelectItem value="active">Активные</SelectItem>
                                <SelectItem value="paused">На паузе</SelectItem>
                                <SelectItem value="draft">Черновики</SelectItem>
                            </SelectContent>
                        </Select>

                        <Button variant="outline" size="sm">
                            <Plus className="h-4 w-4 mr-2" />
                            Новое объявление
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Bulk Actions */}
            {someSelected && (
                <Card className="border-accent/50 bg-accent/5">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-text">
                                Выбрано: <strong>{selected.size}</strong> объявлений
                            </span>
                            <div className="flex gap-2">
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => bulkAction("enable")}
                                    disabled={loading}
                                >
                                    <Play className="h-4 w-4 mr-1" />
                                    Включить
                                </Button>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => bulkAction("pause")}
                                    disabled={loading}
                                >
                                    <Pause className="h-4 w-4 mr-1" />
                                    Пауза
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => bulkAction("delete")}
                                    disabled={loading}
                                    className="text-danger hover:bg-danger/10"
                                >
                                    <Trash2 className="h-4 w-4 mr-1" />
                                    Удалить
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Ads Table */}
            <Card>
                <CardContent className="p-0">
                    {filteredAds.length === 0 ? (
                        <EmptyState
                            title="Объявлений не найдено"
                            description="Измените фильтры или создайте новое объявление"
                        />
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-12">
                                        <Checkbox
                                            checked={allSelected}
                                            onCheckedChange={toggleSelectAll}
                                        />
                                    </TableHead>
                                    <TableHead>Заголовок</TableHead>
                                    <TableHead>Кампания</TableHead>
                                    <TableHead>Платформа</TableHead>
                                    <TableHead>Статус</TableHead>
                                    <TableHead className="text-right">Показы</TableHead>
                                    <TableHead className="text-right">Клики</TableHead>
                                    <TableHead className="text-right">Расход</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredAds.map(ad => {
                                    const statusConf = STATUS_CONFIG[ad.status];
                                    const StatusIcon = statusConf.icon;

                                    return (
                                        <TableRow
                                            key={ad.id}
                                            className={selected.has(ad.id) ? "bg-accent/5" : ""}
                                        >
                                            <TableCell>
                                                <Checkbox
                                                    checked={selected.has(ad.id)}
                                                    onCheckedChange={() => toggleSelect(ad.id)}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <div>
                                                    <div className="font-medium">{ad.title}</div>
                                                    <div className="text-sm text-muted truncate max-w-[300px]">{ad.text}</div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-muted">{ad.campaign}</TableCell>
                                            <TableCell>
                                                <Badge variant="muted">{PLATFORM_NAMES[ad.platform]}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={statusConf.variant}>
                                                    <StatusIcon className="h-3 w-3 mr-1" />
                                                    {statusConf.label}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right tabular-nums">
                                                {ad.impressions.toLocaleString()}
                                            </TableCell>
                                            <TableCell className="text-right tabular-nums">
                                                {ad.clicks.toLocaleString()}
                                            </TableCell>
                                            <TableCell className="text-right tabular-nums">
                                                ₽{ad.spend.toLocaleString()}
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-text">{ads.length}</div>
                        <div className="text-sm text-muted">Всего объявлений</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-green-500">
                            {ads.filter(a => a.status === "active").length}
                        </div>
                        <div className="text-sm text-muted">Активных</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-text">
                            ₽{ads.reduce((s, a) => s + a.spend, 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-muted">Общий расход</div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
