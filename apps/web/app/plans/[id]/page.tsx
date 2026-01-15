"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { getChangePlan, markPlanReady, applyPlan, ChangePlanOut } from "../../../lib/api";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Skeleton } from "../../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

const statusVariant: Record<string, "default" | "secondary" | "success" | "destructive"> = {
  draft: "secondary",
  ready: "default",
  applied: "success",
  failed: "destructive",
  pending: "secondary",
};

export default function PlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const planId = Number(params?.id);
  const [plan, setPlan] = useState<ChangePlanOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getChangePlan(planId);
      setPlan(data);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (planId) load();
  }, [planId]);

  const handleReady = async () => {
    if (!confirm("Зафиксировать план? Редактирование будет недоступно.")) return;
    setProcessing(true);
    try {
      await markPlanReady(planId);
      toast.success("План зафиксирован");
      await load();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setProcessing(false);
    }
  };

  const handleApply = async () => {
    if (!confirm("Применить изменения?")) return;
    setProcessing(true);
    try {
      await applyPlan(planId);
      toast.success("Применение запущено");
      // Poll for status update? Or just reload once.
      setTimeout(load, 2000);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setProcessing(false);
    }
  };

  if (loading && !plan) return <div className="p-6"><Skeleton className="h-40 w-full" /></div>;
  if (!plan) return <div className="p-6 text-center text-muted">План не найден</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {plan.title}
              <Badge variant={statusVariant[plan.status]}>{plan.status.toUpperCase()}</Badge>
            </CardTitle>
            <div className="text-sm text-muted mt-1">
              Подключение #{plan.connection_id} · Создан {new Date(plan.created_at).toLocaleString()}
            </div>
          </div>
          <div className="flex gap-2">
            {plan.status === "draft" && (
              <Button onClick={handleReady} disabled={processing}>Зафиксировать</Button>
            )}
            {plan.status === "ready" && (
              <Button onClick={handleApply} disabled={processing}>Применить</Button>
            )}
            {plan.status === "applied" && (
              <Badge variant="success">Применено {plan.applied_at ? new Date(plan.applied_at).toLocaleString() : ""}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {plan.error && (
            <div className="mb-4 rounded-md border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
              Ошибка: {plan.error}
            </div>
          )}

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Тип</TableHead>
                <TableHead>ID Объекта</TableHead>
                <TableHead>Действие</TableHead>
                <TableHead>Параметры</TableHead>
                <TableHead>Статус</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plan.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="capitalize">{item.subject_type}</TableCell>
                  <TableCell>#{item.subject_id}</TableCell>
                  <TableCell>{item.action_type}</TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate">
                    {JSON.stringify(item.params_json)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusVariant[item.status] || "secondary"}>{item.status}</Badge>
                    {item.error && <div className="text-xs text-danger mt-1">{item.error}</div>}
                  </TableCell>
                </TableRow>
              ))}
              {!plan.items.length && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted py-4">Нет действий</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
