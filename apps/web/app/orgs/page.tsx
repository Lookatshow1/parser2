"use client";

import { useEffect, useState } from "react";
import { createOrg, getActiveOrg, listOrgs, switchOrg } from "../../lib/api";
import { getOrgId, setOrgId } from "../../lib/session";

type Org = { id: number; name: string };

export default function OrgsPage() {
  const [items, setItems] = useState<Org[]>([]);
  const [activeOrg, setActiveOrg] = useState<Org | null>(null);
  const [name, setName] = useState("My Org");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await listOrgs();
      setItems(data.items);
      try {
        const active = await getActiveOrg();
        setActiveOrg(active);
      } catch {
        setActiveOrg(null);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    setError(null);
    setNotice(null);
    try {
      const org = await createOrg({ name });
      setOrgId(String(org.id));
      setActiveOrg(org);
      setNotice(`Created and selected org ${org.name}`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleSwitch = async (org: Org) => {
    setError(null);
    setNotice(null);
    try {
      await switchOrg({ organization_id: org.id });
      setOrgId(String(org.id));
      setActiveOrg(org);
      setNotice(`Switched to ${org.name}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Organizations</h1>
        {error && <div className="text-red-400">{error}</div>}
        {notice && <div className="text-green-400">{notice}</div>}
        <div className="text-sm text-slate-400">
          Active org: {activeOrg ? `${activeOrg.name} (#${activeOrg.id})` : "not set"}
        </div>
        <div className="flex gap-2">
          <input value={name} onChange={(event) => setName(event.target.value)} />
          <button onClick={handleCreate}>Create</button>
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="text-lg font-semibold">Your orgs</h2>
        <div className="grid gap-2 text-sm">
          {items.map((org) => (
            <div key={org.id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span>#{org.id}</span>
              <span>{org.name}</span>
              <button
                onClick={() => handleSwitch(org)}
                className="bg-slate-700 hover:bg-slate-600 text-xs px-3 py-1 rounded"
              >
                Select
              </button>
            </div>
          ))}
          {items.length === 0 && <div className="text-slate-400">No organizations yet.</div>}
        </div>
      </div>

      <div className="card text-sm text-slate-400">
        Stored org in browser: {getOrgId() || "none"}
      </div>
    </div>
  );
}
