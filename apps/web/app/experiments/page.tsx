"use client";
export const dynamic = "force-dynamic";
import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  createExperiment,
  listExperiments,
  listPlans,
  startExperiment,
  ExperimentListItem,
  PlanResponse
} from "../../lib/api";
import { ru } from "../../lib/ru";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

export default function ExperimentsPage() {
  const [items, setItems] = useState<ExperimentListItem[]>([]);
  const [plans, setPlans] = useState<PlanResponse[]>([]);
  const [planId, setPlanId] = useState("");
  const [budget, setBudget] = useState("10000");
  const [platforms, setPlatforms] = useState("yandex,ozon,vk");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      const [experimentsData, plansData] = await Promise.all([listExperiments(), listPlans()]);
      setItems(experimentsData.items);
      setPlans(plansData.items);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    setError(null);
    setNotice(null);
    try {
      if (!planId) {
        const message = "Выберите план перед запуском эксперимента.";
        setError(message);
        toast.error(message);
        return;
      }
      const experiment = await createExperiment({
        plan_id: Number(planId),
        budget: Number(budget),
        platforms: platforms.split(",").map((item) => item.trim())
      });
      await startExperiment(experiment.id);
      setNotice(`Эксперимент ${experiment.id} запущен`);
      toast.success("Эксперимент запущен");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{ru.nav.experiments}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
          {notice && <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{notice}</div>}
          <div className="grid gap-3 md:grid-cols-4">
            <select value={planId} onChange={(event) => setPlanId(event.target.value)} className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm">
              <option value="">Выберите план</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.id} - {plan.url}
                </option>
              ))}
            </select>
            <Input value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="Бюджет" />
            <Input
              value={platforms}
              onChange={(event) => setPlatforms(event.target.value)}
              placeholder="Платформы (через запятую)"
            />
            <Button onClick={handleCreate}>Создать и запустить</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Эксперименты</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead>План</TableHead>
                <TableHead className="text-right">Отчёт</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>#{item.id}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  <TableCell>План {item.plan_id ?? "—"}</TableCell>
                  <TableCell className="text-right">
                    <Link className="text-blue-300 hover:text-blue-200" href={`/experiments/${item.id}`}>
                      Отчёт
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-slate-400">Экспериментов пока нет.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
