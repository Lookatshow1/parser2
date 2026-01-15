"use client";

import { useState } from "react";
import { toast } from "sonner";
import { createPlan } from "../../../lib/api";
import { ru } from "../../../lib/ru";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";

export default function NewPlanPage() {
  const [url, setUrl] = useState("");
  const [businessDescription, setBusinessDescription] = useState("");
  const [kpi, setKpi] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setNotice(null);
    try {
      await createPlan({
        url,
        business_description: businessDescription || null,
        kpi: kpi || null
      });
      setNotice("План создан");
      toast.success("План создан");
      setUrl("");
      setBusinessDescription("");
      setKpi("");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Создание плана</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
        <div className="space-y-2">
          <Label>URL лендинга</Label>
          <Input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com" />
        </div>
        <div className="space-y-2">
          <Label>Описание бизнеса</Label>
          <textarea
            value={businessDescription}
            onChange={(event) => setBusinessDescription(event.target.value)}
            placeholder="Короткое описание"
            rows={3}
            className="w-full rounded-md border border-border bg-panel px-3 py-2 text-sm text-text placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
          />
        </div>
        <div className="space-y-2">
          <Label>KPI</Label>
          <Input value={kpi} onChange={(event) => setKpi(event.target.value)} placeholder="Например: CPA 1200" />
        </div>
        <Button onClick={handleSubmit}>{ru.actions.create}</Button>
      </CardContent>
    </Card>
  );
}
