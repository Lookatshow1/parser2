"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle, Circle, ArrowRight, Sparkles, Link2, CreditCard, Megaphone } from "lucide-react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChecklistItem {
    id: string;
    title: string;
    description: string;
    href: string;
    icon: any;
    completed: boolean;
}

export function OnboardingChecklist() {
    const [items, setItems] = useState<ChecklistItem[]>([
        {
            id: "connection",
            title: "Подключите рекламный кабинет",
            description: "Яндекс.Директ, VK Ads или другой",
            href: "/connections",
            icon: Link2,
            completed: false,
        },
        {
            id: "campaign",
            title: "Создайте первую кампанию",
            description: "Или используйте Magic AI для генерации",
            href: "/magic",
            icon: Megaphone,
            completed: false,
        },
        {
            id: "billing",
            title: "Пополните баланс",
            description: "Для запуска рекламных кампаний",
            href: "/billing",
            icon: CreditCard,
            completed: false,
        },
    ]);

    useEffect(() => {
        checkProgress();
    }, []);

    const checkProgress = async () => {
        const token = localStorage.getItem("ads_access_token");
        if (!token) return;

        try {
            // Check connections
            const connRes = await fetch(`${API_BASE}/api/connections`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (connRes.ok) {
                const conns = await connRes.json();
                if (conns.items?.length > 0) {
                    setItems(prev => prev.map(item =>
                        item.id === "connection" ? { ...item, completed: true } : item
                    ));
                }
            }

            // Check campaigns
            const campRes = await fetch(`${API_BASE}/api/campaigns`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (campRes.ok) {
                const camps = await campRes.json();
                if (camps.items?.length > 0) {
                    setItems(prev => prev.map(item =>
                        item.id === "campaign" ? { ...item, completed: true } : item
                    ));
                }
            }

            // Check billing
            const billRes = await fetch(`${API_BASE}/api/billing/balance`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (billRes.ok) {
                const bill = await billRes.json();
                if (bill.balance > 0) {
                    setItems(prev => prev.map(item =>
                        item.id === "billing" ? { ...item, completed: true } : item
                    ));
                }
            }
        } catch (err) {
            console.error("Checklist error:", err);
        }
    };

    const completedCount = items.filter(i => i.completed).length;
    const progress = (completedCount / items.length) * 100;

    if (completedCount === items.length) {
        return null; // All done, hide checklist
    }

    return (
        <Card className="border-accent/30 bg-gradient-to-br from-accent/5 to-transparent">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-accent" />
                        Начало работы
                    </CardTitle>
                    <span className="text-sm text-muted">{completedCount}/{items.length}</span>
                </div>
                {/* Progress bar */}
                <div className="h-2 bg-panel-strong rounded-full overflow-hidden mt-2">
                    <div
                        className="h-full bg-accent transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {items.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.id}
                            href={item.href}
                            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${item.completed
                                    ? "bg-success/10 border border-success/20"
                                    : "bg-panel hover:bg-panel-strong border border-border"
                                }`}
                        >
                            <div className={`p-2 rounded-lg ${item.completed ? "bg-success/20" : "bg-panel-strong"}`}>
                                {item.completed ? (
                                    <CheckCircle className="h-5 w-5 text-success" />
                                ) : (
                                    <Icon className="h-5 w-5 text-muted" />
                                )}
                            </div>
                            <div className="flex-1">
                                <div className={`font-medium ${item.completed ? "text-success" : "text-text"}`}>
                                    {item.title}
                                </div>
                                <div className="text-xs text-muted">{item.description}</div>
                            </div>
                            {!item.completed && (
                                <ArrowRight className="h-4 w-4 text-muted" />
                            )}
                        </Link>
                    );
                })}
            </CardContent>
        </Card>
    );
}
