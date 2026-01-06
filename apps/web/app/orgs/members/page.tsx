"use client";

import { useEffect, useMemo, useState } from "react";
import { createInvite, listInvites, listMembers } from "../../../lib/api";
import { getOrgId, getToken } from "../../../lib/session";
import Link from "next/link";

const roles = ["owner", "admin", "member", "viewer"];

export default function OrgMembersPage() {
  const [members, setMembers] = useState<Array<{ user_id: number; email: string; role: string }>>([]);
  const [invites, setInvites] = useState<Array<{ id: number; invited_email: string; role: string; expires_at: string; accepted_at: string | null }>>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);

  const token = useMemo(() => getToken(), []);
  const orgId = useMemo(() => getOrgId(), []);

  const load = async () => {
    if (!orgId) {
      return;
    }
    try {
      const [memberData, inviteData] = await Promise.all([
        listMembers(Number(orgId)),
        listInvites(Number(orgId))
      ]);
      setMembers(memberData);
      setInvites(inviteData.items);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleInvite = async () => {
    if (!orgId) {
      setError("Select organization first.");
      return;
    }
    setError(null);
    setNotice(null);
    setInviteToken(null);
    try {
      const created = await createInvite(Number(orgId), { email, role });
      setNotice(`Invite created for ${created.invited_email}`);
      setInviteToken(created.invite_token);
      setEmail("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (!token) {
    return (
      <div className="card">
        <p className="text-slate-300">Login required.</p>
        <Link href="/login" className="text-blue-400">Go to login</Link>
      </div>
    );
  }

  if (!orgId) {
    return (
      <div className="card">
        <p className="text-slate-300">Select an organization first.</p>
        <Link href="/orgs" className="text-blue-400">Go to organizations</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Organization members</h1>
        {error && <div className="text-red-400">{error}</div>}
        {notice && <div className="text-green-400">{notice}</div>}
        {inviteToken && (
          <div className="text-sm text-slate-200">
            Invite token: <span className="font-mono">{inviteToken}</span>
          </div>
        )}
        <div className="flex flex-col gap-2">
          <input
            placeholder="email@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            {roles.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <button onClick={handleInvite}>Create invite</button>
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Members</h2>
        <div className="space-y-2 text-sm">
          {members.map((member) => (
            <div key={member.user_id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span>{member.email}</span>
              <span className="text-slate-400">{member.role}</span>
            </div>
          ))}
          {members.length === 0 && <div className="text-slate-400">No members.</div>}
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Invites</h2>
        <div className="space-y-2 text-sm">
          {invites.map((invite) => (
            <div key={invite.id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span>{invite.invited_email}</span>
              <span className="text-slate-400">{invite.role}</span>
              <span className="text-slate-500">{invite.accepted_at ? "accepted" : "pending"}</span>
            </div>
          ))}
          {invites.length === 0 && <div className="text-slate-400">No invites.</div>}
        </div>
      </div>
    </div>
  );
}
