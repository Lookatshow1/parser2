"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  createInvite,
  deleteMember,
  listInvites,
  listMembers,
  revokeInvite,
  updateMemberRole,
} from "../../../lib/api";
import { getOrgId, getToken } from "../../../lib/session";

type Member = {
  user_id: number;
  email: string;
  role: string;
  joined_at: string;
  is_you: boolean;
};

type Invite = {
  id: number;
  invited_email: string;
  role: string;
  status: string;
  expires_at: string;
  created_by_user_id?: number | null;
};

export default function OrgMembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [joinUrl, setJoinUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const orgId = getOrgId();
  const token = getToken();

  const load = async () => {
    if (!orgId) return;
    try {
      const [memberData, inviteData] = await Promise.all([
        listMembers(Number(orgId)),
        listInvites(Number(orgId)),
      ]);
      setMembers(memberData);
      setInvites(inviteData.items);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, [orgId]);

  const handleInvite = async () => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    setInviteToken(null);
    setJoinUrl(null);
    try {
      const invite = await createInvite(Number(orgId), { email, role });
      setInviteToken(invite.invite_token);
      setJoinUrl(invite.join_url || null);
      setNotice(`Invite created for ${invite.invited_email}`);
      setEmail("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleRoleChange = async (userId: number, nextRole: string) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await updateMemberRole(Number(orgId), userId, { role: nextRole });
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleRemove = async (userId: number) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await deleteMember(Number(orgId), userId);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleRevoke = async (inviteId: number) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await revokeInvite(Number(orgId), inviteId);
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
        <Link href="/orgs" className="text-blue-400">Go to orgs</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Team members</h1>
        {error && <div className="text-red-400">{error}</div>}
        {notice && <div className="text-green-400">{notice}</div>}
        <div className="text-sm text-slate-400">Org #{orgId}</div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Invite member</h2>
        <div className="flex flex-wrap gap-2">
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="email@example.com"
          />
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <button onClick={handleInvite} disabled={!email}>Invite</button>
        </div>
        {inviteToken && (
          <div className="text-sm text-slate-300">
            Invite token: <span className="text-slate-100">{inviteToken}</span>
          </div>
        )}
        {joinUrl && (
          <div className="text-sm text-slate-300">
            Join URL: <span className="text-slate-100">{joinUrl}</span>
          </div>
        )}
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Members</h2>
        <div className="grid gap-2 text-sm">
          {members.map((member) => (
            <div key={member.user_id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <div className="text-slate-200">{member.email}</div>
                <div className="text-xs text-slate-500">
                  Joined {new Date(member.joined_at).toLocaleDateString()}
                  {member.is_you ? " (you)" : ""}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={member.role}
                  onChange={(event) => handleRoleChange(member.user_id, event.target.value)}
                >
                  <option value="owner">Owner</option>
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button
                  onClick={() => handleRemove(member.user_id)}
                  className="bg-rose-600 hover:bg-rose-500 text-xs px-3 py-1 rounded"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
          {members.length === 0 && <div className="text-slate-400">No members yet.</div>}
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Active invites</h2>
        <div className="grid gap-2 text-sm">
          {invites.map((invite) => (
            <div key={invite.id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <div className="text-slate-200">{invite.invited_email}</div>
                <div className="text-xs text-slate-500">
                  Role: {invite.role} · Expires {new Date(invite.expires_at).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={() => handleRevoke(invite.id)}
                className="bg-slate-700 hover:bg-slate-600 text-xs px-3 py-1 rounded"
              >
                Revoke
              </button>
            </div>
          ))}
          {invites.length === 0 && <div className="text-slate-400">No active invites.</div>}
        </div>
      </div>
    </div>
  );
}
