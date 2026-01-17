"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Loader2, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function AdminLoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async () => {
        if (!username || !password) {
            setError("Введите логин и пароль");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await fetch("/api/admin/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Ошибка авторизации");
            }

            const data = await response.json();
            localStorage.setItem("admin_token", data.token);
            toast.success("Добро пожаловать, Admin!");
            router.push("/adminskaya-panel");
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#1a0a0a] to-[#0f0f1a] flex items-center justify-center p-4">
            <Card className="w-full max-w-md bg-white/5 border-white/10 backdrop-blur-xl">
                <CardHeader className="text-center">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-r from-red-600 to-orange-600 flex items-center justify-center mx-auto mb-4">
                        <Shield className="h-10 w-10 text-white" />
                    </div>
                    <CardTitle className="text-2xl text-white">Admin Panel</CardTitle>
                    <p className="text-gray-400 text-sm mt-2">Доступ только для администратора</p>
                </CardHeader>

                <CardContent className="space-y-4">
                    {error && (
                        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        <Input
                            placeholder="Логин"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
                        />
                    </div>

                    <div className="space-y-2">
                        <Input
                            type="password"
                            placeholder="Пароль"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                            className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
                        />
                    </div>

                    <Button
                        onClick={handleLogin}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Вход...
                            </>
                        ) : (
                            <>
                                <Lock className="mr-2 h-4 w-4" />
                                Войти
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
