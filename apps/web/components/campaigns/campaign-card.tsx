"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    Play, Pause, MousePointer2, Eye, Banknote, Sparkles,
    BarChart3, MoreHorizontal, Settings2, Trash2, ExternalLink
} from "lucide-react";

import { Campaign, pauseCampaign, enableCampaign, deleteCampaign } from "../../lib/api";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem,
    DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuLabel
} from "../ui/dropdown-menu";
import { Switch } from "../ui/switch";
import { toast } from "sonner";

interface CampaignCardProps {
    campaign: Campaign;
    onUpdate: () => void;
}

export function CampaignCard({ campaign, onUpdate }: CampaignCardProps) {
    const [loading, setLoading] = useState(false);

    const isAiCreated = campaign.created_by_user_id === null; // Assuming null creator is AI/System
    const isActive = campaign.status === 'active';

    const handleToggleStatus = async (checked: boolean) => {
        setLoading(true);
        try {
            if (checked) {
                await enableCampaign(campaign.id, campaign.connection_id);
                toast.success("Кампания запущена");
            } else {
                await pauseCampaign(campaign.id, campaign.connection_id);
                toast.success("Кампания приостановлена");
            }
            onUpdate();
        } catch (e) {
            toast.error("Не удалось изменить статус");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("Вы уверены? Кампания будет удалена.")) return;
        try {
            await deleteCampaign(campaign.id);
            toast.success("Кампания удалена");
            onUpdate();
        } catch (e) {
            toast.error("Ошибка удаления");
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="group relative bg-panel border-border border rounded-xl overflow-hidden hover:border-violet-500/30 transition-all duration-300 hover:shadow-2xl hover:shadow-violet-500/5"
        >
            {/* Top Banner for AI */}
            {isAiCreated && (
                <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-cyan-500" />
            )}

            <div className="p-5">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <div className="flex gap-4">
                        {/* Platform Icon */}
                        <div className={cn(
                            "w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold border border-white/5",
                            campaign.platform === 'yandex' ? "bg-yellow-500/10 text-yellow-500" :
                                campaign.platform === 'vk' ? "bg-blue-500/10 text-blue-500" :
                                    "bg-panel-strong text-muted"
                        )}>
                            {campaign.platform[0]?.toUpperCase()}
                        </div>

                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-text text-lg line-clamp-1 group-hover:text-violet-200 transition-colors">
                                    {campaign.name}
                                </h3>
                                {isAiCreated && (
                                    <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-violet-500/30 text-violet-400 gap-1">
                                        <Sparkles className="w-2.5 h-2.5" /> AI
                                    </Badge>
                                )}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted">
                                <span>
                                    {new Date(campaign.created_at).toLocaleDateString("ru-RU", {
                                        day: 'numeric',
                                        month: 'long',
                                        year: 'numeric'
                                    })}
                                </span>
                                <span>•</span>
                                <span className={cn(
                                    "capitalize flex items-center gap-1",
                                    isActive ? "text-green-400" : "text-yellow-400"
                                )}>
                                    <span className={cn(
                                        "w-1.5 h-1.5 rounded-full",
                                        isActive ? "bg-green-400 animate-pulse" : "bg-yellow-400"
                                    )} />
                                    {campaign.status}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2 bg-panel-strong px-2 py-1 rounded-lg border border-white/5">
                            <Switch
                                checked={isActive}
                                onCheckedChange={handleToggleStatus}
                                disabled={loading}
                                className="scale-75 data-[state=checked]:bg-green-500"
                            />
                        </div>

                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-white">
                                    <MoreHorizontal className="w-4 h-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Действия</DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => onUpdate()}>
                                    <Settings2 className="w-4 h-4 mr-2" /> Настроить
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={handleDelete} className="text-red-400 focus:text-red-400">
                                    <Trash2 className="w-4 h-4 mr-2" /> Удалить
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="bg-panel-strong/50 rounded-lg p-3 border border-white/5">
                        <div className="flex items-center gap-1.5 text-xs text-muted mb-1">
                            <Eye className="w-3.5 h-3.5" /> Показы
                        </div>
                        <div className="text-lg font-semibold text-text">0</div>
                    </div>
                    <div className="bg-panel-strong/50 rounded-lg p-3 border border-white/5">
                        <div className="flex items-center gap-1.5 text-xs text-muted mb-1">
                            <MousePointer2 className="w-3.5 h-3.5" /> Клики
                        </div>
                        <div className="text-lg font-semibold text-text">0</div>
                    </div>
                    <div className="bg-panel-strong/50 rounded-lg p-3 border border-white/5">
                        <div className="flex items-center gap-1.5 text-xs text-muted mb-1">
                            <Banknote className="w-3.5 h-3.5" /> Расход
                        </div>
                        <div className="text-lg font-semibold text-text">
                            {campaign.budget_total ? `${campaign.budget_total} ₽` : "∞"}
                        </div>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-border/50">
                    <Button variant="outline" size="sm" className="w-full text-xs hover:bg-violet-500/10 hover:text-violet-400 hover:border-violet-500/30 transition-colors">
                        <BarChart3 className="w-3.5 h-3.5 mr-2" />
                        Подробная статистика
                    </Button>
                </div>
            </div>
        </motion.div>
    );
}
