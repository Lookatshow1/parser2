"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Check } from "lucide-react";

import { createCampaignWizard, uploadMedia } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { StepSettings } from "./step-settings";
import { StepAdGroup } from "./step-ad-group";
import { StepAds } from "./step-ads";
import { StepReview } from "./step-review";
import { cn } from "@/lib/utils";

const STEPS = [
    { id: "settings", title: "Настройки" },
    { id: "ad_group", title: "Группа объявлений" },
    { id: "ads", title: "Объявления" },
    { id: "review", title: "Проверка" }
];

export function CampaignWizard() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        name: "",
        platform: "yandex",
        objective: "",
        budget_daily: "",
        budget_total: "",
        start_date: "",
        end_date: "",
        // Ad Group
        group_name: "Основная группа",
        group_budget_daily: "",
        bid_strategy: "manual",
        keywords: "",
        regions: "",
        // Ads
        ads: [
            { id: 1, name: "Объявление 1", title: "", text: "", link: "", image_url: "" }
        ]
    });

    const handleNext = () => {
        if (currentStep < STEPS.length - 1) {
            setCurrentStep(curr => curr + 1);
        } else {
            handleSubmit();
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(curr => curr - 1);
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const payload = {
                name: formData.name,
                platform: formData.platform,
                objective: formData.objective || null,
                budget_total: formData.budget_total ? Number(formData.budget_total) : null,
                budget_daily: formData.budget_daily ? Number(formData.budget_daily) : null,
                start_date: formData.start_date || null,
                end_date: formData.end_date || null,
                ad_groups: [
                    {
                        name: formData.group_name,
                        budget_daily: formData.group_budget_daily ? Number(formData.group_budget_daily) : null,
                        bid_strategy: formData.bid_strategy,
                        targeting_json: {
                            keywords: formData.keywords ? formData.keywords.split("\n").filter(Boolean) : [],
                            regions: formData.regions ? formData.regions.split(",").filter(Boolean) : []
                        },
                        ads: formData.ads.map(ad => ({
                            name: ad.name,
                            title: ad.title || null,
                            text: ad.text || null,
                            landing_url: ad.link || null,
                            creative_json: {
                                image_url: ad.image_url || null
                            }
                        }))
                    }
                ]
            };

            const campaign = await createCampaignWizard(payload);
            toast.success("Кампания успешно создана!");
            router.push(`/campaigns/${campaign.id}`);
        } catch (e: any) {
            toast.error(e.message || "Ошибка создания кампании");
        } finally {
            setLoading(false);
        }
    };

    const updateForm = (updates: Partial<typeof formData>) => {
        setFormData(prev => ({ ...prev, ...updates }));
    };

    return (
        <div className="max-w-4xl mx-auto">
            {/* Steps Header */}
            <div className="flex items-center justify-between mb-8 px-4">
                {STEPS.map((step, idx) => (
                    <div key={step.id} className="flex items-center">
                        <div className={cn(
                            "flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors",
                            idx <= currentStep ? "bg-violet-600 text-white" : "bg-panel-strong text-muted"
                        )}>
                            {idx < currentStep ? <Check className="w-4 h-4" /> : idx + 1}
                        </div>
                        <span className={cn(
                            "ml-3 text-sm font-medium hidden sm:block",
                            idx <= currentStep ? "text-text" : "text-muted"
                        )}>
                            {step.title}
                        </span>
                        {idx < STEPS.length - 1 && (
                            <div className="mx-4 h-[2px] w-12 bg-border hidden sm:block" />
                        )}
                    </div>
                ))}
            </div>

            {/* Content */}
            <div className="bg-panel border border-border rounded-xl p-6 min-h-[400px] shadow-sm relative overflow-hidden">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.2 }}
                    >
                        {currentStep === 0 && <StepSettings data={formData} onChange={updateForm} />}
                        {currentStep === 1 && <StepAdGroup data={formData} onChange={updateForm} />}
                        {currentStep === 2 && <StepAds data={formData} onChange={updateForm} onUpload={uploadMedia} />}
                        {currentStep === 3 && <StepReview data={formData} />}
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Footer Navigation */}
            <div className="mt-6 flex justify-between">
                <Button
                    variant="ghost"
                    onClick={handleBack}
                    disabled={currentStep === 0 || loading}
                >
                    Назад
                </Button>
                <Button
                    onClick={handleNext}
                    disabled={loading}
                    className="bg-violet-600 hover:bg-violet-500 text-white min-w-[120px]"
                >
                    {loading ? "Создание..." : currentStep === STEPS.length - 1 ? "Запустить" : "Далее"}
                    {!loading && currentStep < STEPS.length - 1 && <ChevronRight className="w-4 h-4 ml-2" />}
                </Button>
            </div>
        </div>
    );
}
