"use client";
export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import { Sparkles, ArrowLeft, Rocket, Loader2 } from "lucide-react";
import { registerUserWithInvite } from "../../lib/api";
import { STR } from "../../lib/strings";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [fromMagic, setFromMagic] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const inviteLabel = useMemo(() => (inviteToken ? STR.messages.inviteDetected : null), [inviteToken]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setInviteToken(params.get("invite"));
    setFromMagic(params.get("from") === "magic");
  }, []);

  const handleSignup = async () => {
    if (!email || !password) {
      setError("Заполните email и пароль");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      // 1. Register user
      await registerUserWithInvite({ email, password, invite_token: inviteToken || undefined });

      // 2. Auto-login
      const { loginUser } = await import("../../lib/api");
      const { setToken, setRefreshToken } = await import("../../lib/session");

      const tokens = await loginUser({ email, password });
      setToken(tokens.access_token);
      setRefreshToken(tokens.refresh_token);

      // 3. Check for pending creatives from landing page
      const pendingCreativesJson = localStorage.getItem("pending_creatives");

      if (pendingCreativesJson && fromMagic) {
        try {
          const { creatives, landing_url } = JSON.parse(pendingCreativesJson);

          // Save creatives to backend
          const response = await fetch("/api/magic/save-creatives", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${tokens.access_token}`
            },
            body: JSON.stringify({ creatives, landing_url })
          });

          if (response.ok) {
            // Clear localStorage
            localStorage.removeItem("pending_creatives");

            toast.success("🎉 Ваши объявления готовы! Осталось пополнить баланс.");
            router.push("/drafts");
            return;
          }
        } catch (e) {
          console.error("Failed to save creatives:", e);
        }
      }

      // Default redirect
      toast.success(STR.messages.signupSuccess);
      router.push("/magic");

    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#0f0f1a] to-[#1a0a20] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center text-gray-400 hover:text-white mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          На главную
        </Link>

        <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
          <CardHeader className="text-center">
            {fromMagic ? (
              <>
                <div className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-4">
                  <Rocket className="h-8 w-8 text-white" />
                </div>
                <CardTitle className="text-2xl text-white">Запустите рекламу!</CardTitle>
                <p className="text-gray-400 mt-2">
                  Ваши креативы уже готовы. Зарегистрируйтесь, чтобы запустить кампанию.
                </p>
              </>
            ) : (
              <>
                <div className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="h-8 w-8 text-white" />
                </div>
                <CardTitle className="text-2xl text-white">{STR.nav.signup}</CardTitle>
              </>
            )}
          </CardHeader>

          <CardContent className="space-y-4">
            {inviteLabel && (
              <div className="text-sm text-violet-400 bg-violet-500/10 border border-violet-500/30 rounded-lg p-3">
                {inviteLabel}
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="signup-email" className="text-gray-300">{STR.labels.email}</Label>
              <Input
                id="signup-email"
                type="email"
                placeholder="почта@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password" className="text-gray-300">{STR.labels.password}</Label>
              <Input
                id="signup-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
              />
            </div>

            <Button
              onClick={handleSignup}
              disabled={loading}
              className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Создаём аккаунт...
                </>
              ) : fromMagic ? (
                <>
                  <Rocket className="mr-2 h-4 w-4" />
                  Зарегистрироваться и запустить
                </>
              ) : (
                STR.actions.signup
              )}
            </Button>

            <div className="text-center text-sm text-gray-400">
              Уже есть аккаунт?{" "}
              <Link href={inviteToken ? `/login?invite=${encodeURIComponent(inviteToken)}` : "/login"} className="text-violet-400 hover:text-violet-300">
                Войти
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
