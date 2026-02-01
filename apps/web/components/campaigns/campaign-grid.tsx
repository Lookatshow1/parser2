"use client";

import { Campaign } from "../../lib/api";
import { CampaignCard } from "./campaign-card";
import { AnimatePresence } from "framer-motion";

interface CampaignGridProps {
    campaigns: Campaign[];
    onUpdate: () => void;
}

export function CampaignGrid({ campaigns, onUpdate }: CampaignGridProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
                {campaigns.map((campaign) => (
                    <CampaignCard
                        key={campaign.id}
                        campaign={campaign}
                        onUpdate={onUpdate}
                    />
                ))}
            </AnimatePresence>
        </div>
    );
}
