"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { acceptInvite, getMe, previewInvite } from "../../../lib/api";
import { getToken, clearToken, clearRefreshToken, setOrgId } from "../../../lib/session";

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
        setError((err as Error).message);
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
      setNotice(`Joined ${result.organization_name}`);
      router.push("/connections");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleLogout = () => {
    clearToken();
    clearRefreshToken();
    router.push(`/login?invite=${encodeURIComponent(token)}`);
  };

  if (error) {
    return (
      <div className="card space-y-2">
        <h1 className="text-xl font-semibold">Invite</h1>
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  if (!preview) {
    return <div className="card">Loading invite…</div>;
  }

  if (preview.status !== "active") {
    return (
      <div className="card space-y-2">
        <h1 className="text-xl font-semibold">Invite</h1>
        <div className="text-slate-300">Status: {preview.status}</div>
      </div>
    );
  }

  const inviteEmail = preview.invited_email || "";

  return (
    <div className="card space-y-4 max-w-xl">
      <h1 className="text-xl font-semibold">Invite to {preview.organization_name}</h1>
      <div className="text-sm text-slate-400">
        Role: {preview.role} · Email: {inviteEmail}
      </div>
      {notice && <div className="text-green-400">{notice}</div>}
      {error && <div className="text-red-400">{error}</div>}

      {!authToken && (
        <div className="flex gap-2">
          <Link href={`/login?invite=${encodeURIComponent(token)}`} className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm">
            Log in
          </Link>
          <Link href={`/signup?invite=${encodeURIComponent(token)}`} className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm">
            Sign up
          </Link>
        </div>
      )}

      {authToken && meEmail && meEmail.toLowerCase() !== inviteEmail.toLowerCase() && (
        <div className="space-y-2">
          <div className="text-slate-300">
            You are logged in as {meEmail}. This invite is for {inviteEmail}.
          </div>
          <button onClick={handleLogout} className="bg-slate-700 hover:bg-slate-600 text-sm px-3 py-2 rounded">
            Switch account
          </button>
        </div>
      )}

      {authToken && (!meEmail || meEmail.toLowerCase() === inviteEmail.toLowerCase()) && (
        <button onClick={handleAccept}>Accept invite</button>
      )}
    </div>
  );
}
