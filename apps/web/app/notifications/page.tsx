"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
    Bell, Send, CheckCircle2, Settings2,
    Loader2, MessageCircle, AlertTriangle, TrendingUp, Calendar
} from "lucide-react";
import { toast } from "sonner";
import { getOrgId, getToken } from "@/lib/session";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TelegramSettings {
    connected: boolean;
    chat_id: string | null;
    notifications_enabled: boolean;
    alert_budget: boolean;
    alert_ctr: boolean;
    alert_conversions: boolean;
    daily_report: boolean;
    weekly_report: boolean;
}

export default function NotificationsPage() {
    const [settings, setSettings] = useState<TelegramSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [chatId, setChatId] = useState("");
    const [connecting, setConnecting] = useState(false);
    const [testingType, setTestingType] = useState<string | null>(null);

    useEffect(() => {
        loadSettings();
    }, []);

    const buildHeaders = () => {
        const token = getToken();
        const orgId = getOrgId();
        return {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(orgId ? { "X-Org-Id": orgId } : {}),
        };
    };

    const loadSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/telegram/settings`, {
                headers: buildHeaders()
            });
            if (res.ok) {
                setSettings(await res.json());
            }
        } catch {
            console.error("Failed to load settings");
        } finally {
            setLoading(false);
        }
    };

    const connectTelegram = async () => {
        if (!chatId) {
            toast.error("Введите Chat ID");
            return;
        }

        setConnecting(true);
        try {
            const token = getToken();
            if (!token) {
                toast.error("Нужно войти в систему");
                setConnecting(false);
                return;
            }
            const res = await fetch(`${API_BASE}/api/telegram/connect`, {
                method: "POST",
                headers: {
                    ...buildHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ chat_id: chatId })
            });

            if (res.ok) {
                toast.success("Telegram подключён!");
                loadSettings();
            } else {
                toast.error("Ошибка подключения");
            }
        } finally {
            setConnecting(false);
        }
    };

    const updateSettings = async (updates: Partial<TelegramSettings>) => {
        if (!settings) return;

        const newSettings = { ...settings, ...updates };
        setSettings(newSettings);
        setSaving(true);

        try {
            await fetch(`${API_BASE}/api/telegram/settings`, {
                method: "PUT",
                headers: {
                    ...buildHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(newSettings)
            });
            toast.success("Настройки сохранены");
        } catch {
            toast.error("Ошибка сохранения");
        } finally {
            setSaving(false);
        }
    };

    const testNotification = async (type: string) => {
        setTestingType(type);
        try {
            const token = getToken();
            if (!token) {
                toast.error("Нужно войти в систему");
                setTestingType(null);
                return;
            }
            const res = await fetch(`${API_BASE}/api/telegram/test`, {
                method: "POST",
                headers: {
                    ...buildHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ type })
            });

            if (res.ok) {
                toast.success("Уведомление отправлено!");
            } else {
                toast.error("Ошибка отправки");
            }
        } finally {
            setTestingType(null);
        }
    };

    const disconnect = async () => {
        try {
            await fetch(`${API_BASE}/api/telegram/disconnect`, {
                method: "DELETE",
                headers: buildHeaders()
            });
            toast.success("Telegram отключён");
            loadSettings();
        } catch {
            toast.error("Ошибка");
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
                title="Уведомления"
                subtitle="Настройте Telegram-алерты для важных событий"
            />

            {/* Connection */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <MessageCircle className="h-5 w-5 text-accent" />
                        Telegram
                    </CardTitle>
                    <CardDescription>
                        Получайте уведомления о важных событиях в Telegram
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {settings?.connected ? (
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className="h-5 w-5 text-green-500" />
                                <span className="font-medium text-text">Подключено</span>
                                <Badge variant="muted">Chat: {settings.chat_id}</Badge>
                            </div>
                            <Button variant="outline" size="sm" onClick={disconnect}>
                                Отключить
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <ol className="text-sm text-muted space-y-2 list-decimal list-inside">
                                <li>Найдите бота <code>@EffectoBot</code> в Telegram</li>
                                <li>Отправьте команду <code>/start</code></li>
                                <li>Скопируйте полученный Chat ID и вставьте ниже</li>
                            </ol>
                            <div className="flex gap-3">
                                <Input
                                    value={chatId}
                                    onChange={e => setChatId(e.target.value)}
                                    placeholder="Ваш Chat ID"
                                    className="max-w-xs"
                                />
                                <Button onClick={connectTelegram} disabled={connecting}>
                                    {connecting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Подключить"}
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Settings */}
            {settings?.connected && (
                <>
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Bell className="h-5 w-5 text-accent" />
                                Типы уведомлений
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <Switch
                                        checked={settings.notifications_enabled}
                                        onCheckedChange={v => updateSettings({ notifications_enabled: v })}
                                    />
                                    <span className="font-medium text-text">Все уведомления</span>
                                </div>
                            </div>

                            <hr className="border-border" />

                            <div className="grid gap-4">
                                {/* Budget Alert */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                                        <div>
                                            <div className="font-medium text-text">Бюджет заканчивается</div>
                                            <div className="text-sm text-muted">При остатке менее 15%</div>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={settings.alert_budget}
                                        onCheckedChange={v => updateSettings({ alert_budget: v })}
                                        disabled={!settings.notifications_enabled}
                                    />
                                </div>

                                {/* CTR Alert */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <TrendingUp className="h-5 w-5 text-red-500" />
                                        <div>
                                            <div className="font-medium text-text">CTR упал</div>
                                            <div className="text-sm text-muted">При падении на 30%+</div>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={settings.alert_ctr}
                                        onCheckedChange={v => updateSettings({ alert_ctr: v })}
                                        disabled={!settings.notifications_enabled}
                                    />
                                </div>

                                {/* Conversion Alert */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                        <div>
                                            <div className="font-medium text-text">Новые конверсии</div>
                                            <div className="text-sm text-muted">При достижении целей</div>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={settings.alert_conversions}
                                        onCheckedChange={v => updateSettings({ alert_conversions: v })}
                                        disabled={!settings.notifications_enabled}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Reports */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Calendar className="h-5 w-5 text-accent" />
                                Отчёты
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium text-text">Ежедневный отчёт</div>
                                    <div className="text-sm text-muted">Каждый день в 10:00</div>
                                </div>
                                <Switch
                                    checked={settings.daily_report}
                                    onCheckedChange={v => updateSettings({ daily_report: v })}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium text-text">Еженедельный отчёт</div>
                                    <div className="text-sm text-muted">Каждый понедельник в 10:00</div>
                                </div>
                                <Switch
                                    checked={settings.weekly_report}
                                    onCheckedChange={v => updateSettings({ weekly_report: v })}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Test */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Тест уведомлений</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-wrap gap-3">
                                {["test", "budget", "ctr", "conversion", "daily"].map(type => (
                                    <Button
                                        key={type}
                                        variant="outline"
                                        size="sm"
                                        onClick={() => testNotification(type)}
                                        disabled={testingType !== null}
                                    >
                                        {testingType === type ? (
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        ) : (
                                            <Send className="h-4 w-4 mr-2" />
                                        )}
                                        {type === "test" ? "Тест" :
                                            type === "budget" ? "Бюджет" :
                                                type === "ctr" ? "CTR" :
                                                    type === "conversion" ? "Конверсия" : "Отчёт"}
                                    </Button>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
