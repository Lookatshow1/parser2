"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { acceptInvite, getMe, previewInvite } from "../../../lib/api";
import { getToken, clearToken, clearRefreshToken, setOrgId } from "../../../lib/session";
import { ru } from "../../../lib/ru";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Skeleton } from "../../../components/ui/skeleton";

type Preview = {
  organization_id?: number | null;
  organization_name?: string | null;
  invited_email?: string | null;
  role?: string | null;
  expires_at?: string | null;
  status: string;
};

export default function InviteTokenPage({ params }: { params: { token: string } }) {
  const router = useRouter();
  const token = params.token;
  const [preview, setPreview] = useState<Preview | null>(null);
  const [meEmail, setMeEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const authToken = getToken();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await previewInvite(token);
        setPreview(data);
      } catch (err) {
        const message = (err as Error).message;
        setError(message);
        toast.error(message);
      }
    };
    load();
  }, [token]);

  useEffect(() => {
    const loadMe = async () => {
      if (!authToken) return;
      try {
        const me = await getMe();
        setMeEmail(me.email);
      } catch {
        setMeEmail(null);
      }
    };
    loadMe();
  }, [authToken]);

  const handleAccept = async () => {
    setError(null);
    setNotice(null);
    try {
      const result = await acceptInvite({ token });
      if (result.active_organization_id) {
        setOrgId(String(result.active_organization_id));
      }
      setNotice(`Вы присоединились к ${result.organization_name}`);
      toast.success("Приглашение принято");
      router.push("/connections");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleLogout = () => {
    clearToken();
    clearRefreshToken();
    router.push(`/login?invite=${encodeURIComponent(token)}`);
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Приглашение</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-red-300">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!preview) {
    return (
      <Card>
        <CardContent className="py-6">
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (preview.status !== "active") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Приглашение</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-slate-300">Статус: {preview.status}</div>
        </CardContent>
      </Card>
    );
  }

  const inviteEmail = preview.invited_email || "";

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Приглашение в {preview.organization_name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
          <Badge variant="info">Роль: {preview.role}</Badge>
          <span>Email: {inviteEmail}</span>
        </div>
        {notice && <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{notice}</div>}
        {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}

        {!authToken && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => router.push(`/login?invite=${encodeURIComponent(token)}`)}>
              {ru.actions.login}
            </Button>
            <Button variant="secondary" onClick={() => router.push(`/signup?invite=${encodeURIComponent(token)}`)}>
              {ru.actions.signup}
            </Button>
          </div>
        )}

        {authToken && meEmail && meEmail.toLowerCase() !== inviteEmail.toLowerCase() && (
          <div className="space-y-2">
            <div className="text-slate-300">
              Вы вошли как {meEmail}. Это приглашение для {inviteEmail}.
            </div>
            <Button variant="secondary" onClick={handleLogout}>Сменить аккаунт</Button>
          </div>
        )}

        {authToken && (!meEmail || meEmail.toLowerCase() === inviteEmail.toLowerCase()) && (
          <Button onClick={handleAccept}>{ru.actions.acceptInvite}</Button>
        )}
      </CardContent>
    </Card>
  );
}
