"use client";

import { useEffect, useState } from "react";
import {
    Settings, Key, Brain, Save, Loader2, Eye, EyeOff,
    CheckCircle, AlertCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

interface SystemSettings {
    openai_api_key: string | null;
    anthropic_api_key: string | null;
    ai_model: string;
    ai_temperature: number;
    registration_enabled: boolean;
}

export default function AdminSettingsPage() {
    const [settings, setSettings] = useState<SystemSettings>({
        openai_api_key: "",
        anthropic_api_key: "",
        ai_model: "gpt-4o-mini",
        ai_temperature: 0.7,
        registration_enabled: true
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showOpenAI, setShowOpenAI] = useState(false);
    const [showAnthropic, setShowAnthropic] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch("/api/admin/settings", {
                headers: { "X-Admin-Token": token || "" }
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const saveSettings = async () => {
        setSaving(true);
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch("/api/admin/settings", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-Admin-Token": token || ""
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                toast.success("Настройки сохранены");
                loadSettings();
            }
        } catch (err) {
            toast.error("Ошибка сохранения");
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 text-red-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Настройки</h1>
                <p className="text-gray-400 mt-1">Конфигурация системы</p>
            </div>

            {/* AI API Keys */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-violet-500/20">
                            <Key className="h-5 w-5 text-violet-400" />
                        </div>
                        <div>
                            <CardTitle className="text-white">API Ключи</CardTitle>
                            <CardDescription>Подключение к AI провайдерам</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* OpenAI */}
                    <div className="space-y-2">
                        <Label className="text-gray-300">OpenAI API Key</Label>
                        <div className="flex gap-2">
                            <div className="relative flex-1">
                                <Input
                                    type={showOpenAI ? "text" : "password"}
                                    value={settings.openai_api_key || ""}
                                    onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
                                    placeholder="sk-..."
                                    className="bg-black/30 border-white/10 text-white pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowOpenAI(!showOpenAI)}
                                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                                >
                                    {showOpenAI ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {settings.openai_api_key && !settings.openai_api_key.includes("...") && (
                                <CheckCircle className="h-5 w-5 text-green-400 self-center" />
                            )}
                        </div>
                    </div>

                    {/* Anthropic */}
                    <div className="space-y-2">
                        <Label className="text-gray-300">Anthropic API Key</Label>
                        <div className="flex gap-2">
                            <div className="relative flex-1">
                                <Input
                                    type={showAnthropic ? "text" : "password"}
                                    value={settings.anthropic_api_key || ""}
                                    onChange={(e) => setSettings({ ...settings, anthropic_api_key: e.target.value })}
                                    placeholder="sk-ant-..."
                                    className="bg-black/30 border-white/10 text-white pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowAnthropic(!showAnthropic)}
                                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                                >
                                    {showAnthropic ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* AI Configuration */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-fuchsia-500/20">
                            <Brain className="h-5 w-5 text-fuchsia-400" />
                        </div>
                        <div>
                            <CardTitle className="text-white">Конфигурация AI</CardTitle>
                            <CardDescription>Параметры генерации</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Model */}
                    <div className="space-y-2">
                        <Label className="text-gray-300">Модель по умолчанию</Label>
                        <select
                            value={settings.ai_model}
                            onChange={(e) => setSettings({ ...settings, ai_model: e.target.value })}
                            className="w-full h-10 rounded-md border border-white/10 bg-black/30 px-3 text-white"
                        >
                            <optgroup label="OpenAI">
                                <option value="chatgpt-5.2">ChatGPT 5.2 (Flagship)</option>
                                <option value="chatgpt-5.2-mini">ChatGPT 5.2 Mini (Быстрая)</option>
                                <option value="o3">o3 (Reasoning)</option>
                            </optgroup>
                            <optgroup label="Anthropic">
                                <option value="claude-opus-4.5">Claude Opus 4.5 (Мощная)</option>
                                <option value="claude-sonnet-4.5">Claude Sonnet 4.5 (Рекомендуемая)</option>
                            </optgroup>
                            <optgroup label="Google">
                                <option value="gemini-3-pro">Gemini 3 Pro (Мультимодальная)</option>
                                <option value="gemini-3-flash">Gemini 3 Flash (Быстрая)</option>
                            </optgroup>
                        </select>
                    </div>

                    {/* Temperature */}
                    <div className="space-y-2">
                        <Label className="text-gray-300">
                            Temperature: {settings.ai_temperature}
                        </Label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={settings.ai_temperature}
                            onChange={(e) => setSettings({ ...settings, ai_temperature: parseFloat(e.target.value) })}
                            className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>Консервативно</span>
                            <span>Креативно</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* System Settings */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Settings className="h-5 w-5 text-blue-400" />
                        </div>
                        <div>
                            <CardTitle className="text-white">Системные настройки</CardTitle>
                            <CardDescription>Общие параметры платформы</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Registration */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-white/5">
                        <div>
                            <div className="text-white font-medium">Регистрация пользователей</div>
                            <div className="text-sm text-gray-400">Разрешить новым пользователям регистрироваться</div>
                        </div>
                        <button
                            onClick={() => setSettings({ ...settings, registration_enabled: !settings.registration_enabled })}
                            className={`w-12 h-6 rounded-full transition-colors ${settings.registration_enabled ? 'bg-green-500' : 'bg-gray-600'
                                }`}
                        >
                            <div className={`w-5 h-5 rounded-full bg-white transform transition-transform ${settings.registration_enabled ? 'translate-x-6' : 'translate-x-1'
                                }`} />
                        </button>
                    </div>
                </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end">
                <Button
                    onClick={saveSettings}
                    disabled={saving}
                    className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500"
                >
                    {saving ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Сохранение...
                        </>
                    ) : (
                        <>
                            <Save className="mr-2 h-4 w-4" />
                            Сохранить настройки
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
