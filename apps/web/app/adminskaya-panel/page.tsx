"use client";

import { useEffect, useState } from "react";
import {
    Users, BarChart3, CreditCard, Target, TrendingUp,
    Activity, Loader2, ArrowUp, ArrowDown
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DashboardStats {
    total_users: number;
    new_users_today: number;
    new_users_week: number;
    total_organizations: number;
    total_campaigns: number;
    active_campaigns: number;
    total_balance: number;
    total_spent: number;
    avg_roas: number;
}

export default function AdminDashboardPage() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch("/api/admin/dashboard", {
                headers: { "X-Admin-Token": token || "" }
            });

            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 text-red-500 animate-spin" />
            </div>
        );
    }

    const kpiCards = [
        {
            label: "Всего пользователей",
            value: stats?.total_users || 0,
            icon: Users,
            color: "from-blue-600 to-blue-400",
            change: stats?.new_users_week || 0,
            changeLabel: "за неделю"
        },
        {
            label: "Организаций",
            value: stats?.total_organizations || 0,
            icon: Target,
            color: "from-violet-600 to-violet-400"
        },
        {
            label: "Всего кампаний",
            value: stats?.total_campaigns || 0,
            icon: BarChart3,
            color: "from-fuchsia-600 to-fuchsia-400",
            subValue: stats?.active_campaigns || 0,
            subLabel: "активных"
        },
        {
            label: "Баланс пользователей",
            value: `${(stats?.total_balance || 0).toLocaleString('ru-RU')} ₽`,
            icon: CreditCard,
            color: "from-green-600 to-green-400"
        },
        {
            label: "Общий расход",
            value: `${(stats?.total_spent || 0).toLocaleString('ru-RU')} ₽`,
            icon: TrendingUp,
            color: "from-orange-600 to-orange-400"
        },
        {
            label: "Средний ROAS",
            value: `${stats?.avg_roas || 0}x`,
            icon: Activity,
            color: "from-emerald-600 to-emerald-400"
        },
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Обзор</h1>
                <p className="text-gray-400 mt-1">Статистика платформы Effecto</p>
            </div>

            {/* Today's Stats Banner */}
            <Card className="bg-gradient-to-r from-red-900/30 to-orange-900/30 border-red-500/20">
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-red-300">Новых пользователей сегодня</div>
                            <div className="text-4xl font-bold text-white mt-1">
                                {stats?.new_users_today || 0}
                            </div>
                        </div>
                        <div className="flex items-center gap-2 bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm">
                            <ArrowUp className="h-4 w-4" />
                            +{stats?.new_users_week || 0} за неделю
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {kpiCards.map((card, idx) => (
                    <Card key={idx} className="bg-white/5 border-white/10">
                        <CardContent className="p-6">
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="text-sm text-gray-400">{card.label}</div>
                                    <div className="text-2xl font-bold text-white mt-1">
                                        {card.value}
                                    </div>
                                    {card.subValue !== undefined && (
                                        <div className="text-sm text-gray-500 mt-1">
                                            {card.subValue} {card.subLabel}
                                        </div>
                                    )}
                                    {card.change !== undefined && (
                                        <div className="text-sm text-green-400 mt-1">
                                            +{card.change} {card.changeLabel}
                                        </div>
                                    )}
                                </div>
                                <div className={`p-3 rounded-xl bg-gradient-to-r ${card.color}`}>
                                    <card.icon className="h-6 w-6 text-white" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                        <CardTitle className="text-white">Быстрые действия</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <a href="/adminskaya-panel/users" className="block p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                            <div className="flex items-center gap-3">
                                <Users className="h-5 w-5 text-blue-400" />
                                <span className="text-white">Управление пользователями</span>
                            </div>
                        </a>
                        <a href="/adminskaya-panel/settings" className="block p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                            <div className="flex items-center gap-3">
                                <Target className="h-5 w-5 text-violet-400" />
                                <span className="text-white">Настройки AI</span>
                            </div>
                        </a>
                        <a href="/adminskaya-panel/finances" className="block p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                            <div className="flex items-center gap-3">
                                <CreditCard className="h-5 w-5 text-green-400" />
                                <span className="text-white">Финансы</span>
                            </div>
                        </a>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                        <CardTitle className="text-white">Системный статус</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                            <span className="text-gray-400">API Backend</span>
                            <span className="flex items-center gap-2 text-green-400">
                                <span className="w-2 h-2 rounded-full bg-green-400"></span>
                                Online
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                            <span className="text-gray-400">База данных</span>
                            <span className="flex items-center gap-2 text-green-400">
                                <span className="w-2 h-2 rounded-full bg-green-400"></span>
                                Online
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                            <span className="text-gray-400">AI Providers</span>
                            <span className="flex items-center gap-2 text-yellow-400">
                                <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
                                Mock Mode
                            </span>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
