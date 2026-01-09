"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { loginUser } from "../../lib/api";
import { ru } from "../../lib/ru";
import { setRefreshToken, setToken } from "../../lib/session";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setInviteToken(params.get("invite"));
  }, []);

  const handleLogin = async () => {
    setError(null);
    setNotice(null);
    try {
      const token = await loginUser({ email, password });
      setToken(token.access_token);
      setRefreshToken(token.refresh_token);
      setNotice("Вход выполнен.");
      toast.success("Вы вошли в систему.");
      if (inviteToken) {
        router.push(`/invite/${encodeURIComponent(inviteToken)}`);
        return;
      }
      router.push("/orgs");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>{ru.nav.login}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
        {notice && <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{notice}</div>}
        <div className="space-y-2">
          <Label htmlFor="login-email">{ru.labels.email}</Label>
          <Input
            id="login-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="login-password">{ru.labels.password}</Label>
          <Input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleLogin}>{ru.actions.login}</Button>
          <Button
            variant="secondary"
            onClick={() => router.push(inviteToken ? `/signup?invite=${encodeURIComponent(inviteToken)}` : "/signup")}
          >
            {ru.actions.signup}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
