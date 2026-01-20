"use client";

import { ReactNode, useState } from "react";
import { HelpCircle } from "lucide-react";

// Metric definitions with explanations and tips
export const METRIC_DEFINITIONS: Record<string, {
    name: string;
    description: string;
    formula?: string;
    goodRange?: string;
    tip?: string;
}> = {
    // Cost metrics
    spend: {
        name: "Расходы",
        description: "Общая сумма потраченных средств на рекламу.",
        tip: "Следите за ROI — расходы должны окупаться конверсиями."
    },
    cpc: {
        name: "CPC (Cost Per Click)",
        description: "Стоимость одного клика по объявлению.",
        formula: "CPC = Расходы / Клики",
        goodRange: "В зависимости от ниши: от 5₽ до 100₽",
        tip: "Снижайте CPC улучшая CTR и качество объявлений."
    },
    cpm: {
        name: "CPM (Cost Per Mille)",
        description: "Стоимость 1000 показов объявления.",
        formula: "CPM = (Расходы / Показы) × 1000",
        goodRange: "50₽ – 500₽ в зависимости от аудитории",
        tip: "Высокий CPM может говорить о узкой или конкурентной аудитории."
    },
    cpa: {
        name: "CPA (Cost Per Action)",
        description: "Стоимость одной целевой конверсии.",
        formula: "CPA = Расходы / Конверсии",
        goodRange: "Зависит от маржинальности продукта",
        tip: "Главный показатель эффективности. Сравнивайте с LTV клиента."
    },

    // Engagement metrics
    impressions: {
        name: "Показы",
        description: "Сколько раз объявление было показано пользователям.",
        tip: "Больше показов = больше охват, но следите за частотой."
    },
    clicks: {
        name: "Клики",
        description: "Сколько раз пользователи кликнули по объявлению.",
        tip: "Качественные клики важнее количества."
    },
    ctr: {
        name: "CTR (Click-Through Rate)",
        description: "Процент пользователей, кликнувших по объявлению.",
        formula: "CTR = (Клики / Показы) × 100%",
        goodRange: "1% – 5% для поиска, 0.5% – 2% для РСЯ/КМС",
        tip: "Низкий CTR? Улучшите заголовки и креативы."
    },

    // Conversion metrics
    conversions: {
        name: "Конверсии",
        description: "Количество целевых действий (покупки, заявки, звонки).",
        tip: "Настройте правильные цели в Метрике/Analytics."
    },
    cr: {
        name: "CR (Conversion Rate)",
        description: "Процент кликов, которые привели к конверсии.",
        formula: "CR = (Конверсии / Клики) × 100%",
        goodRange: "1% – 10% в зависимости от типа конверсии",
        tip: "Низкая конверсия? Проверьте лендинг и оффер."
    },
    roas: {
        name: "ROAS (Return on Ad Spend)",
        description: "Возврат на инвестиции в рекламу.",
        formula: "ROAS = Доход / Расходы × 100%",
        goodRange: "> 300% для прибыльности",
        tip: "ROAS < 100% означает убыток. Оптимизируйте кампании."
    },
};

interface MetricTooltipProps {
    metric: keyof typeof METRIC_DEFINITIONS;
    children?: ReactNode;
    className?: string;
}

export function MetricTooltip({ metric, children, className = "" }: MetricTooltipProps) {
    const [isOpen, setIsOpen] = useState(false);
    const def = METRIC_DEFINITIONS[metric];

    if (!def) return <>{children}</>;

    return (
        <span className={`relative inline-flex items-center gap-1 ${className}`}>
            {children}
            <button
                type="button"
                className="text-muted hover:text-accent transition-colors"
                onMouseEnter={() => setIsOpen(true)}
                onMouseLeave={() => setIsOpen(false)}
                onClick={() => setIsOpen(!isOpen)}
                aria-label={`Подробнее о ${def.name}`}
            >
                <HelpCircle className="h-3.5 w-3.5" />
            </button>

            {isOpen && (
                <div className="absolute z-50 left-0 top-full mt-2 w-72 p-3 rounded-lg bg-panel border border-border shadow-xl animate-in fade-in-0 zoom-in-95">
                    <div className="font-semibold text-text mb-1">{def.name}</div>
                    <p className="text-sm text-muted mb-2">{def.description}</p>

                    {def.formula && (
                        <div className="text-xs bg-background/50 rounded px-2 py-1 font-mono mb-2">
                            {def.formula}
                        </div>
                    )}

                    {def.goodRange && (
                        <div className="text-xs text-muted mb-1">
                            <span className="text-success">✓ Хороший диапазон:</span> {def.goodRange}
                        </div>
                    )}

                    {def.tip && (
                        <div className="text-xs text-accent mt-2 pt-2 border-t border-border/50">
                            💡 {def.tip}
                        </div>
                    )}
                </div>
            )}
        </span>
    );
}

// Shorthand for inline metric name with tooltip
export function MetricLabel({ metric, className = "" }: { metric: keyof typeof METRIC_DEFINITIONS; className?: string }) {
    const def = METRIC_DEFINITIONS[metric];
    if (!def) return null;

    return (
        <MetricTooltip metric={metric} className={className}>
            <span>{def.name}</span>
        </MetricTooltip>
    );
}
