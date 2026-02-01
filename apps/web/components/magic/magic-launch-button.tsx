"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
    Loader2,
    Rocket,
    ArrowRight,
    CheckCircle2,
    AlertCircle,
    DollarSign,
    Zap,
    Target,
    TrendingUp,
    Play,
    Sparkles,
    Image as ImageIcon,
    Mic,
    Video
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { getToken, getOrgId } from "@/lib/session";

// Types
interface LaunchResult {
    status: string;
    business_name?: string;
    total_budget: number;
    budget_launched: number;
    platforms_launched: number;
    platforms_total: number;
    campaigns: PlatformResult[];
    creatives: {
        ads_count: number;
        images_count: number;
        voiceovers_count: number;
        videos_count: number;
    };
    ai_provider?: string;
    launched_at: string;
}

interface PlatformResult {
    platform: string;
    status: string;
    draft_campaign_id?: number;
    external_id?: string;
    budget: number;
    ads_count: number;
    message?: string;
}

interface EstimateResult {
    total: {
        impressions: number;
        clicks: number;
        leads: number;
        budget: number;
    };
    by_platform: Record<string, {
        impressions: number;
        clicks: number;
        leads: number;
        budget: number;
    }>;
    disclaimer: string;
}

// API calls
const api = {
    async launch(data: {
        landing_url?: string;
        business_description?: string;
        budget: number;
        platforms?: string[];
        auto_start: boolean;
        generate_images: boolean;
        generate_voice: boolean;
        generate_video: boolean;
    }): Promise<LaunchResult> {
        const token = getToken();
        const orgId = getOrgId();
        const res = await fetch('/api/magic-launch/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...(orgId ? { 'X-Org-Id': orgId } : {})
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Launch failed');
        }
        return res.json();
    },

    async estimate(data: {
        budget: number;
        platforms: string[];
        business_type?: string;
    }): Promise<EstimateResult> {
        const token = getToken();
        const orgId = getOrgId();
        const res = await fetch('/api/magic-launch/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...(orgId ? { 'X-Org-Id': orgId } : {})
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        if (!res.ok) throw new Error('Estimate failed');
        return res.json();
    },

    async getPlatforms(): Promise<{ platforms: Array<{ platform: string; name: string; status: string }> }> {
        const token = getToken();
        const orgId = getOrgId();
        const res = await fetch('/api/magic-launch/platforms', {
            headers: {
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...(orgId ? { 'X-Org-Id': orgId } : {})
            },
            credentials: 'include'
        });
        if (!res.ok) throw new Error('Failed to get platforms');
        return res.json();
    }
};

// Format number with K/M suffixes
function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// Format currency
function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        maximumFractionDigits: 0
    }).format(amount);
}

