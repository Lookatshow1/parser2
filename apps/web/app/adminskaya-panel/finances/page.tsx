"use client";

import { useEffect, useState } from "react";
import {
    CreditCard, TrendingUp, ArrowUpRight, ArrowDownRight,
    Loader2, Calendar, DollarSign
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Transaction {
    id: number;
    organization_id: number;
    type: string;
    amount: number;
    status: string;
    description: string;
    created_at: string;
}

interface FinancesData {
    items: Transaction[];
    total: number;
    total_topup: number;
}

export default function AdminFinancesPage() {
    const [data, setData] = useState<FinancesData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadTransactions();
    }, []);

    const loadTransactions = async () => {
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch("/api/admin/transactions?limit=100", {
                headers: { "X-Admin-Token": token || "" }
            });

            if (response.ok) {
                const result = await response.json();
                setData(result);
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

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Финансы</h1>
                <p className="text-gray-400 mt-1">Транзакции и балансы</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border-green-500/20">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-green-300">Всего пополнений</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {(data?.total_topup || 0).toLocaleString('ru-RU')} ₽
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-green-500/20">
                                <TrendingUp className="h-6 w-6 text-green-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Всего транзакций</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {data?.total || 0}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-blue-500/20">
                                <CreditCard className="h-6 w-6 text-blue-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm text-gray-400">Средняя сумма</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {data && data.total > 0
                                        ? Math.round(data.total_topup / data.total).toLocaleString('ru-RU')
                                        : 0} ₽
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-violet-500/20">
                                <DollarSign className="h-6 w-6 text-violet-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Transactions Table */}
            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <CardTitle className="text-white">Последние транзакции</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-white/5">
                                <tr>
                                    <th className="text-left p-4 text-gray-400 font-medium">ID</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Тип</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Сумма</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Статус</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Описание</th>
                                    <th className="text-left p-4 text-gray-400 font-medium">Дата</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {data?.items.map((tx) => (
                                    <tr key={tx.id} className="hover:bg-white/5">
                                        <td className="p-4 text-gray-300">{tx.id}</td>
                                        <td className="p-4">
                                            <span className={`flex items-center gap-1 ${tx.type === 'topup' ? 'text-green-400' : 'text-orange-400'
                                                }`}>
                                                {tx.type === 'topup' ? (
                                                    <ArrowUpRight className="h-4 w-4" />
                                                ) : (
                                                    <ArrowDownRight className="h-4 w-4" />
                                                )}
                                                {tx.type === 'topup' ? 'Пополнение' : 'Расход'}
                                            </span>
                                        </td>
                                        <td className={`p-4 font-medium ${tx.type === 'topup' ? 'text-green-400' : 'text-white'
                                            }`}>
                                            {tx.type === 'topup' ? '+' : '-'}{Math.abs(tx.amount).toLocaleString('ru-RU')} ₽
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs ${tx.status === 'completed'
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : tx.status === 'pending'
                                                        ? 'bg-yellow-500/20 text-yellow-400'
                                                        : 'bg-gray-500/20 text-gray-400'
                                                }`}>
                                                {tx.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-400 max-w-xs truncate">
                                            {tx.description || '-'}
                                        </td>
                                        <td className="p-4 text-gray-400">
                                            {tx.created_at ? new Date(tx.created_at).toLocaleString('ru-RU') : '-'}
                                        </td>
                                    </tr>
                                ))}
                                {(!data?.items || data.items.length === 0) && (
                                    <tr>
                                        <td colSpan={6} className="p-8 text-center text-gray-500">
                                            Нет транзакций
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
