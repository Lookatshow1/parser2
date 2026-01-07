"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAuditEvents, OrgAuditEvent } from "../../../lib/api";
import { getOrgId, getToken } from "../../../lib/session";

export default function OrgAuditPage() {
  const [items, setItems] = useState<OrgAuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const orgId = getOrgId();
  const token = getToken();

  const load = async () => {
    if (!orgId) return;
    try {
      const data = await listAuditEvents(Number(orgId), { limit: 50, offset: 0 });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, [orgId]);

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
      <div className="card space-y-2">
        <h1 className="text-xl font-semibold">Audit log</h1>
        <div className="text-sm text-slate-400">Org #{orgId} · {total} events</div>
        {error && <div className="text-red-400">{error}</div>}
      </div>
      <div className="card space-y-3">
        <div className="grid gap-2 text-sm">
          {items.map((event) => (
            <div key={event.id} className="border-b border-slate-800 pb-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-200">{event.action}</span>
                <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
              </div>
              <div className="text-xs text-slate-500">
                subject: {event.subject_type || "-"} #{event.subject_id ?? "-"} · actor {event.actor_user_id ?? "system"}
              </div>
              {event.meta && Object.keys(event.meta).length > 0 && (
                <pre className="text-xs text-slate-300 whitespace-pre-wrap">
                  {JSON.stringify(event.meta, null, 2)}
                </pre>
              )}
            </div>
          ))}
          {items.length === 0 && <div className="text-slate-400">No audit events yet.</div>}
        </div>
      </div>
    </div>
  );
}
