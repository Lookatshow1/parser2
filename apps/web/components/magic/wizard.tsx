"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MagicApi, MagicRun, ConnectionResponse, listConnections, DraftsApi } from "@/lib/api";
import { Loader2, Sparkles, ArrowRight, CheckCircle2, AlertCircle, Play } from "lucide-react";
import { STR } from "@/lib/strings";
import Link from "next/link";
import { toast } from "sonner";

// --- Sub-components ---

type MagicRunPayload = {
    landing_url?: string | null;
    description?: string;
    ad_count: number;
    budget_daily?: number;
    connection_ids: number[];
    connection_id?: number | null;
    platform?: string;
    product_ids?: number[];
};

const platformLabels: Record<string, string> = {
    yandex: "Яндекс Директ",
    vk: "VK Реклама",
    ozon: "Ozon Performance",
};

function StepInput({ onStart, isLoading }: { onStart: (payload: MagicRunPayload) => void; isLoading: boolean }) {
    const [url, setUrl] = useState("https://");
    const [description, setDescription] = useState("");
    const [adCount, setAdCount] = useState("6");
    const [budgetDaily, setBudgetDaily] = useState("1000");
    const [productIdsRaw, setProductIdsRaw] = useState("");
    const [connections, setConnections] = useState<ConnectionResponse[]>([]);
    const [selectedConnectionIds, setSelectedConnectionIds] = useState<number[]>([]);
    const [loadingConnections, setLoadingConnections] = useState(true);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim() && !description.trim()) {
            toast.error("Введите URL сайта или описание бизнеса");
            return;
        }
        if (selectedConnectionIds.length === 0) {
            toast.error("Выберите подключение для запуска рекламы");
            return;
        }

        const hasOzon = selectedConnectionIds.some((id) => connections.find((conn) => conn.id === id)?.platform === "ozon");
        const productIds = productIdsRaw
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean)
            .map((item) => Number(item))
            .filter((item) => !Number.isNaN(item));

        if (hasOzon && productIds.length === 0) {
            toast.error("Для Ozon укажите ID товаров");
            return;
        }

        const cleanedUrl = url.trim();
        const landingUrl = cleanedUrl === "https://" || cleanedUrl === "http://" ? "" : cleanedUrl;
        const primaryConnection = connections.find((conn) => selectedConnectionIds.includes(conn.id));

        const payload: MagicRunPayload = {
            landing_url: landingUrl || null,
            description: description.trim() || undefined,
            ad_count: Number(adCount),
            budget_daily: Number(budgetDaily) || 1000,
            connection_ids: selectedConnectionIds,
            connection_id: primaryConnection?.id || null,
            platform: primaryConnection?.platform,
            product_ids: productIds.length > 0 ? productIds : undefined,
        };

        onStart(payload);
    };

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            setLoadingConnections(true);
            try {
                const data = await listConnections();
                if (cancelled) return;
                setConnections(data.items || []);
            } catch (e) {
                if (!cancelled) {
                    setConnections([]);
                }
            } finally {
                if (!cancelled) {
                    setLoadingConnections(false);
                }
            }
        };
        load();
        return () => {
            cancelled = true;
        };
    }, []);

    const toggleConnection = (id: number) => {
        setSelectedConnectionIds((prev) =>
            prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
        );
    };

    const hasOzon = selectedConnectionIds.some((id) => connections.find((conn) => conn.id === id)?.platform === "ozon");

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-3xl mx-auto"
        >
            <Card className="glass-card border-none text-white">
                <CardHeader className="text-center">
                    <div className="mx-auto bg-accent/20 p-4 rounded-full w-fit mb-4">
                        <Sparkles className="w-8 h-8 text-accent animate-pulse" />
                    </div>
                    <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent to-accent-2">
                        {STR.magic.title}
                    </CardTitle>
                    <CardDescription className="text-gray-300">
                        {STR.magic.subtitle}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label>{STR.magic.inputLabel}</Label>
                            <Input
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder={STR.magic.inputPlaceholder}
                                className="bg-black/20 border-white/10 text-white placeholder:text-gray-500 h-12"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Описание бизнеса</Label>
                            <Textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Чем занимаетесь, что продаёте, кто клиенты..."
                                className="bg-black/20 border-white/10 text-white placeholder:text-gray-500 min-h-[100px]"
                            />
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label>Количество объявлений</Label>
                                <Select value={adCount} onValueChange={setAdCount}>
                                    <SelectTrigger className="bg-black/20 border-white/10 text-white">
                                        <SelectValue placeholder="Выберите количество" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="3">3 объявления</SelectItem>
                                        <SelectItem value="6">6 объявлений</SelectItem>
                                        <SelectItem value="9">9 объявлений</SelectItem>
                                        <SelectItem value="12">12 объявлений</SelectItem>
                                        <SelectItem value="15">15 объявлений</SelectItem>
                                        <SelectItem value="20">20 объявлений</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Бюджет в день, ₽</Label>
                                <Input
                                    type="number"
                                    min="100"
                                    value={budgetDaily}
                                    onChange={(e) => setBudgetDaily(e.target.value)}
                                    className="bg-black/20 border-white/10 text-white placeholder:text-gray-500"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Подключения для запуска</Label>
                            <div className="text-xs text-gray-500">
                                Можно выбрать несколько подключений — создадим черновики для каждой площадки.
                            </div>
                            {loadingConnections ? (
                                <div className="text-sm text-muted">Загружаем подключения...</div>
                            ) : connections.length === 0 ? (
                                <div className="rounded-lg border border-dashed border-white/10 p-4 text-sm text-muted">
                                    Подключений пока нет. Перейдите в
                                    <Link href="/connections" className="ml-1 text-accent hover:underline">
                                        подключения
                                    </Link>
                                    , чтобы запустить рекламу.
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {connections.map((conn) => (
                                        <label
                                            key={conn.id}
                                            className="flex items-center gap-3 rounded-lg border border-white/10 bg-black/20 px-3 py-2"
                                        >
                                            <Checkbox
                                                checked={selectedConnectionIds.includes(conn.id)}
                                                onCheckedChange={() => toggleConnection(conn.id)}
                                            />
                                            <div className="flex flex-col">
                                                <span className="text-sm text-white">{conn.name || platformLabels[conn.platform] || conn.platform}</span>
                                                <span className="text-xs text-gray-500">{platformLabels[conn.platform] || conn.platform}</span>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                        {hasOzon && (
                            <div className="space-y-2">
                                <Label>ID товаров Ozon (через запятую)</Label>
                                <Input
                                    value={productIdsRaw}
                                    onChange={(e) => setProductIdsRaw(e.target.value)}
                                    placeholder="12345, 67890"
                                    className="bg-black/20 border-white/10 text-white placeholder:text-gray-500"
                                />
                            </div>
                        )}
                        <Button
                            type="submit"
                            className="w-full h-12 text-lg bg-accent hover:bg-accent/90 text-white font-semibold shadow-soft"
                            disabled={isLoading || loadingConnections || connections.length === 0}
                        >
                            {isLoading ? (
                                <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> {STR.magic.analyzing}</>
                            ) : (
                                <>{STR.magic.generateButton} <ArrowRight className="ml-2 h-5 w-5" /></>
                            )}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </motion.div>
    );
}

function StepProcessing() {
    return (
        <div className="text-center py-20">
            <div className="relative inline-block">
                <div className="absolute inset-0 bg-accent blur-3xl opacity-20 animate-pulse rounded-full"></div>
                <div className="relative bg-panel-strong p-8 rounded-full border border-white/5 animate-float">
                    <Sparkles className="w-16 h-16 text-accent" />
                </div>
            </div>
            <h3 className="mt-8 text-2xl font-bold text-white">{STR.magic.processing}</h3>
            <p className="mt-2 text-gray-400">{STR.magic.processingHint}</p>
        </div>
    );
}

function StepSuccess({ run, onReset }: { run: MagicRun; onReset: () => void }) {
    const [publishing, setPublishing] = useState(false);
    const result = run.result_json || {};
    const campaignName = result.business_name ? `Magic: ${result.business_name}` : "Новая кампания";
    const ads = Array.isArray(result.ads) ? result.ads : [];
    const drafts = Array.isArray(result.drafts) ? result.drafts : [];
    const draftsCount = drafts.length;

    const handlePublishAll = async () => {
        if (!drafts.length) {
            toast.error("Нет черновиков для запуска");
            return;
        }
        setPublishing(true);
        const results = await Promise.allSettled(drafts.map((draft: any) => DraftsApi.publish(draft.id)));
        const successCount = results.filter((res) => res.status === "fulfilled").length;
        const failedCount = results.length - successCount;
        if (successCount > 0) {
            toast.success(`Запущено кампаний: ${successCount}`);
        }
        if (failedCount > 0) {
            toast.error(`Не удалось запустить: ${failedCount}`);
        }
        setPublishing(false);
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto"
        >
            <Card className="glass-card border-none">
                <CardHeader className="text-center pb-2">
                    <div className="mx-auto bg-green-500/20 p-3 rounded-full w-fit mb-4">
                        <CheckCircle2 className="w-8 h-8 text-green-400" />
                    </div>
                    <CardTitle className="text-2xl text-white">{STR.magic.successTitle}</CardTitle>
                    <CardDescription className="text-gray-300">
                        {STR.magic.successDesc}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="bg-black/30 rounded-xl p-6 border border-white/5">
                        <h4 className="text-lg font-semibold text-accent mb-2">{campaignName}</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
                            <div className="flex flex-col">
                                <span className="text-gray-500 mb-1">Объявлений</span>
                                <span className="text-white text-lg font-medium">{ads.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-gray-500 mb-1">Кампаний</span>
                                <span className="text-white text-lg font-medium">{draftsCount}</span>
                            </div>
                        </div>
                    </div>
                    {ads.length > 0 && (
                        <div className="grid gap-3">
                            <div className="text-sm text-gray-400">Превью объявлений</div>
                            <div className="grid gap-3 md:grid-cols-3">
                                {ads.slice(0, 3).map((ad: any, index: number) => (
                                    <div key={index} className="rounded-lg border border-white/10 bg-black/20 p-3">
                                        <div className="text-sm font-semibold text-white">{ad.title || "Без заголовка"}</div>
                                        <div className="mt-1 text-xs text-gray-400">{ad.text || "Без текста"}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {drafts.length > 0 && (
                        <div className="grid gap-3">
                            <Button
                                className="w-full bg-green-600 hover:bg-green-500"
                                onClick={handlePublishAll}
                                disabled={publishing}
                            >
                                {publishing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                Запустить все площадки
                            </Button>
                            <div className="text-sm text-gray-400">Черновики для запуска</div>
                            <div className="grid gap-2 md:grid-cols-2">
                                {drafts.map((draft: any) => (
                                    <Link key={draft.id} href={`/drafts/${draft.id}`}>
                                        <Button variant="secondary" className="w-full justify-between">
                                            <span>Открыть {typeof draft.platform === "string" ? draft.platform.toUpperCase() : "черновик"}</span>
                                            <ArrowRight className="h-4 w-4" />
                                        </Button>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="flex gap-4">
                        <Button variant="outline" className="flex-1 border-white/10 text-white hover:bg-white/5" onClick={onReset}>
                            {STR.magic.createAnother}
                        </Button>
                        <Link href="/drafts" className="flex-1">
                            <Button className="w-full bg-accent hover:bg-accent/90">
                                {STR.magic.viewDrafts} <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}

function StepError({ error, onReset }: { error: string; onReset: () => void }) {
    return (
        <div className="max-w-md mx-auto text-center">
            <Card className="bg-red-950/30 border-red-500/30">
                <CardHeader>
                    <div className="mx-auto bg-red-500/20 p-3 rounded-full w-fit mb-4">
                        <AlertCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <CardTitle className="text-red-400">{STR.magic.errorTitle}</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-red-200 mb-6">{error}</p>
                    <Button onClick={onReset} variant="outline" className="border-red-500/30 text-red-300 hover:bg-red-500/10">
                        {STR.magic.tryAgain}
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

// --- Main Wizard ---

export function MagicWizard() {
    const [step, setStep] = useState<'input' | 'processing' | 'success' | 'error'>('input');
    const [run, setRun] = useState<MagicRun | null>(null);
    const [error, setError] = useState<string>("");

    const startMagic = async (payload: MagicRunPayload) => {
        setError("");
        setStep('processing');
        try {
            const newRun = await MagicApi.createRun(payload);
            setRun(newRun);

            // Poll for completion
            const interval = setInterval(async () => {
                try {
                    const updated = await MagicApi.getRun(newRun.id);
                    if (updated.status === 'success' || updated.status === 'done') {
                        setRun(updated);
                        setStep('success');
                        clearInterval(interval);
                    } else if (updated.status === 'failed') {
                        setError(updated.error || "Неизвестная ошибка");
                        setStep('error');
                        clearInterval(interval);
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1000);

        } catch (e: any) {
            setError(e.message || "Ошибка при создании кампании");
            setStep('error');
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6">
            <AnimatePresence mode="wait">
                {step === 'input' && (
                    <StepInput key="input" onStart={startMagic} isLoading={false} />
                )}
                {step === 'processing' && (
                    <motion.div
                        key="processing"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <StepProcessing />
                    </motion.div>
                )}
                {step === 'success' && run && (
                    <StepSuccess key="success" run={run} onReset={() => setStep('input')} />
                )}
                {step === 'error' && (
                    <StepError key="error" error={error} onReset={() => setStep('input')} />
                )}
            </AnimatePresence>
        </div>
    );
}
