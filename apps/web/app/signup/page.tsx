"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { registerUserWithInvite } from "../../lib/api";
import { STR } from "../../lib/strings";
 
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";

export default function SignupPage() {
  const router = useRouter();
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const inviteLabel = useMemo(() => (inviteToken ? STR.messages.inviteDetected : null), [inviteToken]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setInviteToken(params.get("invite"));
  }, []);

  const handleSignup = async () => {
    setError(null);
    setNotice(null);
    try {
      await registerUserWithInvite({ email, password, invite_token: inviteToken || undefined });
      setNotice(STR.messages.accountCreated);
      toast.success(STR.messages.signupSuccess);
      router.push(inviteToken ? `/login?invite=${encodeURIComponent(inviteToken)}` : "/login");
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>{STR.nav.signup}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {inviteLabel && <div className="text-sm text-muted">{inviteLabel}</div>}
        {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        {notice && <div className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">{notice}</div>}
        <div className="space-y-2">
          <Label htmlFor="signup-email">{STR.labels.email}</Label>
          <Input
            id="signup-email"
            type="email"
            placeholder="почта@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="signup-password">{STR.labels.password}</Label>
          <Input
            id="signup-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleSignup}>{STR.actions.signup}</Button>
          <Button variant="secondary" onClick={() => router.push(inviteToken ? `/login?invite=${encodeURIComponent(inviteToken)}` : "/login")}>
            {STR.actions.back}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
