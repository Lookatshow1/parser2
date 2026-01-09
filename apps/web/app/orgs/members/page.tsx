"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  createInvite,
  deleteMember,
  listInvites,
  listMembers,
  resendInvite,
  revokeInvite,
  updateMemberRole,
} from "../../../lib/api";
import { getOrgId, getToken } from "../../../lib/session";
import { ru } from "../../../lib/ru";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "../../../components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../../../components/ui/dropdown-menu";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { Skeleton } from "../../../components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

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
  sent_at?: string | null;
  send_count?: number;
  last_error?: string | null;
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
  const [loading, setLoading] = useState(false);

  const orgId = getOrgId();
  const token = getToken();

  const load = async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const [memberData, inviteData] = await Promise.all([
        listMembers(Number(orgId)),
        listInvites(Number(orgId)),
      ]);
      setMembers(memberData);
      setInvites(inviteData.items);
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
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
      setNotice(`Приглашение создано для ${invite.invited_email}`);
      toast.success("Приглашение создано");
      setEmail("");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleRoleChange = async (userId: number, nextRole: string) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await updateMemberRole(Number(orgId), userId, { role: nextRole });
      toast.success("Роль обновлена");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleRemove = async (userId: number) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await deleteMember(Number(orgId), userId);
      toast.success("Участник удалён");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleRevoke = async (inviteId: number) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await revokeInvite(Number(orgId), inviteId);
      toast.success("Приглашение отозвано");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const handleResend = async (inviteId: number) => {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      await resendInvite(Number(orgId), inviteId, {});
      setNotice("Приглашение отправлено повторно");
      toast.success("Отправлено повторно");
      await load();
    } catch (err) {
      const message = (err as Error).message;
      setError(message);
      toast.error(message);
    }
  };

  const roleLabel = useMemo(() => {
    return (value: string) => ru.roles[value as keyof typeof ru.roles] || value;
  }, []);

  if (!token) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-slate-300">{ru.messages.loginRequired}</p>
          <Link href="/login" className="text-blue-400">{ru.nav.login}</Link>
        </CardContent>
      </Card>
    );
  }

  if (!orgId) {
    return (
      <Card>
        <CardContent className="space-y-2 py-6">
          <p className="text-slate-300">{ru.messages.selectOrg}</p>
          <Link href="/orgs" className="text-blue-400">{ru.nav.orgs}</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{ru.nav.members}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
          {notice && <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{notice}</div>}
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
            <div>Организация #{orgId}</div>
            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm">{ru.actions.invite}</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{ru.actions.invite}</DialogTitle>
                  <DialogDescription>Отправьте приглашение участнику и выберите роль.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="invite-email">{ru.labels.inviteEmail}</Label>
                    <Input
                      id="invite-email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="email@example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="invite-role">{ru.labels.inviteRole}</Label>
                    <select
                      id="invite-role"
                      value={role}
                      onChange={(event) => setRole(event.target.value)}
                      className="h-10 w-full rounded-md border border-slate-800 bg-slate-900 px-3 text-sm"
                    >
                      <option value="member">{ru.roles.member}</option>
                      <option value="admin">{ru.roles.admin}</option>
                    </select>
                  </div>
                  <Button onClick={handleInvite} disabled={!email}>
                    {ru.actions.invite}
                  </Button>
                  {inviteToken && (
                    <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-300">
                      Токен приглашения: <span className="text-slate-100">{inviteToken}</span>
                    </div>
                  )}
                  {joinUrl && (
                    <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-300">
                      Ссылка для вступления: <span className="text-slate-100">{joinUrl}</span>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.members}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && members.length === 0 && <div className="text-sm text-slate-400">{ru.messages.noMembers}</div>}
          {!loading && members.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>{ru.labels.role}</TableHead>
                  <TableHead>{ru.labels.createdAt}</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.user_id}>
                    <TableCell>
                      <div className="font-medium text-slate-100">{member.email}</div>
                      <div className="text-xs text-slate-500">{member.is_you ? "Вы" : ""}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={member.role === "owner" ? "info" : "muted"}>{roleLabel(member.role)}</Badge>
                    </TableCell>
                    <TableCell className="text-slate-400">
                      {new Date(member.joined_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="secondary" size="sm">Действия</Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleRoleChange(member.user_id, "owner")}>Сделать владельцем</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(member.user_id, "admin")}>Сделать админом</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(member.user_id, "member")}>Сделать участником</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleRoleChange(member.user_id, "viewer")}>Сделать наблюдателем</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleRemove(member.user_id)} className="text-red-300">
                            Удалить
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{ru.labels.invites}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && invites.length === 0 && <div className="text-sm text-slate-400">{ru.messages.noInvites}</div>}
          {!loading && invites.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>{ru.labels.role}</TableHead>
                  <TableHead>{ru.labels.inviteExpires}</TableHead>
                  <TableHead>{ru.labels.sendStatus}</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invites.map((invite) => {
                  const sendStatus = invite.sent_at
                    ? ru.inviteStatus.sent
                    : invite.last_error
                      ? ru.inviteStatus.failed
                      : ru.inviteStatus.notSent;
                  return (
                    <TableRow key={invite.id}>
                      <TableCell>
                        <div className="font-medium text-slate-100">{invite.invited_email}</div>
                        <div className="text-xs text-slate-500">Отправок: {invite.send_count ?? 0}</div>
                        {invite.last_error && (
                          <div className="text-xs text-rose-400">Ошибка: {invite.last_error}</div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="muted">{roleLabel(invite.role)}</Badge>
                      </TableCell>
                      <TableCell className="text-slate-400">
                        {new Date(invite.expires_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={invite.last_error ? "danger" : "success"}>{sendStatus}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="secondary" size="sm">Действия</Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleResend(invite.id)}>{ru.actions.resend}</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleRevoke(invite.id)} className="text-red-300">
                              Отозвать
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
