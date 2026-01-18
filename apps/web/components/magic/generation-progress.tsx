"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, AlertCircle, Globe, Sparkles, Image, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";

interface GenerationStep {
    id: number;
    message: string;
    status: "pending" | "active" | "done" | "error";
}

interface GenerationProgressProps {
    isGenerating: boolean;
    onResult?: (data: any) => void;
    onError?: (message: string) => void;
    landingUrl?: string;
    description?: string;
}

const STEPS: GenerationStep[] = [
    { id: 1, message: "Анализируем сайт...", status: "pending" },
    { id: 2, message: "Генерируем тексты объявлений...", status: "pending" },
    { id: 3, message: "Создаём изображения...", status: "pending" },
    { id: 4, message: "Готово!", status: "pending" },
];

const STEP_ICONS = [Globe, Sparkles, Image, Rocket];

export function GenerationProgress({
    isGenerating,
    onResult,
    onError,
    landingUrl,
    description
}: GenerationProgressProps) {
    const [steps, setSteps] = useState<GenerationStep[]>(STEPS);
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState(0);
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        if (!isGenerating) {
            // Reset state
            setSteps(STEPS.map(s => ({ ...s, status: "pending" })));
            setProgress(0);
            setCurrentStep(0);
            return;
        }

        // Start SSE connection
        const startGeneration = async () => {
            try {
                const response = await fetch("/api/magic/generate-stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ landing_url: landingUrl, description })
                });

                const reader = response.body?.getReader();
                const decoder = new TextDecoder();

                if (!reader) return;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split("\n\n");

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                handleEvent(data);
                            } catch { }
                        }
                    }
                }
            } catch (err) {
                onError?.((err as Error).message);
            }
        };

        startGeneration();

        return () => {
            eventSourceRef.current?.close();
        };
    }, [isGenerating, landingUrl, description]);

    const handleEvent = (event: any) => {
        switch (event.type) {
            case "step":
                setCurrentStep(event.step);
                setSteps(prev => prev.map(s => ({
                    ...s,
                    status: s.id < event.step ? "done" : s.id === event.step ? "active" : "pending",
                    message: s.id === event.step ? event.message : s.message
                })));
                break;
            case "progress":
                setProgress(event.percent);
                break;
            case "result":
                setSteps(prev => prev.map(s => ({ ...s, status: "done" })));
                setProgress(100);
                onResult?.(event.data);
                break;
            case "error":
                setSteps(prev => prev.map(s =>
                    s.status === "active" ? { ...s, status: "error" } : s
                ));
                onError?.(event.message);
                break;
        }
    };

    if (!isGenerating && progress === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-panel/60 backdrop-blur-xl rounded-xl border border-white/10 p-6"
        >
            {/* Progress Bar */}
            <div className="mb-6">
                <div className="flex justify-between text-sm text-muted mb-2">
                    <span>Прогресс генерации</span>
                    <span>{progress}%</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-accent to-accent-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                    />
                </div>
            </div>

            {/* Steps */}
            <div className="space-y-3">
                {steps.map((step, idx) => {
                    const Icon = STEP_ICONS[idx];
                    return (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className={cn(
                                "flex items-center gap-3 p-3 rounded-lg transition-colors",
                                step.status === "active" && "bg-accent/10 border border-accent/30",
                                step.status === "done" && "opacity-60",
                                step.status === "error" && "bg-red-500/10 border border-red-500/30"
                            )}
                        >
                            <div className={cn(
                                "p-2 rounded-lg",
                                step.status === "active" && "bg-accent/20",
                                step.status === "done" && "bg-green-500/20",
                                step.status === "error" && "bg-red-500/20",
                                step.status === "pending" && "bg-white/5"
                            )}>
                                {step.status === "active" ? (
                                    <Loader2 className="h-5 w-5 text-accent animate-spin" />
                                ) : step.status === "done" ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                ) : step.status === "error" ? (
                                    <AlertCircle className="h-5 w-5 text-red-500" />
                                ) : (
                                    <Icon className="h-5 w-5 text-muted" />
                                )}
                            </div>
                            <span className={cn(
                                "text-sm",
                                step.status === "active" && "text-white font-medium",
                                step.status === "done" && "text-muted",
                                step.status === "error" && "text-red-400",
                                step.status === "pending" && "text-muted"
                            )}>
                                {step.message}
                            </span>
                        </motion.div>
                    );
                })}
            </div>
        </motion.div>
    );
}
