"use client";
export const dynamic = "force-dynamic";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { acceptInvite } from "../../lib/api";
import { getToken, setOrgId } from "../../lib/session";
import { STR } from "../../lib/strings";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";

export default function InvitePage() {
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const authToken = useMemo(() => getToken(), []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setToken(params.get("token") || "");
  }, []);

  if (token) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-muted">Формат ссылки на приглашение изменился.</p>
          <Link href={`/invite/${encodeURIComponent(token)}`} className="text-accent hover:opacity-80">
            Перейти к приглашению
          </Link>
        </CardContent>
      </Card>
    );
  }

  const handleAccept = async () => {
    setError(null);
    setStatus(null);
    try {
      const result = await acceptInvite({ token });
      if (result.active_organization_id) {
        setOrgId(String(result.active_organization_id));
      }
      setStatus(`Вы присоединились к ${result.organization_name}.`);
      toast.success("Приглашение принято");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  if (!authToken) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-muted">Нужно войти, чтобы принять приглашение.</p>
          <Link href="/login" className="text-accent hover:opacity-80">Перейти ко входу</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
          <CardTitle>{STR.actions.acceptInvite}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {token ? (
          <div className="text-sm text-muted">Токен приглашения найден.</div>
        ) : (
          <div className="text-sm text-muted">В ссылке нет токена.</div>
        )}
        {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        {status && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{status}</div>}
        <Button onClick={handleAccept} disabled={!token}>{STR.actions.acceptInvite}</Button>
      </CardContent>
    </Card>
  );
}
