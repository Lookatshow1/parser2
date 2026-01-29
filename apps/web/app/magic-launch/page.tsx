"use client";

import { AppShell } from "@/components/app-shell";
import { MagicLaunchButton } from "@/components/magic/magic-launch-button";
import { PageHeader } from "@/components/ui/page-header";
import { Rocket, Zap, Target, DollarSign, Sparkles, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";

export default function MagicLaunchPage() {
    return (
        <AppShell>
            <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900">
                {/* Hero Section */}
                <div className="relative overflow-hidden">
                    {/* Background effects */}
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-yellow-500/10 via-transparent to-transparent"></div>
                    <div className="absolute top-20 left-1/4 w-72 h-72 bg-yellow-500/20 rounded-full blur-3xl animate-pulse"></div>
                    <div className="absolute top-40 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>

                    <div className="relative z-10 max-w-7xl mx-auto px-4 py-12">
                        {/* Header */}
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-center mb-8"
                        >
                            <div className="inline-flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/20 rounded-full px-4 py-2 mb-6">
                                <Sparkles className="w-4 h-4 text-yellow-400" />
                                <span className="text-yellow-400 text-sm font-medium">
                                    Новая функция
                                </span>
                            </div>

                            <h1 className="text-5xl md:text-7xl font-black mb-4">
                                <span className="bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500">
                                    MAGIC LAUNCH
                                </span>
                            </h1>

                            <p className="text-xl md:text-2xl text-gray-300 max-w-2xl mx-auto">
                                Кнопка &laquo;БАБЛО&raquo; - один клик и ваша реклама работает на всех площадках
                            </p>
                        </motion.div>

                        {/* Features */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12"
                        >
                            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 text-center border border-white/10">
                                <Rocket className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                                <div className="text-white font-medium">Мгновенный запуск</div>
                                <div className="text-xs text-gray-400">За 30 секунд</div>
                            </div>
                            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 text-center border border-white/10">
                                <Target className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                                <div className="text-white font-medium">3 площадки</div>
                                <div className="text-xs text-gray-400">Яндекс, VK, Ozon</div>
                            </div>
                            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 text-center border border-white/10">
                                <Sparkles className="w-8 h-8 mx-auto mb-2 text-purple-400" />
                                <div className="text-white font-medium">AI-креативы</div>
                                <div className="text-xs text-gray-400">GPT-4, Claude, DALL-E</div>
                            </div>
                            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 text-center border border-white/10">
                                <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-400" />
                                <div className="text-white font-medium">Умный бюджет</div>
                                <div className="text-xs text-gray-400">Автораспределение</div>
                            </div>
                        </motion.div>

                        {/* Main Launch Component */}
                        <MagicLaunchButton />

                        {/* How it works */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="mt-16 max-w-4xl mx-auto"
                        >
                            <h2 className="text-2xl font-bold text-white text-center mb-8">
                                Как это работает
                            </h2>

                            <div className="grid md:grid-cols-4 gap-6">
                                {[
                                    {
                                        step: 1,
                                        title: "Введите URL",
                                        desc: "Или опишите ваш бизнес в двух словах",
                                        icon: "🌐"
                                    },
                                    {
                                        step: 2,
                                        title: "AI анализирует",
                                        desc: "GPT-4 изучает ваш сайт и конкурентов",
                                        icon: "🤖"
                                    },
                                    {
                                        step: 3,
                                        title: "Создаёт рекламу",
                                        desc: "Тексты, картинки, видео - всё автоматически",
                                        icon: "✨"
                                    },
                                    {
                                        step: 4,
                                        title: "Запускает",
                                        desc: "На Яндекс, VK и Ozon одновременно",
                                        icon: "🚀"
                                    }
                                ].map((item, i) => (
                                    <div key={i} className="relative">
                                        <div className="bg-white/5 rounded-xl p-6 border border-white/10 h-full">
                                            <div className="text-4xl mb-4">{item.icon}</div>
                                            <div className="text-sm text-gray-400 mb-1">
                                                Шаг {item.step}
                                            </div>
                                            <div className="text-lg font-semibold text-white mb-2">
                                                {item.title}
                                            </div>
                                            <div className="text-sm text-gray-400">
                                                {item.desc}
                                            </div>
                                        </div>
                                        {i < 3 && (
                                            <div className="hidden md:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
                                                <ArrowRight className="w-6 h-6 text-gray-600" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        {/* AI Providers */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.7 }}
                            className="mt-16 text-center"
                        >
                            <p className="text-sm text-gray-500 mb-4">
                                Используем лучшие AI-модели
                            </p>
                            <div className="flex flex-wrap justify-center gap-6 opacity-50">
                                <span className="text-white font-medium">OpenAI GPT-4</span>
                                <span className="text-gray-500">|</span>
                                <span className="text-white font-medium">Claude</span>
                                <span className="text-gray-500">|</span>
                                <span className="text-white font-medium">GigaChat</span>
                                <span className="text-gray-500">|</span>
                                <span className="text-white font-medium">DALL-E 3</span>
                                <span className="text-gray-500">|</span>
                                <span className="text-white font-medium">ElevenLabs</span>
                                <span className="text-gray-500">|</span>
                                <span className="text-white font-medium">HeyGen</span>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
