"use client";

import { CampaignWizard } from "@/components/campaigns/wizard/campaign-wizard";

export default function NewCampaignPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Создание кампании</h1>
        <p className="text-muted">Заполните шаги, чтобы создать новую рекламную кампанию</p>
      </div>

      <CampaignWizard />
    </div>
  );
}
