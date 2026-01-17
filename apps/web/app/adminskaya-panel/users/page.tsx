"use client";

import { useEffect, useState } from "react";
import {
    Users, Search, Ban, CheckCircle, Loader2,
    ChevronLeft, ChevronRight, Mail, Calendar
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface UserData {
    id: number;
    email: string;
    created_at: string;
    campaigns_count: number;
    total_spent: number;
    balance: number;
    is_active: boolean;
}

export default function AdminUsersPage() {
    const [users, setUsers] = useState<UserData[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(0);
    const limit = 20;

    useEffect(() => {
        loadUsers();
    }, [page]);

    const loadUsers = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch(`/api/admin/users?skip=${page * limit}&limit=${limit}`, {
                headers: { "X-Admin-Token": token || "" }
            });

            if (response.ok) {
                const data = await response.json();
                setUsers(data.items);
                setTotal(data.total);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const toggleUserActive = async (userId: number) => {
        try {
            const token = localStorage.getItem("admin_token");
            const response = await fetch(`/api/admin/users/${userId}/toggle-active`, {
                method: "POST",
                headers: { "X-Admin-Token": token || "" }
            });

            if (response.ok) {
                const data = await response.json();
                setUsers(users.map(u =>
                    u.id === userId ? { ...u, is_active: data.is_active } : u
                ));
                toast.success(data.is_active ? "Пользователь активирован" : "Пользователь заблокирован");
            }
        } catch (err) {
            toast.error("Ошибка");
        }
    };

    const filteredUsers = search
        ? users.filter(u => u.email.toLowerCase().includes(search.toLowerCase()))
        : users;

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Пользователи</h1>
                    <p className="text-gray-400 mt-1">Всего: {total}</p>
                </div>
            </div>

            {/* Search */}
            <Card className="bg-white/5 border-white/10">
                <CardContent className="p-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
                        <Input
                            placeholder="Поиск по email..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="pl-10 bg-black/30 border-white/10 text-white"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Users Table */}
            <Card className="bg-white/5 border-white/10">
                <CardContent className="p-0">
                    {loading ? (
                        <div className="flex items-center justify-center h-64">
                            <Loader2 className="h-8 w-8 text-red-500 animate-spin" />
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-white/5">
                                    <tr>
                                        <th className="text-left p-4 text-gray-400 font-medium">ID</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Email</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Дата регистрации</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Кампаний</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Баланс</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Статус</th>
                                        <th className="text-left p-4 text-gray-400 font-medium">Действия</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {filteredUsers.map((user) => (
                                        <tr key={user.id} className="hover:bg-white/5">
                                            <td className="p-4 text-gray-300">{user.id}</td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <Mail className="h-4 w-4 text-gray-500" />
                                                    <span className="text-white">{user.email}</span>
                                                </div>
                                            </td>
                                            <td className="p-4 text-gray-400">
                                                {user.created_at ? new Date(user.created_at).toLocaleDateString('ru-RU') : '-'}
                                            </td>
                                            <td className="p-4 text-gray-300">{user.campaigns_count}</td>
                                            <td className="p-4 text-gray-300">
                                                {user.balance.toLocaleString('ru-RU')} ₽
                                            </td>
                                            <td className="p-4">
                                                {user.is_active ? (
                                                    <span className="flex items-center gap-1 text-green-400">
                                                        <CheckCircle className="h-4 w-4" />
                                                        Активен
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-1 text-red-400">
                                                        <Ban className="h-4 w-4" />
                                                        Заблокирован
                                                    </span>
                                                )}
                                            </td>
                                            <td className="p-4">
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => toggleUserActive(user.id)}
                                                    className={user.is_active
                                                        ? "text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                                        : "text-green-400 hover:text-green-300 hover:bg-green-500/10"
                                                    }
                                                >
                                                    {user.is_active ? "Заблокировать" : "Активировать"}
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setPage(p => Math.max(0, p - 1))}
                        disabled={page === 0}
                        className="text-gray-400"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-gray-400">
                        Страница {page + 1} из {totalPages}
                    </span>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                        disabled={page >= totalPages - 1}
                        className="text-gray-400"
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    );
}
