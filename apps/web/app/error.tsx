"use client";

/**
 * Global Error Page (500)
 * 
 * Handles unexpected errors gracefully.
 */

import { useEffect } from "react";
import Link from "next/link";
import { RefreshCw, Home, AlertTriangle, Sparkles } from "lucide-react";
import { Button } from "../components/ui/button";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log error to console (in production, send to Sentry)
        console.error("Application error:", error);
    }, [error]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#0f0f1a] to-[#1a0a20] flex items-center justify-center p-4">
            <div className="text-center max-w-lg">
                {/* Logo */}
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-r from-red-600 to-orange-600 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-red-500/30">
                    <AlertTriangle className="h-10 w-10 text-white" />
                </div>

                {/* Error */}
                <h1 className="text-4xl font-bold text-white mb-4">
                    Что-то пошло не так
                </h1>

                {/* Message */}
                <p className="text-gray-400 mb-6 leading-relaxed">
                    Произошла непредвиденная ошибка. Наша команда уже уведомлена
                    и работает над исправлением.
                </p>

                {/* Error digest */}
                {error.digest && (
                    <div className="bg-white/5 rounded-lg px-4 py-2 mb-8 inline-block">
                        <code className="text-xs text-gray-500">
                            Код ошибки: {error.digest}
                        </code>
                    </div>
                )}

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button
                        onClick={reset}
                        variant="default"
                        className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
                    >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Попробовать снова
                    </Button>

                    <Button
                        asChild
                        variant="outline"
                        className="border-white/20 text-white hover:bg-white/10"
                    >
                        <Link href="/">
                            <Home className="mr-2 h-4 w-4" />
                            На главную
                        </Link>
                    </Button>
                </div>

                {/* Support */}
                <div className="mt-12 pt-8 border-t border-white/10">
                    <p className="text-sm text-gray-500">
                        Если проблема повторяется, напишите в поддержку:{" "}
                        <a
                            href="mailto:support@reklai.ai"
                            className="text-violet-400 hover:text-violet-300"
                        >
                            support@reklai.ai
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}
