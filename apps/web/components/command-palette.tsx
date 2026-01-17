"use client";

/**
 * Command Palette (⌘K)
 * 
 * Spotlight-style command palette for power users.
 * Quick navigation, actions, and AI commands.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Search, Sparkles, LayoutDashboard, BarChart3, FileText,
    Settings, CreditCard, Zap, PlusCircle, TrendingUp,
    Users, Activity, Megaphone, ArrowRight, Command
} from "lucide-react";

interface CommandItem {
    id: string;
    title: string;
    description?: string;
    icon: React.ReactNode;
    action: () => void;
    category: "navigation" | "action" | "ai" | "recent";
    keywords?: string[];
}

export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();

    // Navigation items
    const navigationItems: CommandItem[] = [
        {
            id: "dashboard",
            title: "Dashboard",
            description: "Обзор метрик и KPI",
            icon: <LayoutDashboard className="h-4 w-4" />,
            action: () => router.push("/dashboard"),
            category: "navigation",
            keywords: ["home", "главная", "обзор"],
        },
        {
            id: "analytics",
            title: "Аналитика",
            description: "Графики и отчёты",
            icon: <BarChart3 className="h-4 w-4" />,
            action: () => router.push("/analytics"),
            category: "navigation",
            keywords: ["charts", "графики", "отчёты"],
        },
        {
            id: "magic",
            title: "Magic Create",
            description: "AI-генерация креативов",
            icon: <Sparkles className="h-4 w-4" />,
            action: () => router.push("/magic"),
            category: "navigation",
            keywords: ["ai", "создать", "генерация"],
        },
        {
            id: "drafts",
            title: "Черновики",
            description: "Неопубликованные кампании",
            icon: <FileText className="h-4 w-4" />,
            action: () => router.push("/drafts"),
            category: "navigation",
        },
        {
            id: "campaigns",
            title: "Кампании",
            description: "Активные рекламные кампании",
            icon: <Megaphone className="h-4 w-4" />,
            action: () => router.push("/campaigns"),
            category: "navigation",
        },
        {
            id: "ab-tests",
            title: "A/B Тесты",
            description: "Эксперименты с креативами",
            icon: <Activity className="h-4 w-4" />,
            action: () => router.push("/ab-tests"),
            category: "navigation",
        },
        {
            id: "budget-optimizer",
            title: "Оптимизатор бюджета",
            description: "AI-распределение бюджета",
            icon: <TrendingUp className="h-4 w-4" />,
            action: () => router.push("/budget-optimizer"),
            category: "navigation",
        },
        {
            id: "billing",
            title: "Биллинг",
            description: "Баланс и транзакции",
            icon: <CreditCard className="h-4 w-4" />,
            action: () => router.push("/billing"),
            category: "navigation",
        },
        {
            id: "settings",
            title: "Настройки",
            description: "Профиль и конфигурация",
            icon: <Settings className="h-4 w-4" />,
            action: () => router.push("/settings"),
            category: "navigation",
        },
    ];

    // Action items
    const actionItems: CommandItem[] = [
        {
            id: "new-campaign",
            title: "Создать кампанию",
            description: "Новая рекламная кампания",
            icon: <PlusCircle className="h-4 w-4" />,
            action: () => router.push("/magic"),
            category: "action",
            keywords: ["new", "create", "новая"],
        },
        {
            id: "quick-optimize",
            title: "Быстрая оптимизация",
            description: "Оптимизировать все кампании",
            icon: <Zap className="h-4 w-4" />,
            action: () => router.push("/budget-optimizer?auto=true"),
            category: "action",
        },
    ];

    // AI commands (special prefix handling)
    const aiItems: CommandItem[] = [
        {
            id: "ai-creative",
            title: "AI: Сгенерировать креативы",
            description: "Создать рекламу с помощью AI",
            icon: <Sparkles className="h-4 w-4 text-violet-400" />,
            action: () => router.push("/magic"),
            category: "ai",
        },
        {
            id: "ai-analyze",
            title: "AI: Анализ конкурентов",
            description: "Изучить рекламу конкурентов",
            icon: <Users className="h-4 w-4 text-violet-400" />,
            action: () => alert("Coming soon!"),
            category: "ai",
        },
    ];

    const allItems = [...navigationItems, ...actionItems, ...aiItems];

    // Filter items based on query
    const filteredItems = query
        ? allItems.filter((item) => {
            const searchText = `${item.title} ${item.description} ${item.keywords?.join(" ")}`.toLowerCase();
            return searchText.includes(query.toLowerCase());
        })
        : allItems;

    // Group by category
    const groupedItems = {
        navigation: filteredItems.filter((i) => i.category === "navigation"),
        action: filteredItems.filter((i) => i.category === "action"),
        ai: filteredItems.filter((i) => i.category === "ai"),
    };

    // Keyboard shortcut to open
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                setOpen(true);
            }
            if (e.key === "Escape") {
                setOpen(false);
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, []);

    // Focus input when opened
    useEffect(() => {
        if (open && inputRef.current) {
            inputRef.current.focus();
        }
    }, [open]);

    // Navigate with arrow keys
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!open) return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelectedIndex((i) => Math.min(i + 1, filteredItems.length - 1));
            }
            if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelectedIndex((i) => Math.max(i - 1, 0));
            }
            if (e.key === "Enter" && filteredItems[selectedIndex]) {
                e.preventDefault();
                executeItem(filteredItems[selectedIndex]);
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [open, selectedIndex, filteredItems]);

    // Reset selection when query changes
    useEffect(() => {
        setSelectedIndex(0);
    }, [query]);

    const executeItem = (item: CommandItem) => {
        setOpen(false);
        setQuery("");
        item.action();
    };

    if (!open) {
        return (
            <button
                onClick={() => setOpen(true)}
                className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 text-white/60 hover:text-white hover:bg-white/20 transition-all shadow-lg"
            >
                <Command className="h-4 w-4" />
                <span className="text-sm">⌘K</span>
            </button>
        );
    }

    return (
        <div
            className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
            onClick={() => setOpen(false)}
        >
            <div
                className="w-full max-w-xl bg-[#1a1a2e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
                    <Search className="h-5 w-5 text-white/40" />
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Поиск команд, страниц..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="flex-1 bg-transparent text-white placeholder:text-white/40 outline-none text-lg"
                    />
                    <kbd className="px-2 py-1 text-xs text-white/40 bg-white/5 rounded border border-white/10">
                        ESC
                    </kbd>
                </div>

                {/* Results */}
                <div className="max-h-[60vh] overflow-y-auto p-2">
                    {filteredItems.length === 0 ? (
                        <div className="py-8 text-center text-white/40">
                            <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p>Ничего не найдено</p>
                            <p className="text-sm mt-1">Попробуйте другой запрос</p>
                        </div>
                    ) : (
                        <>
                            {/* Navigation */}
                            {groupedItems.navigation.length > 0 && (
                                <div className="mb-2">
                                    <div className="px-3 py-2 text-xs text-white/40 uppercase tracking-wider">
                                        Навигация
                                    </div>
                                    {groupedItems.navigation.map((item) => (
                                        <CommandItemRow
                                            key={item.id}
                                            item={item}
                                            isSelected={filteredItems[selectedIndex]?.id === item.id}
                                            onSelect={() => executeItem(item)}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* Actions */}
                            {groupedItems.action.length > 0 && (
                                <div className="mb-2">
                                    <div className="px-3 py-2 text-xs text-white/40 uppercase tracking-wider">
                                        Действия
                                    </div>
                                    {groupedItems.action.map((item) => (
                                        <CommandItemRow
                                            key={item.id}
                                            item={item}
                                            isSelected={filteredItems[selectedIndex]?.id === item.id}
                                            onSelect={() => executeItem(item)}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* AI */}
                            {groupedItems.ai.length > 0 && (
                                <div className="mb-2">
                                    <div className="px-3 py-2 text-xs text-violet-400 uppercase tracking-wider flex items-center gap-1">
                                        <Sparkles className="h-3 w-3" />
                                        AI Команды
                                    </div>
                                    {groupedItems.ai.map((item) => (
                                        <CommandItemRow
                                            key={item.id}
                                            item={item}
                                            isSelected={filteredItems[selectedIndex]?.id === item.id}
                                            onSelect={() => executeItem(item)}
                                        />
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-white/10 flex items-center justify-between text-xs text-white/40">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↑</kbd>
                            <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↓</kbd>
                            навигация
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↵</kbd>
                            выбрать
                        </span>
                    </div>
                    <span className="text-violet-400">Effecto</span>
                </div>
            </div>
        </div>
    );
}

function CommandItemRow({
    item,
    isSelected,
    onSelect,
}: {
    item: CommandItem;
    isSelected: boolean;
    onSelect: () => void;
}) {
    return (
        <button
            onClick={onSelect}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${isSelected ? "bg-violet-500/20 text-white" : "text-white/70 hover:bg-white/5"
                }`}
        >
            <div className={`p-2 rounded-lg ${isSelected ? "bg-violet-500/30" : "bg-white/5"}`}>
                {item.icon}
            </div>
            <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{item.title}</div>
                {item.description && (
                    <div className="text-sm text-white/40 truncate">{item.description}</div>
                )}
            </div>
            <ArrowRight className={`h-4 w-4 ${isSelected ? "opacity-100" : "opacity-0"}`} />
        </button>
    );
}
