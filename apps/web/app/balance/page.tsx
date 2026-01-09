"use client";

import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { STR } from "../../lib/strings";

export default function BalancePage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{STR.nav.balance}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-400">Раздел в разработке. Скоро появятся пополнения и история списаний.</div>
        </CardContent>
      </Card>
    </div>
  );
}
