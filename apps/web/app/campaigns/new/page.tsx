"use client";
export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createCampaign } from "../../../lib/api";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";

const steps = ["Кампания", "Бюджет и даты", "Резюме"];

export default function CampaignBuilderPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    name: "",
    platform: "yandex",
    objective: "",
    budget_total: "",
    budget_daily: "",
    start_date: "",
    end_date: "",
    status: "draft",
  });

  const summary = useMemo(() => ({
    name: form.name || "Без названия",
    platform: form.platform,
    objective: form.objective || "—",
    budget_total: form.budget_total ? `${form.budget_total} ₽` : "—",
    budget_daily: form.budget_daily ? `${form.budget_daily} ₽/день` : "—",
    start_date: form.start_date || "—",
    end_date: form.end_date || "—",
  }), [form]);

  const canNext = useMemo(() => {
    if (step === 0) return form.name.trim().length > 0;
    return true;
  }, [step, form.name]);

  const handleCreate = async () => {
    try {
      const payload = {
        name: form.name,
        platform: form.platform,
        objective: form.objective || null,
        status: form.status,
        budget_total: form.budget_total ? Number(form.budget_total) : null,
        budget_daily: form.budget_daily ? Number(form.budget_daily) : null,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
      };
      const created = await createCampaign(payload);
      toast.success("Кампания создана");
      router.push(`/campaigns/${created.id}`);
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Конструктор кампании</h1>
        <p className="text-sm text-slate-400">Шаг {step + 1} из 3: {steps[step]}</p>
      </div>

      {step === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Основные параметры</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Название</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Платформа</Label>
              <select
                className="w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                value={form.platform}
                onChange={(e) => setForm({ ...form, platform: e.target.value })}
              >
                <option value="yandex">Яндекс</option>
                <option value="ozon">Ozon</option>
                <option value="vk">VK</option>
                <option value="stub">Stub</option>
              </select>
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Цель кампании</Label>
              <Input value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} placeholder="Например, рост заявок" />
            </div>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Бюджет и даты</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Бюджет на период</Label>
              <Input type="number" value={form.budget_total} onChange={(e) => setForm({ ...form, budget_total: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Бюджет на день</Label>
              <Input type="number" value={form.budget_daily} onChange={(e) => setForm({ ...form, budget_daily: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Дата начала</Label>
              <Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Дата окончания</Label>
              <Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Резюме</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-300">
            <div>Название: <span className="text-slate-100">{summary.name}</span></div>
            <div>Платформа: <span className="text-slate-100">{summary.platform}</span></div>
            <div>Цель: <span className="text-slate-100">{summary.objective}</span></div>
            <div>Бюджет на период: <span className="text-slate-100">{summary.budget_total}</span></div>
            <div>Бюджет на день: <span className="text-slate-100">{summary.budget_daily}</span></div>
            <div>Дата начала: <span className="text-slate-100">{summary.start_date}</span></div>
            <div>Дата окончания: <span className="text-slate-100">{summary.end_date}</span></div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={() => (step === 0 ? router.push("/campaigns") : setStep(step - 1))}>
          Назад
        </Button>
        {step < 2 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canNext}>Дальше</Button>
        ) : (
          <Button onClick={handleCreate}>Создать кампанию</Button>
        )}
      </div>
    </div>
  );
}
