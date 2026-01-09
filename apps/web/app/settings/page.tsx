"use client";

import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { STR } from "../../lib/strings";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{STR.nav.settings}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-400">Раздел настроек будет добавлен позже. Сейчас доступен базовый функционал.</div>
        </CardContent>
      </Card>
    </div>
  );
}
