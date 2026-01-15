"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import {
  listCatalogCampaigns,
  listCatalogAdGroups,
  listCatalogAds,
  buildUtmLink,
  AdCampaignOut,
  AdAdGroupOut,
  AdAdOut
} from "../../../../lib/api";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Input } from "../../../../components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../../components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../../../components/ui/tabs";
import { Copy, Link as LinkIcon } from "lucide-react";

export default function CatalogPage() {
  const params = useParams();
  const connectionId = Number(params?.id);

  const [tab, setTab] = useState("campaigns");
  const [campaigns, setCampaigns] = useState<AdCampaignOut[]>([]);
  const [groups, setGroups] = useState<AdAdGroupOut[]>([]);
  const [ads, setAds] = useState<AdAdOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  // UTM Builder state
  const [utmUrl, setUtmUrl] = useState("");
  const [generatedUrl, setGeneratedUrl] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === "campaigns") {
        const data = await listCatalogCampaigns(connectionId, { query: search });
        setCampaigns(data);
      } else if (tab === "groups") {
        const data = await listCatalogAdGroups(connectionId, { query: search });
        setGroups(data);
      } else if (tab === "ads") {
        const data = await listCatalogAds(connectionId, { query: search });
        setAds(data);
      }
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (connectionId) loadData();
  }, [connectionId, tab, search]);

  const handleGenerateUtm = async (ad: AdAdOut) => {
    if (!utmUrl) {
      toast.error("Введите базовый URL");
      return;
    }
    try {
      const res = await buildUtmLink({
        url: utmUrl,
        platform: ad.platform,
        campaign_external_id: ad.campaign_external_id,
        ad_group_external_id: ad.ad_group_external_id,
        ad_external_id: ad.external_id
      });
      setGeneratedUrl(res.final_url);
      navigator.clipboard.writeText(res.final_url);
      toast.success("Ссылка скопирована");
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Каталог объектов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <Input
              placeholder="Поиск..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="max-w-sm"
            />
            <Button onClick={loadData} variant="secondary">Обновить</Button>
          </div>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="campaigns">Кампании</TabsTrigger>
              <TabsTrigger value="groups">Группы</TabsTrigger>
              <TabsTrigger value="ads">Объявления</TabsTrigger>
            </TabsList>

            <TabsContent value="campaigns" className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Название</TableHead>
                    <TableHead>External ID</TableHead>
                    <TableHead>Обновлено</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaigns.map(c => (
                    <TableRow key={c.id}>
                      <TableCell>{c.id}</TableCell>
                      <TableCell>{c.name}</TableCell>
                      <TableCell className="font-mono text-xs">{c.external_id}</TableCell>
                      <TableCell className="text-muted">{new Date(c.updated_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                  {!campaigns.length && !loading && <TableRow><TableCell colSpan={4} className="text-center text-muted">Нет данных</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TabsContent>

            <TabsContent value="groups" className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Название</TableHead>
                    <TableHead>External ID</TableHead>
                    <TableHead>Кампания ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {groups.map(g => (
                    <TableRow key={g.id}>
                      <TableCell>{g.id}</TableCell>
                      <TableCell>{g.name}</TableCell>
                      <TableCell className="font-mono text-xs">{g.external_id}</TableCell>
                      <TableCell className="font-mono text-xs">{g.campaign_external_id}</TableCell>
                    </TableRow>
                  ))}
                  {!groups.length && !loading && <TableRow><TableCell colSpan={4} className="text-center text-muted">Нет данных</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TabsContent>

            <TabsContent value="ads" className="mt-4">
              <div className="mb-4 rounded-md border border-border bg-panel p-4">
                <h3 className="mb-2 text-sm font-medium text-muted">Генератор ссылок</h3>
                <div className="flex gap-2">
                  <Input
                    placeholder="https://example.com/landing"
                    value={utmUrl}
                    onChange={e => setUtmUrl(e.target.value)}
                  />
                  {generatedUrl && (
                    <div className="flex-1 rounded border border-border bg-panel-strong px-3 py-2 text-sm font-mono text-muted truncate">
                      {generatedUrl}
                    </div>
                  )}
                </div>
                <p className="mt-2 text-xs text-muted">
                  Введите URL и нажмите кнопку "Link" в таблице, чтобы сгенерировать ссылку с UTM для конкретного объявления.
                </p>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Название</TableHead>
                    <TableHead>External ID</TableHead>
                    <TableHead>Группа ID</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ads.map(a => (
                    <TableRow key={a.id}>
                      <TableCell>{a.id}</TableCell>
                      <TableCell>{a.name}</TableCell>
                      <TableCell className="font-mono text-xs">{a.external_id}</TableCell>
                      <TableCell className="font-mono text-xs">{a.ad_group_external_id}</TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" variant="ghost" onClick={() => handleGenerateUtm(a)} title="Сгенерировать UTM">
                          <LinkIcon className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!ads.length && !loading && <TableRow><TableCell colSpan={5} className="text-center text-muted">Нет данных</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
