"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import {
    Brain, Target, TrendingUp, Users, Mic, Loader2,
    Search, Sparkles, BarChart3, Zap, CheckCircle2,
    AlertTriangle, ArrowRight, Play, Star, Shield,
    Lightbulb, Eye, MessageSquare
} from "lucide-react";
import { toast } from "sonner";

// Types
interface CompetitorAnalysis {
    competitor_name: string;
    competitor_strengths: string[];
    competitor_weaknesses: string[];
    opportunities_for_you: string[];
    recommended_counter_strategies: Array<{
        strategy: string;
        description: string;
        expected_impact: string;
    }>;
    ad_copy_suggestions: Array<{
        headline: string;
        text: string;
        angle: string;
    }>;
    overall_threat_level: string;
}

interface ROIPrediction {
    predictions: {
        impressions: number;
        clicks: number;
        conversions: number;
        revenue: number;
        roi_percent: number;
        roas: number;
    };
    scenarios: {
        pessimistic: { conversions: number; revenue: number; roi: number };
        realistic: { conversions: number; revenue: number; roi: number };
        optimistic: { conversions: number; revenue: number; roi: number };
    };
    confidence: number;
    recommendations: string[];
}

interface CreativeScore {
    overall_score: number;
    dimensions: Record<string, { score: number; feedback: string }>;
    strengths: string[];
    weaknesses: string[];
    improvement_suggestions: Array<{
        issue: string;
        suggestion: string;
        improved_version: string;
    }>;
    predicted_ctr_range: string;
}

// Format helpers
const formatNumber = (n: number) => new Intl.NumberFormat('ru-RU').format(n);
const formatCurrency = (n: number) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(n);

