"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { MagicApi, MagicRun } from "@/lib/api";
import { Loader2, Sparkles, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { STR } from "@/lib/strings";
import Link from "next/link";

// --- Sub-components ---

function StepInput({ onStart, isLoading }: { onStart: (url: string) => void; isLoading: boolean }) {
    const [url, setUrl] = useState("https://");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (url) onStart(url);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-md mx-auto"
        >
            <Card className="glass-card border-none text-white">
                <CardHeader className="text-center">
                    <div className="mx-auto bg-accent/20 p-4 rounded-full w-fit mb-4">
                        <Sparkles className="w-8 h-8 text-accent animate-pulse" />
                    </div>
                    <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent to-accent-2">
                        {STR.magic.title}
                    </CardTitle>
                    <CardDescription className="text-gray-300">
                        {STR.magic.subtitle}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label>{STR.magic.inputLabel}</Label>
                            <Input
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder={STR.magic.inputPlaceholder}
                                className="bg-black/20 border-white/10 text-white placeholder:text-gray-500 h-12"
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full h-12 text-lg bg-accent hover:bg-accent/90 text-white font-semibold shadow-soft"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> {STR.magic.analyzing}</>
                            ) : (
                                <>{STR.magic.generateButton} <ArrowRight className="ml-2 h-5 w-5" /></>
                            )}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </motion.div>
    );
}

function StepProcessing() {
    return (
        <div className="text-center py-20">
            <div className="relative inline-block">
                <div className="absolute inset-0 bg-accent blur-3xl opacity-20 animate-pulse rounded-full"></div>
                <div className="relative bg-panel-strong p-8 rounded-full border border-white/5 animate-float">
                    <Sparkles className="w-16 h-16 text-accent" />
                </div>
            </div>
            <h3 className="mt-8 text-2xl font-bold text-white">{STR.magic.processing}</h3>
            <p className="mt-2 text-gray-400">{STR.magic.processingHint}</p>
        </div>
    );
}

function StepSuccess({ run, onReset }: { run: MagicRun; onReset: () => void }) {
    const result = run.result_json || {};
    const campaignName = result.campaign_name || "Новая кампания";
    const groupCount = result.ad_groups?.length || 0;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto"
        >
            <Card className="glass-card border-none">
                <CardHeader className="text-center pb-2">
                    <div className="mx-auto bg-green-500/20 p-3 rounded-full w-fit mb-4">
                        <CheckCircle2 className="w-8 h-8 text-green-400" />
                    </div>
                    <CardTitle className="text-2xl text-white">{STR.magic.successTitle}</CardTitle>
                    <CardDescription className="text-gray-300">
                        {STR.magic.successDesc}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="bg-black/30 rounded-xl p-6 border border-white/5">
                        <h4 className="text-lg font-semibold text-accent mb-2">{campaignName}</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
                            <div className="flex flex-col">
                                <span className="text-gray-500 mb-1">{STR.magic.adGroups}</span>
                                <span className="text-white text-lg font-medium">{groupCount}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-gray-500 mb-1">{STR.drafts.status}</span>
                                <span className="text-white text-lg font-medium capitalize">{run.status}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <Button variant="outline" className="flex-1 border-white/10 text-white hover:bg-white/5" onClick={onReset}>
                            {STR.magic.createAnother}
                        </Button>
                        <Link href="/drafts" className="flex-1">
                            <Button className="w-full bg-accent hover:bg-accent/90">
                                {STR.magic.viewDrafts} <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}

function StepError({ error, onReset }: { error: string; onReset: () => void }) {
    return (
        <div className="max-w-md mx-auto text-center">
            <Card className="bg-red-950/30 border-red-500/30">
                <CardHeader>
                    <div className="mx-auto bg-red-500/20 p-3 rounded-full w-fit mb-4">
                        <AlertCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <CardTitle className="text-red-400">{STR.magic.errorTitle}</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-red-200 mb-6">{error}</p>
                    <Button onClick={onReset} variant="outline" className="border-red-500/30 text-red-300 hover:bg-red-500/10">
                        {STR.magic.tryAgain}
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

// --- Main Wizard ---

export function MagicWizard() {
    const [step, setStep] = useState<'input' | 'processing' | 'success' | 'error'>('input');
    const [run, setRun] = useState<MagicRun | null>(null);
    const [error, setError] = useState<string>("");

    const startMagic = async (url: string) => {
        setStep('processing');
        try {
            const newRun = await MagicApi.createRun({ landing_url: url });
            setRun(newRun);

            // Poll for completion
            const interval = setInterval(async () => {
                try {
                    const updated = await MagicApi.getRun(newRun.id);
                    if (updated.status === 'success') {
                        setRun(updated);
                        setStep('success');
                        clearInterval(interval);
                    } else if (updated.status === 'failed') {
                        setError(updated.error || "Неизвестная ошибка");
                        setStep('error');
                        clearInterval(interval);
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1000);

        } catch (e: any) {
            setError(e.message || "Ошибка при создании кампании");
            setStep('error');
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6">
            <AnimatePresence mode="wait">
                {step === 'input' && (
                    <StepInput key="input" onStart={startMagic} isLoading={false} />
                )}
                {step === 'processing' && (
                    <motion.div
                        key="processing"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <StepProcessing />
                    </motion.div>
                )}
                {step === 'success' && run && (
                    <StepSuccess key="success" run={run} onReset={() => setStep('input')} />
                )}
                {step === 'error' && (
                    <StepError key="error" error={error} onReset={() => setStep('input')} />
                )}
            </AnimatePresence>
        </div>
    );
}
