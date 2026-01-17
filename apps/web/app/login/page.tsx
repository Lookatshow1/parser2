"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Sparkles, ArrowLeft, Loader2 } from "lucide-react";
import { loginUser } from "../../lib/api";
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
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setInviteToken(params.get("invite"));
  }, []);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);

    try {
      const token = await loginUser({ email, password });
      setToken(token.access_token);
      setRefreshToken(token.refresh_token);
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
            <div className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl text-white">{STR.nav.login}</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="login-email" className="text-gray-300">{STR.labels.email}</Label>
              <Input
                id="login-email"
                type="email"
                placeholder="почта@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="login-password" className="text-gray-300">{STR.labels.password}</Label>
              <Input
                id="login-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-black/30 border-white/10 text-white placeholder:text-gray-500"
              />
            </div>

            <Button
              onClick={handleLogin}
              disabled={loading}
              className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Входим...
                </>
              ) : (
                STR.actions.login
              )}
            </Button>

            <div className="text-center text-sm text-gray-400">
              Нет аккаунта?{" "}
              <Link
                href={inviteToken ? `/signup?invite=${encodeURIComponent(inviteToken)}` : "/signup"}
                className="text-violet-400 hover:text-violet-300"
              >
                Зарегистрироваться
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
