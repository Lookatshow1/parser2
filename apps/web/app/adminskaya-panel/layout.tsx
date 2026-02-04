"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
    Shield, Users, Settings, BarChart3, CreditCard,
    LogOut, Menu, Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface AdminLayoutProps {
    children: React.ReactNode;
}

const navItems = [
    { href: "/adminskaya-panel", icon: BarChart3, label: "Обзор" },
    { href: "/adminskaya-panel/users", icon: Users, label: "Пользователи" },
    { href: "/adminskaya-panel/campaigns", icon: Activity, label: "Кампании" },
    { href: "/adminskaya-panel/finances", icon: CreditCard, label: "Финансы" },
    { href: "/adminskaya-panel/settings", icon: Settings, label: "Настройки" },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [checking, setChecking] = useState(true);

    // If this is the login page, render children directly without auth check
    const isLoginPage = pathname === "/adminskaya-panel/login";

    useEffect(() => {
        if (isLoginPage) {
            setChecking(false);
            return;
        }

        const token = localStorage.getItem("admin_token");
        if (!token) {
            router.push("/adminskaya-panel/login");
        } else {
            setIsAuthenticated(true);
        }
        setChecking(false);
    }, [router, isLoginPage]);

    // For login page, render children directly
    if (isLoginPage) {
        return <>{children}</>;
    }

    const handleLogout = () => {
        localStorage.removeItem("admin_token");
        router.push("/adminskaya-panel/login");
    };

    if (checking) {
        return (
            <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
                <div className="text-white">Загрузка...</div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="min-h-screen bg-[#0a0a0f] flex">
            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/60 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                fixed lg:static inset-y-0 left-0 z-50
                w-64 bg-[#0f0f1a] border-r border-white/5
                transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
                transition-transform duration-200 ease-in-out
            `}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="p-6 border-b border-white/5">
                        <Link href="/adminskaya-panel" className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-red-600 to-orange-600 flex items-center justify-center">
                                <Shield className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <div className="font-bold text-white">Admin Panel</div>
                                <div className="text-xs text-gray-500">Reklai</div>
                            </div>
                        </Link>
                    </div>

                    {/* Nav */}
                    <nav className="flex-1 p-4 space-y-1">
                        {navItems.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                            >
                                <item.icon className="h-5 w-5" />
                                {item.label}
                            </Link>
                        ))}
                    </nav>

                    {/* Footer */}
                    <div className="p-4 border-t border-white/5">
                        <Button
                            variant="ghost"
                            className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            onClick={handleLogout}
                        >
                            <LogOut className="h-5 w-5 mr-3" />
                            Выйти
                        </Button>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 min-h-screen">
                {/* Mobile header */}
                <header className="lg:hidden sticky top-0 z-30 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5 p-4">
                    <div className="flex items-center justify-between">
                        <button onClick={() => setSidebarOpen(true)}>
                            <Menu className="h-6 w-6 text-white" />
                        </button>
                        <div className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-red-500" />
                            <span className="font-bold text-white">Admin</span>
                        </div>
                        <div className="w-6" />
                    </div>
                </header>

                {/* Page content */}
                <div className="p-6 lg:p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
