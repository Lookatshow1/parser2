"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useMemo } from "react";
import { toast } from "sonner";
import { listRecommendations, recomputeRecommendations, resolveRecommendation, listConnections, RecommendationOut, ConnectionResponse } from "../../lib/api";
import { STR } from "../../lib/strings";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../../components/ui/dialog";
import { CheckCircle2, AlertTriangle, Info } from "lucide-react";

const severityVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  info: "secondary",
  warn: "default", // orange usually, but default is primary. Let's use default for warn.
  critical: "destructive",
};

const severityIcon: Record<string, any> = {
  info: Info,
  warn: AlertTriangle,
  critical: AlertTriangle,
};

export default function RecommendationsPage() {
  const [items, setItems] = useState<RecommendationOut[]>([]);
  const [connections, setConnections] = useState<ConnectionResponse[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [selectedItem, setSelectedItem] = useState<RecommendationOut | null>(null);

  const defaultDateRange = useMemo(() => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 13);
    return {
      from: from.toISOString().slice(0, 10),
      to: to.toISOString().slice(0, 10),
    };
  }, []);

  useEffect(() => {
    setDateFrom(defaultDateRange.from);
    setDateTo(defaultDateRange.to);

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
      const data = await listRecommendations({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        connection_id: selectedConnection === "all" ? undefined : Number(selectedConnection),
      });
      setItems(data.items);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom && dateTo) load();
  }, [dateFrom, dateTo, selectedConnection]);

  const handleRecompute = async () => {
    setRecomputing(true);
    try {
      await recomputeRecommendations({
        date_from: dateFrom || defaultDateRange.from,
        date_to: dateTo || defaultDateRange.to,
        connection_ids: selectedConnection === "all" ? undefined : [Number(selectedConnection)],
      });
      toast.success("Пересчёт запущен");
      await load();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setRecomputing(false);
    }
  };

  const handleResolve = async () => {
    if (!selectedItem) return;
    try {
      await resolveRecommendation(selectedItem.id);
      toast.success("Рекомендация выполнена");
      setSelectedItem(null);
      await load();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <CardTitle>Рекомендации</CardTitle>
          <div className="flex gap-2">
             <Button variant="outline" onClick={handleRecompute} disabled={recomputing}>
               {recomputing ? "Пересчёт..." : "Пересчитать"}
             </Button>
          </div>
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
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            <Button onClick={load}>{STR.actions.refresh}</Button>
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
                  <TableHead>Важность</TableHead>
                  <TableHead>Рекомендация</TableHead>
                  <TableHead>Объект</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => {
                  const Icon = severityIcon[item.severity] || Info;
                  return (
                    <TableRow key={item.id} className="cursor-pointer hover:bg-slate-900/50" onClick={() => setSelectedItem(item)}>
                      <TableCell>
                        <Badge variant={severityVariant[item.severity] || "outline"} className="gap-1">
                          <Icon className="h-3 w-3" />
                          {item.severity.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{item.title}</div>
                        <div className="text-xs text-slate-500 truncate max-w-md">{item.description}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{item.subject_name || `#${item.subject_id}`}</div>
                        <div className="text-xs text-slate-500 capitalize">{item.subject_type}</div>
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {new Date(item.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {item.resolved_at ? (
                          <Badge variant="success" className="gap-1"><CheckCircle2 className="h-3 w-3" /> Done</Badge>
                        ) : (
                          <Button size="sm" variant="ghost">Открыть</Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {!items.length && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-slate-500 py-8">Нет рекомендаций</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!selectedItem} onOpenChange={(open) => !open && setSelectedItem(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedItem?.title}</DialogTitle>
            <DialogDescription>
              {selectedItem?.subject_type}: {selectedItem?.subject_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-slate-300">{selectedItem?.description}</div>

            <div className="bg-slate-900 p-3 rounded border border-slate-800">
              <div className="text-xs text-slate-500 mb-1 uppercase">Действие</div>
              <div className="text-sm">{selectedItem?.action}</div>
            </div>

            {selectedItem?.meta_json && Object.keys(selectedItem.meta_json).length > 0 && (
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(selectedItem.meta_json).map(([k, v]) => (
                  <div key={k} className="bg-slate-950 p-2 rounded border border-slate-800 flex justify-between">
                    <span className="text-slate-500">{k}</span>
                    <span className="font-mono">{String(v)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            {!selectedItem?.resolved_at && (
              <Button onClick={handleResolve}>Отметить как сделанное</Button>
            )}
            {selectedItem?.resolved_at && (
              <div className="text-sm text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Выполнено {new Date(selectedItem.resolved_at).toLocaleString()}
              </div>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
