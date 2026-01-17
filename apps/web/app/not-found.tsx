"use client";

/**
 * Custom 404 Page
 * 
 * Beautiful, on-brand 404 page with helpful navigation.
 */

import Link from "next/link";
import { Home, ArrowLeft, Search, Sparkles } from "lucide-react";
import { Button } from "../components/ui/button";

export default function NotFound() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#0f0f1a] to-[#1a0a20] flex items-center justify-center p-4">
            <div className="text-center max-w-lg">
                {/* Logo */}
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-violet-500/30">
                    <Sparkles className="h-10 w-10 text-white" />
                </div>

                {/* 404 */}
                <h1 className="text-8xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent mb-4">
                    404
                </h1>

                {/* Message */}
                <h2 className="text-2xl font-medium text-white mb-4">
                    Страница не найдена
                </h2>
                <p className="text-gray-400 mb-8 leading-relaxed">
                    К сожалению, запрашиваемая страница не существует или была перемещена.
                    Возможно, вы перешли по устаревшей ссылке.
                </p>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button
                        asChild
                        variant="default"
                        className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
                    >
                        <Link href="/">
                            <Home className="mr-2 h-4 w-4" />
                            На главную
                        </Link>
                    </Button>

                    <Button
                        asChild
                        variant="outline"
                        className="border-white/20 text-white hover:bg-white/10"
                    >
                        <Link href="/dashboard">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            В дашборд
                        </Link>
                    </Button>
                </div>

                {/* Helpful links */}
                <div className="mt-12 pt-8 border-t border-white/10">
                    <p className="text-sm text-gray-500 mb-4">Популярные разделы:</p>
                    <div className="flex flex-wrap gap-3 justify-center">
                        <Link
                            href="/magic"
                            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
                        >
                            Magic Create
                        </Link>
                        <span className="text-white/20">•</span>
                        <Link
                            href="/analytics"
                            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
                        >
                            Аналитика
                        </Link>
                        <span className="text-white/20">•</span>
                        <Link
                            href="/settings"
                            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
                        >
                            Настройки
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
