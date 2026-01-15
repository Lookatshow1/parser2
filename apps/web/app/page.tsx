"use client";

import { useState } from "react";
import { toast } from "sonner";
import { seedDev } from "../lib/api";
import { ru } from "../lib/ru";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function HomePage() {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleSeed = async () => {
    setError(null);
    setNotice(null);
    try {
      const data = await seedDev();
      const message = `Созданы данные: рекламодатель ${data.advertiser_id}, план ${data.plan_id}, эксперимент ${data.experiment_id}`;
      setNotice(message);
      toast.success("Демо-данные созданы.");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{ru.appName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-muted">{ru.messages.homeIntro}</p>
        {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
        <Button onClick={handleSeed}>{ru.actions.seedDemo}</Button>
      </CardContent>
    </Card>
  );
}
