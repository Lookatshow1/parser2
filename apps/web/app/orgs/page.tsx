"use client";
export const dynamic = "force-dynamic";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { createOrg, getActiveOrg, listOrgs, switchOrg } from "../../lib/api";
import { getOrgId, setOrgId } from "../../lib/session";
import { ru } from "../../lib/ru";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";

type Org = { id: number; name: string };

export default function OrgsPage() {
  const [items, setItems] = useState<Org[]>([]);
  const [activeOrg, setActiveOrg] = useState<Org | null>(null);
  const [name, setName] = useState("Моя организация");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await listOrgs();
      setItems(data.items);
      try {
        const active = await getActiveOrg();
        setActiveOrg(active);
      } catch {
        setActiveOrg(null);
      }
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
  }, []);

  const handleCreate = async () => {
    setError(null);
    setNotice(null);
    try {
      const org = await createOrg({ name });
      setOrgId(String(org.id));
      setActiveOrg(org);
      setNotice(`Организация ${org.name} создана и выбрана.`);
      toast.success("Организация создана");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleSwitch = async (org: Org) => {
    setError(null);
    setNotice(null);
    try {
      await switchOrg({ organization_id: org.id });
      setOrgId(String(org.id));
      setActiveOrg(org);
      setNotice(`Активная организация: ${org.name}`);
      toast.success("Организация переключена");
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
          <CardTitle>{ru.nav.orgs}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
          {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
          <div className="text-sm text-muted">
            {ru.labels.activeOrg}: {activeOrg ? `${activeOrg.name} (#${activeOrg.id})` : "не выбрана"}
          </div>
          <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
            <div className="space-y-2">
              <Label htmlFor="org-name">{ru.labels.orgName}</Label>
              <Input id="org-name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <Button onClick={handleCreate}>{ru.actions.createOrg}</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ваши организации</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && items.length === 0 && <div className="text-sm text-muted">Организаций пока нет.</div>}
          {!loading && items.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Название</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell>#{org.id}</TableCell>
                    <TableCell className="text-text">{org.name}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="secondary" size="sm" onClick={() => handleSwitch(org)}>
                        {ru.actions.switchOrg}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="text-sm text-muted">
          Сохранённая организация в браузере: {getOrgId() || "нет"}
        </CardContent>
      </Card>
    </div>
  );
}
