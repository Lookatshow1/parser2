"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { acceptInvite } from "../../lib/api";
import { getToken, setOrgId } from "../../lib/session";

export default function InvitePage() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const authToken = useMemo(() => getToken(), []);

  if (token) {
    return (
      <div className="card">
        <p className="text-slate-300">Invite link format changed.</p>
        <Link href={`/invite/${encodeURIComponent(token)}`} className="text-blue-400">
          Continue to invite
        </Link>
      </div>
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
      setStatus(`Joined ${result.organization_name}. Active org set.`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (!authToken) {
    return (
      <div className="card">
        <p className="text-slate-300">Login required to accept invites.</p>
        <Link href="/login" className="text-blue-400">Go to login</Link>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <h1 className="text-xl font-semibold">Accept invite</h1>
      {token ? (
        <div className="text-sm text-slate-300">Invite token detected.</div>
      ) : (
        <div className="text-sm text-slate-400">Missing token in URL.</div>
      )}
      {error && <div className="text-red-400">{error}</div>}
      {status && <div className="text-green-400">{status}</div>}
      <button onClick={handleAccept} disabled={!token}>Accept invite</button>
    </div>
  );
}
