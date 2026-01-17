"use client";

import { useEffect, useState } from "react";
import {
    Activity, BarChart3, Target, Loader2, TrendingUp,
    CheckCircle, Clock, FileText
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CampaignStats {
    by_platform: Record<string, number>;
    by_status: Record<string, number>;
    recent: Array<{
        id: number;
        name: string;
        platform: string;
        status: string;
        created_at: string;
    }>;
    total_ads: number;
}

export default function AdminCampaignsPage() {
    const [stats, setStats] = useState<CampaignStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch("/api/admin/campaign-stats", {
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

    const platformColors: Record<string, string> = {
        yandex: "from-yellow-600 to-yellow-400",
        google: "from-blue-600 to-blue-400",
        vk: "from-sky-600 to-sky-400",
        facebook: "from-indigo-600 to-indigo-400"
    };

    const statusIcons: Record<string, React.ReactNode> = {
        draft: <FileText className="h-4 w-4" />,
        published: <CheckCircle className="h-4 w-4" />,
        pending: <Clock className="h-4 w-4" />
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Кампании</h1>
                <p className="text-gray-400 mt-1">Статистика рекламных кампаний</p>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Всего кампаний</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {Object.values(stats?.by_status || {}).reduce((a, b) => a + b, 0)}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-violet-500/20">
                                <BarChart3 className="h-6 w-6 text-violet-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Опубликовано</div>
                                <div className="text-3xl font-bold text-green-400 mt-1">
                                    {stats?.by_status?.published || 0}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-green-500/20">
                                <CheckCircle className="h-6 w-6 text-green-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Черновики</div>
                                <div className="text-3xl font-bold text-yellow-400 mt-1">
                                    {stats?.by_status?.draft || 0}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-yellow-500/20">
                                <FileText className="h-6 w-6 text-yellow-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Всего объявлений</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {stats?.total_ads || 0}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-blue-500/20">
                                <Target className="h-6 w-6 text-blue-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* By Platform */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <CardTitle className="text-white">По платформам</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(stats?.by_platform || {}).map(([platform, count]) => (
                            <div
                                key={platform}
                                className="p-4 rounded-xl bg-white/5 border border-white/10"
                            >
                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${platformColors[platform] || 'from-gray-600 to-gray-400'} text-white mb-2`}>
                                    {platform.toUpperCase()}
                                </div>
                                <div className="text-2xl font-bold text-white">{count}</div>
                                <div className="text-sm text-gray-400">кампаний</div>
                            </div>
                        ))}
                        {Object.keys(stats?.by_platform || {}).length === 0 && (
                            <div className="col-span-4 text-center text-gray-500 py-8">
                                Нет данных по платформам
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Recent Campaigns */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <CardTitle className="text-white">Последние кампании</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-white/5">
                                <tr>
                                    <th className="text-left p-4 text-gray-400 font-medium">ID</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Название</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Платформа</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Статус</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Дата создания</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {stats?.recent.map((campaign) => (
                                    <tr key={campaign.id} className="hover:bg-white/5">
                                        <td className="p-4 text-gray-300">{campaign.id}</td>
                                        <td className="p-4 text-white font-medium">{campaign.name}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${platformColors[campaign.platform] || 'from-gray-600 to-gray-400'} text-white`}>
                                                {campaign.platform}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <span className={`flex items-center gap-1 ${campaign.status === 'published'
                                                    ? 'text-green-400'
                                                    : 'text-yellow-400'
                                                }`}>
                                                {statusIcons[campaign.status] || <Activity className="h-4 w-4" />}
                                                {campaign.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-400">
                                            {campaign.created_at ? new Date(campaign.created_at).toLocaleString('ru-RU') : '-'}
                                        </td>
                                    </tr>
                                ))}
                                {(!stats?.recent || stats.recent.length === 0) && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-gray-500">
                                            Нет кампаний
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
