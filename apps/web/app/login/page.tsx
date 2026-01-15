"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { demoSeed, loginUser } from "../../lib/api";
import { STR } from "../../lib/strings";
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
  const [demoLoading, setDemoLoading] = useState(false);

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
      setNotice(STR.messages.loginSuccess);
      toast.success(STR.messages.loginSuccess);
      if (inviteToken) {
        router.push(`/invite/${encodeURIComponent(inviteToken)}`);
        return;
      }
      router.push("/dashboard");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleDemo = async () => {
    setError(null);
    setNotice(null);
    setDemoLoading(true);
    try {
      const demo = await demoSeed();
      if (demo.demo_user_email) {
        setEmail(demo.demo_user_email);
      }
      if (demo.demo_password) {
        setPassword(demo.demo_password);
      }
      setNotice(STR.messages.demoReady);
      toast.success(STR.messages.demoReady);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>{STR.nav.login}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
          {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
        <div className="space-y-2">
          <Label htmlFor="login-email">{STR.labels.email}</Label>
          <Input
            id="login-email"
            type="email"
            placeholder="почта@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="login-password">{STR.labels.password}</Label>
          <Input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleLogin}>{STR.actions.login}</Button>
          <Button
            variant="secondary"
            onClick={() => router.push(inviteToken ? `/signup?invite=${encodeURIComponent(inviteToken)}` : "/signup")}
          >
            {STR.actions.signup}
          </Button>
          <Button variant="secondary" onClick={handleDemo} disabled={demoLoading}>
            {STR.actions.demoAccess}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
