"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { listChangePlans, listConnections, ChangePlanOut, ConnectionResponse } from "../../lib/api";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

const statusVariant: Record<string, "default" | "secondary" | "success" | "destructive"> = {
  draft: "secondary",
  ready: "default",
  applied: "success",
  failed: "destructive",
};

export default function PlansPage() {
  const router = useRouter();
  const [items, setItems] = useState<ChangePlanOut[]>([]);
  const [connections, setConnections] = useState<ConnectionResponse[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>("all");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadConns = async () => {
      try {
        const data = await listConnections();
        setConnections(data.items);
      } catch (err) {
        toast.error((err as Error).message);
      }
    };
    loadConns();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const data = await listChangePlans({
        connection_id: selectedConnection === "all" ? undefined : Number(selectedConnection),
      });
      setItems(data);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [selectedConnection]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <CardTitle>Планы изменений</CardTitle>
          <Button onClick={() => router.push("/connections")}>Создать план</Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            <select
              value={selectedConnection}
              onChange={(event) => setSelectedConnection(event.target.value)}
              className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm text-slate-100"
            >
              <option value="all">Все подключения</option>
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || `Подключение #${c.id}`}
                </option>
              ))}
            </select>
            <Button onClick={load} variant="secondary">{STR.actions.refresh}</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {loading && <div className="p-6"><Skeleton className="h-40 w-full" /></div>}
          {!loading && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Название</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Подключение</TableHead>
                  <TableHead>Создан</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>#{item.id}</TableCell>
                    <TableCell className="font-medium">{item.title}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant[item.status] || "secondary"}>
                        {item.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>#{item.connection_id}</TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {new Date(item.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="ghost" onClick={() => router.push(`/plans/${item.id}`)}>
                        Открыть
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!items.length && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-slate-500 py-8">Нет планов</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