// Step 1: Input
function StepInput({
    onNext,
    isLoading
}: {
    onNext: (data: any) => void;
    isLoading: boolean;
}) {
    const [url, setUrl] = useState("");
    const [description, setDescription] = useState("");
    const [budget, setBudget] = useState(10000);
    const [generateImages, setGenerateImages] = useState(true);
    const [generateVoice, setGenerateVoice] = useState(false);
    const [generateVideo, setGenerateVideo] = useState(false);
    const [estimate, setEstimate] = useState<EstimateResult | null>(null);

    // Get estimate when budget changes
    useEffect(() => {
        const timer = setTimeout(async () => {
            try {
                const result = await api.estimate({
                    budget,
                    platforms: ['yandex', 'vk']
                });
                setEstimate(result);
            } catch (e) {
                console.error('Estimate failed:', e);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [budget]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onNext({
            landing_url: url || undefined,
            business_description: description || undefined,
            budget,
            auto_start: true,
            generate_images: generateImages,
            generate_voice: generateVoice,
            generate_video: generateVideo
        });
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl mx-auto"
        >
            <Card className="bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-cyan-900/40 border-none shadow-2xl">
                <CardHeader className="text-center pb-2">
                    <div className="mx-auto relative mb-4">
                        <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-orange-500 blur-2xl opacity-30 animate-pulse"></div>
                        <div className="relative bg-gradient-to-r from-yellow-400 to-orange-500 p-4 rounded-full">
                            <DollarSign className="w-10 h-10 text-white" />
                        </div>
                    </div>
                    <CardTitle className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500">
                        MAGIC LAUNCH
                    </CardTitle>
                    <CardDescription className="text-lg text-gray-300">
                        Один клик - реклама на всех площадках
                    </CardDescription>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* URL Input */}
                        <div className="space-y-2">
                            <Label className="text-white">Ваш сайт (необязательно)</Label>
                            <Input
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://your-site.ru"
                                className="bg-black/30 border-white/10 text-white h-12"
                            />
                        </div>

                        {/* Description */}
                        <div className="space-y-2">
                            <Label className="text-white">Опишите ваш бизнес</Label>
                            <Input
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Продаем кроссовки Nike с доставкой по России"
                                className="bg-black/30 border-white/10 text-white h-12"
                            />
                        </div>

                        {/* Budget Slider */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <Label className="text-white">Бюджет</Label>
                                <span className="text-2xl font-bold text-yellow-400">
                                    {formatCurrency(budget)}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="5000"
                                max="500000"
                                step="5000"
                                value={budget}
                                onChange={(e) => setBudget(Number(e.target.value))}
                                className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-400"
                            />
                            <div className="flex justify-between text-xs text-gray-400">
                                <span>5 000 RUB</span>
                                <span>500 000 RUB</span>
                            </div>
                        </div>

                        {/* Estimate Preview */}
                        {estimate && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="bg-black/30 rounded-xl p-4 border border-white/10"
                            >
                                <h4 className="text-sm font-medium text-gray-400 mb-3">
                                    Прогноз результатов
                                </h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="text-center">
                                        <Target className="w-5 h-5 mx-auto mb-1 text-blue-400" />
                                        <div className="text-xl font-bold text-white">
                                            {formatNumber(estimate.total.impressions)}
                                        </div>
                                        <div className="text-xs text-gray-400">Показов</div>
                                    </div>
                                    <div className="text-center">
                                        <Zap className="w-5 h-5 mx-auto mb-1 text-yellow-400" />
                                        <div className="text-xl font-bold text-white">
                                            {formatNumber(estimate.total.clicks)}
                                        </div>
                                        <div className="text-xs text-gray-400">Кликов</div>
                                    </div>
                                    <div className="text-center">
                                        <TrendingUp className="w-5 h-5 mx-auto mb-1 text-green-400" />
                                        <div className="text-xl font-bold text-white">
                                            {formatNumber(estimate.total.leads)}
                                        </div>
                                        <div className="text-xs text-gray-400">Лидов</div>
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {/* Creative Options */}
                        <div className="bg-black/20 rounded-xl p-4 space-y-3">
                            <h4 className="text-sm font-medium text-gray-300 mb-2">
                                AI-генерация
                            </h4>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <ImageIcon className="w-4 h-4 text-purple-400" />
                                    <span className="text-white text-sm">Изображения</span>
                                </div>
                                <Switch
                                    checked={generateImages}
                                    onCheckedChange={setGenerateImages}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Mic className="w-4 h-4 text-blue-400" />
                                    <span className="text-white text-sm">Озвучка</span>
                                    <span className="text-xs text-gray-500">(ElevenLabs)</span>
                                </div>
                                <Switch
                                    checked={generateVoice}
                                    onCheckedChange={setGenerateVoice}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Video className="w-4 h-4 text-pink-400" />
                                    <span className="text-white text-sm">Видео</span>
                                    <span className="text-xs text-gray-500">(HeyGen)</span>
                                </div>
                                <Switch
                                    checked={generateVideo}
                                    onCheckedChange={setGenerateVideo}
                                />
                            </div>
                        </div>

                        {/* Launch Button */}
                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full h-16 text-xl font-bold bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 hover:from-yellow-300 hover:via-orange-400 hover:to-red-400 text-white shadow-lg shadow-orange-500/30 transition-all hover:shadow-xl hover:shadow-orange-500/40 hover:scale-[1.02]"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                                    Запускаем...
                                </>
                            ) : (
                                <>
                                    <Rocket className="mr-2 h-6 w-6" />
                                    ЗАПУСТИТЬ РЕКЛАМУ
                                    <ArrowRight className="ml-2 h-6 w-6" />
                                </>
                            )}
                        </Button>

                        <p className="text-center text-xs text-gray-500">
                            AI создаст объявления и запустит рекламу на Яндекс.Директ и VK Ads
                        </p>
                    </form>
                </CardContent>
            </Card>
        </motion.div>
    );
}

// Step 2: Processing with live progress
function StepProcessing({
    progress,
    currentStep,
    totalSteps,
    message
}: {
    progress: number;
    currentStep: number;
    totalSteps: number;
    message: string;
}) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 max-w-md mx-auto"
        >
            <div className="relative mb-8">
                <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-orange-500 blur-3xl opacity-20 animate-pulse"></div>
                <div className="relative">
                    <svg className="w-32 h-32 mx-auto" viewBox="0 0 100 100">
                        <circle
                            className="stroke-gray-700"
                            strokeWidth="8"
                            fill="transparent"
                            r="42"
                            cx="50"
                            cy="50"
                        />
                        <circle
                            className="stroke-yellow-400 transition-all duration-500"
                            strokeWidth="8"
                            strokeLinecap="round"
                            fill="transparent"
                            r="42"
                            cx="50"
                            cy="50"
                            style={{
                                strokeDasharray: `${2 * Math.PI * 42}`,
                                strokeDashoffset: `${2 * Math.PI * 42 * (1 - progress / 100)}`,
                                transform: 'rotate(-90deg)',
                                transformOrigin: '50% 50%'
                            }}
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-3xl font-bold text-white">{progress}%</span>
                    </div>
                </div>
            </div>

            <h3 className="text-2xl font-bold text-white mb-2">
                {message}
            </h3>
            <p className="text-gray-400">
                Шаг {currentStep} из {totalSteps}
            </p>

            <div className="mt-8 flex justify-center gap-2">
                {Array.from({ length: totalSteps }).map((_, i) => (
                    <div
                        key={i}
                        className={cn(
                            "w-3 h-3 rounded-full transition-all",
                            i < currentStep
                                ? "bg-yellow-400"
                                : i === currentStep - 1
                                    ? "bg-yellow-400 animate-pulse"
                                    : "bg-gray-700"
                        )}
                    />
                ))}
            </div>
        </motion.div>
    );
}

// Step 3: Success
function StepSuccess({
    result,
    onReset
}: {
    result: LaunchResult;
    onReset: () => void;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto"
        >
            <Card className="bg-gradient-to-br from-green-900/40 to-emerald-900/40 border-none">
                <CardHeader className="text-center pb-2">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", delay: 0.2 }}
                        className="mx-auto bg-green-500/20 p-4 rounded-full w-fit mb-4"
                    >
                        <CheckCircle2 className="w-12 h-12 text-green-400" />
                    </motion.div>
                    <CardTitle className="text-3xl text-white">
                        Реклама запущена!
                    </CardTitle>
                    <CardDescription className="text-lg text-green-200">
                        {result.business_name}
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-6">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-black/30 rounded-xl p-4 text-center">
                            <div className="text-2xl font-bold text-white">
                                {result.platforms_launched}
                            </div>
                            <div className="text-xs text-gray-400">Площадок</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 text-center">
                            <div className="text-2xl font-bold text-yellow-400">
                                {formatCurrency(result.budget_launched)}
                            </div>
                            <div className="text-xs text-gray-400">Бюджет</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 text-center">
                            <div className="text-2xl font-bold text-purple-400">
                                {result.creatives.ads_count}
                            </div>
                            <div className="text-xs text-gray-400">Объявлений</div>
                        </div>
                        <div className="bg-black/30 rounded-xl p-4 text-center">
                            <div className="text-2xl font-bold text-blue-400">
                                {result.creatives.images_count}
                            </div>
                            <div className="text-xs text-gray-400">Изображений</div>
                        </div>
                    </div>

                    {/* Platform Results */}
                    <div className="space-y-3">
                        {result.campaigns.map((campaign, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3 + i * 0.1 }}
                                className="flex items-center justify-between bg-black/30 rounded-xl p-4"
                            >
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold",
                                        campaign.platform === 'yandex' ? "bg-yellow-500/20 text-yellow-400" :
                                            campaign.platform === 'vk' ? "bg-blue-500/20 text-blue-400" :
                                                "bg-purple-500/20 text-purple-400"
                                    )}>
                                        {campaign.platform[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="font-medium text-white capitalize">
                                            {campaign.platform === 'yandex' ? 'Яндекс.Директ' :
                                                campaign.platform === 'vk' ? 'VK Ads' :
                                                    campaign.platform}
                                        </div>
                                        <div className="text-sm text-gray-400">
                                            {campaign.ads_count} объявлений
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {campaign.status === 'launched' ? (
                                        <span className="flex items-center gap-1 text-green-400 text-sm">
                                            <Play className="w-4 h-4" /> Запущено
                                        </span>
                                    ) : (
                                        <span className="text-yellow-400 text-sm">
                                            {campaign.message || 'Черновик'}
                                        </span>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* AI Provider Badge */}
                    {result.ai_provider && (
                        <div className="flex justify-center">
                            <span className="inline-flex items-center gap-1 text-xs text-gray-400 bg-black/30 px-3 py-1 rounded-full">
                                <Sparkles className="w-3 h-3" />
                                Сгенерировано: {result.ai_provider}
                            </span>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-4">
                        <Button
                            variant="outline"
                            className="flex-1 border-white/10 text-white hover:bg-white/5"
                            onClick={onReset}
                        >
                            Запустить ещё
                        </Button>
                        <Link href="/dashboard" className="flex-1">
                            <Button className="w-full bg-green-500 hover:bg-green-600">
                                Смотреть статистику
                                <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}

// Step 4: Error
function StepError({
    error,
    onReset
}: {
    error: string;
    onReset: () => void;
}) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="max-w-md mx-auto text-center"
        >
            <Card className="bg-red-950/30 border-red-500/30">
                <CardHeader>
                    <div className="mx-auto bg-red-500/20 p-4 rounded-full w-fit mb-4">
                        <AlertCircle className="w-10 h-10 text-red-400" />
                    </div>
                    <CardTitle className="text-2xl text-red-400">
                        Ошибка запуска
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-red-200 mb-6">{error}</p>
                    <Button
                        onClick={onReset}
                        variant="outline"
                        className="border-red-500/30 text-red-300 hover:bg-red-500/10"
                    >
                        Попробовать снова
                    </Button>
                </CardContent>
            </Card>
        </motion.div>
    );
}

// Main Component
export function MagicLaunchButton() {
    const [step, setStep] = useState<'input' | 'processing' | 'success' | 'error'>('input');
    const [result, setResult] = useState<LaunchResult | null>(null);
    const [error, setError] = useState<string>("");
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState(1);
    const [message, setMessage] = useState("Подготовка...");
    const [isLoading, setIsLoading] = useState(false);

    const handleLaunch = async (data: any) => {
        setIsLoading(true);
        setStep('processing');
        setProgress(0);
        setCurrentStep(1);
        setMessage("Анализируем ваш бизнес...");

        try {
            // Use SSE for real-time progress
            const token = getToken();
            const orgId = getOrgId();
            const response = await fetch('/api/magic-launch/launch-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                    ...(orgId ? { 'X-Org-Id': orgId } : {})
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Launch failed');
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                // Fallback to regular API
                const result = await api.launch(data);
                setResult(result);
                setStep('success');
                return;
            }

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const event = JSON.parse(line.slice(6));

                            if (event.type === 'step') {
                                setCurrentStep(event.step);
                                setMessage(event.message);
                            } else if (event.type === 'progress') {
                                setProgress(event.percent);
                            } else if (event.type === 'result') {
                                setResult(event.data);
                            } else if (event.type === 'done') {
                                setStep('success');
                            } else if (event.type === 'error') {
                                throw new Error(event.message);
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
            }

        } catch (e: any) {
            setError(e.message || "Произошла ошибка при запуске");
            setStep('error');
        } finally {
            setIsLoading(false);
        }
    };

    const handleReset = () => {
        setStep('input');
        setResult(null);
        setError("");
        setProgress(0);
        setCurrentStep(1);
    };

    return (
        <div className="w-full p-4 md:p-8">
            <AnimatePresence mode="wait">
                {step === 'input' && (
                    <StepInput
                        key="input"
                        onNext={handleLaunch}
                        isLoading={isLoading}
                    />
                )}
                {step === 'processing' && (
                    <StepProcessing
                        key="processing"
                        progress={progress}
                        currentStep={currentStep}
                        totalSteps={5}
                        message={message}
                    />
                )}
                {step === 'success' && result && (
                    <StepSuccess
                        key="success"
                        result={result}
                        onReset={handleReset}
                    />
                )}
                {step === 'error' && (
                    <StepError
                        key="error"
                        error={error}
                        onReset={handleReset}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}