// Competitor Analysis Tab
function CompetitorTab() {
    const [competitorUrl, setCompetitorUrl] = useState("");
    const [yourBusiness, setYourBusiness] = useState("");
    const [loading, setLoading] = useState(false);
    const [analysis, setAnalysis] = useState<CompetitorAnalysis | null>(null);

    const handleAnalyze = async () => {
        if (!competitorUrl || !yourBusiness) {
            toast.error("Заполните все поля");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch('/api/ai/competitors/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    competitor_url: competitorUrl,
                    your_business: yourBusiness
                }),
                credentials: 'include'
            });

            if (!res.ok) throw new Error('Analysis failed');
            const data = await res.json();
            setAnalysis(data);
            toast.success("Анализ завершён!");
        } catch (e) {
            toast.error("Ошибка анализа");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
                <div>
                    <Label>URL конкурента</Label>
                    <Input
                        value={competitorUrl}
                        onChange={(e) => setCompetitorUrl(e.target.value)}
                        placeholder="https://competitor.ru"
                        className="mt-1"
                    />
                </div>
                <div>
                    <Label>Ваш бизнес</Label>
                    <Input
                        value={yourBusiness}
                        onChange={(e) => setYourBusiness(e.target.value)}
                        placeholder="Интернет-магазин кроссовок"
                        className="mt-1"
                    />
                </div>
            </div>

            <Button onClick={handleAnalyze} disabled={loading} className="w-full">
                {loading ? <Loader2 className="animate-spin mr-2" /> : <Search className="mr-2" />}
                Анализировать конкурента
            </Button>

            {analysis && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                >
                    {/* Threat Level */}
                    <Card className={`border-2 ${
                        analysis.overall_threat_level === 'high' ? 'border-red-500/50 bg-red-500/5' :
                        analysis.overall_threat_level === 'medium' ? 'border-yellow-500/50 bg-yellow-500/5' :
                        'border-green-500/50 bg-green-500/5'
                    }`}>
                        <CardHeader className="pb-2">
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="w-5 h-5" />
                                {analysis.competitor_name}
                            </CardTitle>
                            <CardDescription>
                                Уровень угрозы: <span className="font-bold uppercase">{analysis.overall_threat_level}</span>
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    {/* Strengths & Weaknesses */}
                    <div className="grid md:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-green-400 flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4" />
                                    Их сильные стороны
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-1">
                                    {analysis.competitor_strengths.slice(0, 5).map((s, i) => (
                                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                                            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
                                            {s}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-red-400 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4" />
                                    Их слабые стороны
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-1">
                                    {analysis.competitor_weaknesses.slice(0, 5).map((w, i) => (
                                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                                            <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                                            {w}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Counter Strategies */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="w-5 h-5 text-yellow-400" />
                                Рекомендуемые стратегии
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {analysis.recommended_counter_strategies.slice(0, 3).map((strategy, i) => (
                                    <div key={i} className="bg-black/20 rounded-lg p-3">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="font-medium text-white">{strategy.strategy}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded ${
                                                strategy.expected_impact === 'high' ? 'bg-green-500/20 text-green-400' :
                                                strategy.expected_impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-gray-500/20 text-gray-400'
                                            }`}>
                                                {strategy.expected_impact} impact
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400">{strategy.description}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Ad Suggestions */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <MessageSquare className="w-5 h-5 text-purple-400" />
                                Готовые объявления
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid md:grid-cols-2 gap-3">
                                {analysis.ad_copy_suggestions.slice(0, 4).map((ad, i) => (
                                    <div key={i} className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-lg p-3 border border-purple-500/20">
                                        <div className="font-medium text-white mb-1">{ad.headline}</div>
                                        <p className="text-sm text-gray-300 mb-2">{ad.text}</p>
                                        <div className="text-xs text-purple-400">Угол: {ad.angle}</div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}

// ROI Prediction Tab
function ROITab() {
    const [budget, setBudget] = useState(50000);
    const [industry, setIndustry] = useState("ecommerce");
    const [business, setBusiness] = useState("");
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState<ROIPrediction | null>(null);

    const industries = [
        { id: "ecommerce", name: "E-commerce" },
        { id: "services", name: "Услуги" },
        { id: "saas", name: "SaaS / IT" },
        { id: "education", name: "Образование" },
        { id: "beauty", name: "Красота" },
        { id: "auto", name: "Авто" },
    ];

    const handlePredict = async () => {
        if (!business) {
            toast.error("Опишите ваш бизнес");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch('/api/ai/predict/roi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    budget,
                    industry,
                    business_description: business,
                    platforms: ["yandex", "vk"]
                }),
                credentials: 'include'
            });

            if (!res.ok) throw new Error('Prediction failed');
            const data = await res.json();
            setPrediction(data);
            toast.success("Прогноз готов!");
        } catch (e) {
            toast.error("Ошибка прогноза");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
                <div>
                    <Label>Бюджет (RUB)</Label>
                    <Input
                        type="number"
                        value={budget}
                        onChange={(e) => setBudget(Number(e.target.value))}
                        className="mt-1"
                    />
                </div>
                <div>
                    <Label>Индустрия</Label>
                    <select
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        className="mt-1 w-full h-10 rounded-md border border-border bg-panel px-3 text-sm"
                    >
                        {industries.map(ind => (
                            <option key={ind.id} value={ind.id}>{ind.name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <Label>Ваш бизнес</Label>
                    <Input
                        value={business}
                        onChange={(e) => setBusiness(e.target.value)}
                        placeholder="Доставка еды в Москве"
                        className="mt-1"
                    />
                </div>
            </div>

            <Button onClick={handlePredict} disabled={loading} className="w-full">
                {loading ? <Loader2 className="animate-spin mr-2" /> : <TrendingUp className="mr-2" />}
                Спрогнозировать ROI
            </Button>

            {prediction && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                >
                    {/* Main Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {[
                            { label: "Показы", value: formatNumber(prediction.predictions.impressions), icon: Eye },
                            { label: "Клики", value: formatNumber(prediction.predictions.clicks), icon: Target },
                            { label: "Конверсии", value: prediction.predictions.conversions, icon: CheckCircle2 },
                            { label: "Выручка", value: formatCurrency(prediction.predictions.revenue), icon: TrendingUp },
                        ].map((m, i) => (
                            <Card key={i} className="bg-gradient-to-br from-blue-500/10 to-purple-500/10">
                                <CardContent className="p-4 text-center">
                                    <m.icon className="w-5 h-5 mx-auto mb-2 text-blue-400" />
                                    <div className="text-2xl font-bold text-white">{m.value}</div>
                                    <div className="text-xs text-gray-400">{m.label}</div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* ROI & ROAS */}
                    <div className="grid md:grid-cols-2 gap-4">
                        <Card className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 border-green-500/30">
                            <CardContent className="p-6 text-center">
                                <div className="text-5xl font-black text-green-400">
                                    {prediction.predictions.roi_percent > 0 ? '+' : ''}{prediction.predictions.roi_percent.toFixed(0)}%
                                </div>
                                <div className="text-gray-300 mt-2">Прогнозируемый ROI</div>
                            </CardContent>
                        </Card>

                        <Card className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-500/30">
                            <CardContent className="p-6 text-center">
                                <div className="text-5xl font-black text-yellow-400">
                                    {prediction.predictions.roas.toFixed(1)}x
                                </div>
                                <div className="text-gray-300 mt-2">ROAS</div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Scenarios */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Сценарии</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid md:grid-cols-3 gap-4">
                                {Object.entries(prediction.scenarios).map(([key, scenario]) => (
                                    <div key={key} className={`p-4 rounded-lg ${
                                        key === 'pessimistic' ? 'bg-red-500/10 border border-red-500/20' :
                                        key === 'realistic' ? 'bg-blue-500/10 border border-blue-500/20' :
                                        'bg-green-500/10 border border-green-500/20'
                                    }`}>
                                        <div className="font-medium mb-2 capitalize">
                                            {key === 'pessimistic' ? 'Пессимистичный' :
                                             key === 'realistic' ? 'Реалистичный' : 'Оптимистичный'}
                                        </div>
                                        <div className="text-sm space-y-1 text-gray-300">
                                            <div>Конверсии: {scenario.conversions}</div>
                                            <div>Выручка: {formatCurrency(scenario.revenue)}</div>
                                            <div>ROI: {scenario.roi.toFixed(0)}%</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Confidence */}
                    <div className="flex items-center justify-between bg-black/20 rounded-lg p-4">
                        <span className="text-gray-400">Уверенность прогноза</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                    style={{ width: `${prediction.confidence}%` }}
                                />
                            </div>
                            <span className="font-bold text-white">{prediction.confidence}%</span>
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    );
}

// Creative Scoring Tab
function CreativeTab() {
    const [title, setTitle] = useState("");
    const [text, setText] = useState("");
    const [loading, setLoading] = useState(false);
    const [score, setScore] = useState<CreativeScore | null>(null);

    const handleScore = async () => {
        if (!title || !text) {
            toast.error("Заполните заголовок и текст");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch('/api/ai/creatives/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, text, platform: "yandex" }),
                credentials: 'include'
            });

            if (!res.ok) throw new Error('Scoring failed');
            const data = await res.json();
            setScore(data);
            toast.success("Оценка готова!");
        } catch (e) {
            toast.error("Ошибка оценки");
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 8) return "text-green-400";
        if (score >= 6) return "text-yellow-400";
        return "text-red-400";
    };

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                <div>
                    <Label>Заголовок объявления</Label>
                    <Input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Кроссовки Nike с доставкой за 1 день"
                        className="mt-1"
                    />
                </div>
                <div>
                    <Label>Текст объявления</Label>
                    <Textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Оригинальные кроссовки Nike Air Max. Бесплатная доставка по Москве. Скидка 20% на первый заказ!"
                        className="mt-1"
                        rows={3}
                    />
                </div>
            </div>

            <Button onClick={handleScore} disabled={loading} className="w-full">
                {loading ? <Loader2 className="animate-spin mr-2" /> : <Star className="mr-2" />}
                Оценить креатив
            </Button>

            {score && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                >
                    {/* Overall Score */}
                    <Card className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-500/30">
                        <CardContent className="p-6 text-center">
                            <div className={`text-7xl font-black ${getScoreColor(score.overall_score)}`}>
                                {score.overall_score}/10
                            </div>
                            <div className="text-gray-300 mt-2">Общая оценка</div>
                            <div className="text-sm text-gray-400 mt-1">
                                Прогноз CTR: {score.predicted_ctr_range}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Dimensions */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Детальная оценка</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {Object.entries(score.dimensions).slice(0, 8).map(([key, dim]) => (
                                    <div key={key} className="bg-black/20 rounded-lg p-3">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs text-gray-400 capitalize">
                                                {key.replace(/_/g, ' ')}
                                            </span>
                                            <span className={`font-bold ${getScoreColor(dim.score)}`}>
                                                {dim.score}
                                            </span>
                                        </div>
                                        <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${
                                                    dim.score >= 8 ? 'bg-green-500' :
                                                    dim.score >= 6 ? 'bg-yellow-500' : 'bg-red-500'
                                                }`}
                                                style={{ width: `${dim.score * 10}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Improvements */}
                    {score.improvement_suggestions.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                                    Рекомендации по улучшению
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {score.improvement_suggestions.map((s, i) => (
                                        <div key={i} className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
                                            <div className="text-sm text-yellow-400 mb-1">{s.issue}</div>
                                            <div className="text-gray-300 mb-2">{s.suggestion}</div>
                                            <div className="bg-black/30 rounded p-2">
                                                <div className="text-xs text-gray-400 mb-1">Улучшенная версия:</div>
                                                <div className="text-green-400">{s.improved_version}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </motion.div>
            )}
        </div>
    );
}

// Voice Assistant Tab
function VoiceTab() {
    const [command, setCommand] = useState("");
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<{ intent: any; response: string } | null>(null);
    const [isListening, setIsListening] = useState(false);

    const exampleCommands = [
        "Покажи статистику за сегодня",
        "Какой CTR у моих кампаний?",
        "Увеличь бюджет на 20%",
        "Останови рекламу",
        "Дай рекомендации"
    ];

    const handleCommand = async (cmd: string = command) => {
        if (!cmd) {
            toast.error("Введите команду");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch('/api/ai/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd }),
                credentials: 'include'
            });

            if (!res.ok) throw new Error('Command failed');
            const data = await res.json();
            setResponse(data);

            // Speak the response
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(data.response);
                utterance.lang = 'ru-RU';
                speechSynthesis.speak(utterance);
            }

        } catch (e) {
            toast.error("Ошибка обработки команды");
        } finally {
            setLoading(false);
        }
    };

    const startListening = () => {
        if (!('webkitSpeechRecognition' in window)) {
            toast.error("Голосовой ввод не поддерживается");
            return;
        }

        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.lang = 'ru-RU';
        recognition.continuous = false;

        recognition.onstart = () => setIsListening(true);
        recognition.onend = () => setIsListening(false);

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setCommand(transcript);
            handleCommand(transcript);
        };

        recognition.start();
    };

    return (
        <div className="space-y-6">
            {/* Voice Input */}
            <div className="text-center">
                <motion.button
                    onClick={startListening}
                    disabled={loading || isListening}
                    className={`w-24 h-24 rounded-full ${
                        isListening
                            ? 'bg-red-500 animate-pulse'
                            : 'bg-gradient-to-br from-violet-500 to-fuchsia-500 hover:from-violet-400 hover:to-fuchsia-400'
                    } flex items-center justify-center mx-auto shadow-lg shadow-violet-500/30`}
                    whileTap={{ scale: 0.95 }}
                >
                    <Mic className={`w-10 h-10 text-white ${isListening ? 'animate-bounce' : ''}`} />
                </motion.button>
                <p className="mt-4 text-gray-400">
                    {isListening ? 'Слушаю...' : 'Нажмите для голосовой команды'}
                </p>
            </div>

            {/* Text Input */}
            <div className="flex gap-2">
                <Input
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="Или введите команду текстом..."
                    onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
                />
                <Button onClick={() => handleCommand()} disabled={loading}>
                    {loading ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                </Button>
            </div>

            {/* Example Commands */}
            <div>
                <Label className="text-gray-400 mb-2 block">Примеры команд:</Label>
                <div className="flex flex-wrap gap-2">
                    {exampleCommands.map((cmd, i) => (
                        <Button
                            key={i}
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                setCommand(cmd);
                                handleCommand(cmd);
                            }}
                            className="text-xs"
                        >
                            {cmd}
                        </Button>
                    ))}
                </div>
            </div>

            {/* Response */}
            {response && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card className="bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border-violet-500/30">
                        <CardContent className="p-6">
                            <div className="flex items-start gap-4">
                                <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center shrink-0">
                                    <Brain className="w-5 h-5 text-violet-400" />
                                </div>
                                <div>
                                    <div className="text-lg text-white mb-2">{response.response}</div>
                                    <div className="text-xs text-gray-400">
                                        Намерение: {response.intent.intent} |
                                        Уверенность: {(response.intent.confidence * 100).toFixed(0)}%
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}

// Main Page
export default function AIStudioPage() {
    return (
        <AppShell>
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                            <Brain className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">AI Studio</h1>
                            <p className="text-gray-400">Ваш AI-ассистент для рекламы</p>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <Tabs defaultValue="competitors" className="space-y-6">
                    <TabsList className="grid grid-cols-4 gap-2 bg-transparent h-auto p-0">
                        {[
                            { value: "competitors", label: "Конкуренты", icon: Search },
                            { value: "roi", label: "ROI Прогноз", icon: TrendingUp },
                            { value: "creative", label: "Оценка креативов", icon: Star },
                            { value: "voice", label: "Голосовой ассистент", icon: Mic },
                        ].map((tab) => (
                            <TabsTrigger
                                key={tab.value}
                                value={tab.value}
                                className="data-[state=active]:bg-violet-500/20 data-[state=active]:border-violet-500/50 border border-white/10 rounded-lg p-3 flex flex-col items-center gap-1"
                            >
                                <tab.icon className="w-5 h-5" />
                                <span className="text-xs">{tab.label}</span>
                            </TabsTrigger>
                        ))}
                    </TabsList>

                    <TabsContent value="competitors">
                        <CompetitorTab />
                    </TabsContent>

                    <TabsContent value="roi">
                        <ROITab />
                    </TabsContent>

                    <TabsContent value="creative">
                        <CreativeTab />
                    </TabsContent>

                    <TabsContent value="voice">
                        <VoiceTab />
                    </TabsContent>
                </Tabs>
            </div>
        </AppShell>
    );
}
