"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { listAuditEvents, OrgAuditEvent } from "../../../lib/api";
import { getOrgId, getToken } from "../../../lib/session";
import { ru } from "../../../lib/ru";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Skeleton } from "../../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

export default function OrgAuditPage() {
  const [items, setItems] = useState<OrgAuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [actionFilter, setActionFilter] = useState<string>("all");

  const orgId = getOrgId();
  const token = getToken();

  const load = async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const data = await listAuditEvents(Number(orgId), { limit: 50, offset });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [orgId, offset]);

  const actions = useMemo(() => {
    const unique = new Set(items.map((item) => item.action));
    return Array.from(unique).sort();
  }, [items]);

  const filteredItems = useMemo(() => {
    if (actionFilter === "all") return items;
    return items.filter((item) => item.action === actionFilter);
  }, [items, actionFilter]);

  if (!token) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-slate-300">{ru.messages.loginRequired}</p>
          <Link href="/login" className="text-blue-400">{ru.nav.login}</Link>
        </CardContent>
      </Card>
    );
  }

  if (!orgId) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-slate-300">{ru.messages.selectOrg}</p>
          <Link href="/orgs" className="text-blue-400">{ru.nav.orgs}</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{ru.nav.audit}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
            <div>Организация #{orgId} · {total} событий</div>
            <div className="flex items-center gap-2">
              <span>{ru.labels.action}</span>
              <select
                className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm"
                value={actionFilter}
                onChange={(event) => setActionFilter(event.target.value)}
              >
                <option value="all">Все</option>
                {actions.map((action) => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </div>
          </div>
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4">
          {loading && <Skeleton className="h-24 w-full" />}
          {!loading && filteredItems.length === 0 && <div className="text-sm text-slate-400">{ru.messages.noAudit}</div>}
          {!loading && filteredItems.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Действие</TableHead>
                  <TableHead>Субъект</TableHead>
                  <TableHead>Актор</TableHead>
                  <TableHead>Дата</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>
                      <Badge variant="info">{event.action}</Badge>
                    </TableCell>
                    <TableCell className="text-slate-400">
                      {event.subject_type || "-"} #{event.subject_id ?? "-"}
                    </TableCell>
                    <TableCell className="text-slate-400">
                      {event.actor_user_id ?? "system"}
                    </TableCell>
                    <TableCell className="text-slate-400">
                      {new Date(event.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 50))}
            >
              Назад
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={offset + 50 >= total}
              onClick={() => setOffset(offset + 50)}
            >
              Вперёд
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
