"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { registerUserWithInvite } from "../../lib/api";
import { setRefreshToken, setToken } from "../../lib/session";

export default function SignupPage() {
  const params = useSearchParams();
  const router = useRouter();
  const inviteToken = params.get("invite");
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("secret123");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const inviteLabel = useMemo(() => (inviteToken ? "Invite detected" : null), [inviteToken]);

  const handleSignup = async () => {
    setError(null);
    setNotice(null);
    try {
      await registerUserWithInvite({ email, password, invite_token: inviteToken || undefined });
      setNotice("Account created. You can log in now.");
      router.push(inviteToken ? `/login?invite=${encodeURIComponent(inviteToken)}` : "/login");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="card space-y-4 max-w-md">
      <h1 className="text-xl font-semibold">Sign up</h1>
      {inviteLabel && <div className="text-sm text-slate-400">{inviteLabel}</div>}
      {error && <div className="text-red-400">{error}</div>}
      {notice && <div className="text-green-400">{notice}</div>}
      <label className="text-sm text-slate-400">Email</label>
      <input value={email} onChange={(event) => setEmail(event.target.value)} />
      <label className="text-sm text-slate-400">Password</label>
      <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <div className="flex gap-2">
        <button onClick={handleSignup}>Create account</button>
        <Link href="/login" className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm">
          Back to login
        </Link>
      </div>
    </div>
  );
}
