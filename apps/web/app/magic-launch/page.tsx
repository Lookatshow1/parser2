"use client";


import { MagicLaunchButton } from "@/components/magic/magic-launch-button";
import { Rocket, Target, Sparkles, DollarSign, ArrowRight, Clock, Zap } from "lucide-react";

export default function MagicLaunchPage() {
    return (
        <div className="max-w-5xl mx-auto">
            {/* Header */}
            <div className="text-center mb-10">
                <div className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/30 rounded-full px-4 py-2 mb-6">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <span className="text-violet-400 text-sm font-medium">Reklai AI</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-bold text-text mb-4">
                    Запуск рекламы
                </h1>

                <p className="text-lg text-muted max-w-xl mx-auto">
                    Введите URL или опишите бизнес — AI создаст и запустит рекламу на всех площадках за 60 секунд
                </p>
            </div>

            {/* Features row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                {[
                    { icon: Clock, label: "60 секунд", desc: "До запуска", color: "text-yellow-400" },
                    { icon: Target, label: "3 площадки", desc: "Яндекс, VK, Ozon", color: "text-blue-400" },
                    { icon: Sparkles, label: "AI-креативы", desc: "Тексты и картинки", color: "text-violet-400" },
                    { icon: DollarSign, label: "Авто-бюджет", desc: "Умное распределение", color: "text-green-400" }
                ].map((item, idx) => (
                    <div key={idx} className="bg-panel rounded-xl p-4 border border-border text-center">
                        <item.icon className={`w-6 h-6 mx-auto mb-2 ${item.color}`} />
                        <div className="font-medium text-text text-sm">{item.label}</div>
                        <div className="text-xs text-muted">{item.desc}</div>
                    </div>
                ))}
            </div>

            {/* Main Launch Component */}
            <MagicLaunchButton />

            {/* How it works */}
            <div className="mt-16">
                <h2 className="text-xl font-semibold text-text text-center mb-8">
                    Как это работает
                </h2>

                <div className="grid md:grid-cols-3 gap-6">
                    {[
                        {
                            step: "01",
                            title: "Вы даёте URL",
                            desc: "Или описываете бизнес в двух предложениях"
                        },
                        {
                            step: "02",
                            title: "AI создаёт рекламу",
                            desc: "Анализирует сайт, генерирует тексты и картинки"
                        },
                        {
                            step: "03",
                            title: "Запускает и ведёт",
                            desc: "На всех площадках, оптимизирует 24/7"
                        }
                    ].map((item, idx) => (
                        <div key={idx} className="relative">
                            <div className="text-5xl font-bold text-muted/10 mb-2">{item.step}</div>
                            <h3 className="text-lg font-semibold text-text mb-1">{item.title}</h3>
                            <p className="text-sm text-muted">{item.desc}</p>
                            {idx < 2 && (
                                <div className="hidden md:block absolute top-6 -right-3 text-muted/30">
                                    <ArrowRight className="w-6 h-6" />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* AI badge */}
            <div className="mt-12 pt-8 border-t border-border text-center">
                <p className="text-xs text-muted mb-3">Работает на</p>
                <div className="flex flex-wrap justify-center gap-4 text-sm text-muted/60">
                    <span>GPT-4</span>
                    <span>•</span>
                    <span>Claude</span>
                    <span>•</span>
                    <span>GigaChat</span>
                    <span>•</span>
                    <span>DALL-E</span>
                </div>
            </div>
        </div>
    );
}
