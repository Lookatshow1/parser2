"use client";

import { ReactNode } from "react";
import Link from "next/link";
import {
    Sparkles,
    TrendingUp,
    LayoutGrid,
    Target,
    ArrowRight,
    type LucideIcon
} from "lucide-react";
import { Card } from "@/components/ui/card";

interface QuickAction {
    id: string;
    title: string;
    description: string;
    icon: LucideIcon;
    href?: string;
    onClick?: () => void;
    variant?: "default" | "primary" | "success";
    badge?: string;
}

const defaultActions: QuickAction[] = [
    {
        id: "magic",
        title: "Магия AI",
        description: "Создать объявления",
        icon: Sparkles,
        href: "/magic",
        variant: "primary"
    },
    {
        id: "campaigns",
        title: "Кампании",
        description: "Создание и запуск",
        icon: LayoutGrid,
        href: "/campaigns"
    },
    {
        id: "competitors",
        title: "Конкуренты",
        description: "Анализ рынка",
        icon: Target,
        href: "/competitors"
    },
    {
        id: "analytics",
        title: "Аналитика",
        description: "Подробные отчёты",
        icon: TrendingUp,
        href: "/analytics"
    }
];

interface QuickActionsProps {
    actions?: QuickAction[];
    className?: string;
}

export function QuickActions({ actions = defaultActions, className = "" }: QuickActionsProps) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-4 gap-3 ${className}`}>
            {actions.map((action) => {
                const Icon = action.icon;
                const content = (
                    <Card
                        className={`
                            relative p-4 cursor-pointer transition-all duration-200
                            hover:scale-[1.02] hover:shadow-lg
                            ${action.variant === "primary" ? "bg-accent/10 border-accent/30 hover:bg-accent/20" : ""}
                            ${action.variant === "success" ? "bg-success/10 border-success/30 hover:bg-success/20" : ""}
                        `}
                    >
                        <div className="flex items-start gap-3">
                            <div className={`
                                p-2 rounded-lg
                                ${action.variant === "primary" ? "bg-accent/20 text-accent" : ""}
                                ${action.variant === "success" ? "bg-success/20 text-success" : ""}
                                ${!action.variant ? "bg-white/5 text-muted" : ""}
                            `}>
                                <Icon className="h-5 w-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="font-medium text-text text-sm truncate">
                                    {action.title}
                                </div>
                                <div className="text-xs text-muted truncate">
                                    {action.description}
                                </div>
                            </div>
                            {action.badge && (
                                <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-accent text-white">
                                    {action.badge}
                                </span>
                            )}
                        </div>
                    </Card>
                );

                if (action.href) {
                    return (
                        <Link key={action.id} href={action.href}>
                            {content}
                        </Link>
                    );
                }

                return (
                    <button key={action.id} onClick={action.onClick} className="text-left">
                        {content}
                    </button>
                );
            })}
        </div>
    );
}

// Compact inline quick action button
export function QuickActionButton({
    icon: Icon,
    label,
    href,
    onClick,
    variant = "default"
}: {
    icon: LucideIcon;
    label: string;
    href?: string;
    onClick?: () => void;
    variant?: "default" | "primary";
}) {
    const classes = `
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
        transition-all duration-200 cursor-pointer
        ${variant === "primary"
            ? "bg-accent text-white hover:bg-accent/90"
            : "bg-white/5 text-muted hover:bg-white/10 hover:text-text"
        }
    `;

    const content = (
        <>
            <Icon className="h-4 w-4" />
            <span>{label}</span>
            <ArrowRight className="h-3 w-3" />
        </>
    );

    if (href) {
        return <Link href={href} className={classes}>{content}</Link>;
    }

    return <button onClick={onClick} className={classes}>{content}</button>;
}
