"use client";

/**
 * Loading States
 * 
 * Consistent loading state components
 */

import { Loader2, Sparkles } from "lucide-react";
import { cn } from "../../lib/utils";

interface LoadingProps {
    size?: "sm" | "md" | "lg";
    text?: string;
    className?: string;
}

export function LoadingSpinner({ size = "md", className }: LoadingProps) {
    const sizeClasses = {
        sm: "h-4 w-4",
        md: "h-6 w-6",
        lg: "h-10 w-10",
    };

    return (
        <Loader2
            className={cn(
                "animate-spin text-violet-400",
                sizeClasses[size],
                className
            )}
        />
    );
}

export function LoadingPage({ text = "Загрузка..." }: LoadingProps) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
            <div className="relative">
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 blur-xl opacity-50 animate-pulse" />
                <div className="relative w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center">
                    <Sparkles className="h-8 w-8 text-white animate-pulse" />
                </div>
            </div>
            <p className="text-gray-400 animate-pulse">{text}</p>
        </div>
    );
}

export function LoadingButton({
    loading,
    children,
    loadingText = "Загрузка...",
    className,
}: {
    loading: boolean;
    children: React.ReactNode;
    loadingText?: string;
    className?: string;
}) {
    return (
        <span className={cn("inline-flex items-center gap-2", className)}>
            {loading ? (
                <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {loadingText}
                </>
            ) : (
                children
            )}
        </span>
    );
}

export function LoadingOverlay({
    visible,
    text = "Обработка...",
}: {
    visible: boolean;
    text?: string;
}) {
    if (!visible) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 flex flex-col items-center gap-4">
                <LoadingSpinner size="lg" />
                <p className="text-white font-medium">{text}</p>
            </div>
        </div>
    );
}

export function LoadingCard() {
    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-white/10 animate-pulse" />
                <div className="flex-1 space-y-2">
                    <div className="h-4 w-1/3 bg-white/10 rounded animate-pulse" />
                    <div className="h-3 w-1/2 bg-white/10 rounded animate-pulse" />
                </div>
            </div>
        </div>
    );
}

export function LoadingDots() {
    return (
        <span className="inline-flex gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "300ms" }} />
        </span>
    );
}
