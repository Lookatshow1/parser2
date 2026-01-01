"use client";

import { useEffect, useState } from "react";
import { createConnection, listConnections, testConnection, ConnectionResponse } from "../../lib/api";

const platforms = ["yandex", "ozon", "vk"];

export default function ConnectionsPage() {
  const [items, setItems] = useState<ConnectionResponse[]>([]);
  const [platform, setPlatform] = useState("yandex");
  const [credentialsJson, setCredentialsJson] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await listConnections();
      setItems(data.items);
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
      const credentials = JSON.parse(credentialsJson);
      await createConnection({ platform, credentials_json: credentials });
      setNotice("Connection created");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleTest = async (connectionId: number) => {
    setError(null);
    setNotice(null);
    try {
      const result = await testConnection(connectionId);
      setNotice(result.ok ? "Connection OK" : "Connection failed");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-xl font-semibold mb-4">Connections</h1>
        {error && <div className="text-red-400 mb-2">{error}</div>}
        {notice && <div className="text-green-400 mb-2">{notice}</div>}
        <div className="grid gap-3 md:grid-cols-3">
          <select value={platform} onChange={(event) => setPlatform(event.target.value)}>
            {platforms.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <input
            value={credentialsJson}
            onChange={(event) => setCredentialsJson(event.target.value)}
            placeholder='{"token":"..."}'
          />
          <div className="flex gap-2">
            <button onClick={handleCreate}>Create</button>
            <button onClick={handleTest} className="bg-slate-700 hover:bg-slate-600">
              Test
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Existing connections</h2>
        <div className="grid gap-2 text-sm">
          {items.map((item) => (
            <div key={item.id} className="flex justify-between border-b border-slate-800 pb-2">
              <span>#{item.id}</span>
              <span>{item.platform}</span>
              <span>{item.status}</span>
              <button
                onClick={() => handleTest(item.id)}
                className="bg-slate-700 hover:bg-slate-600 text-xs px-3 py-1 rounded"
              >
                Test
              </button>
            </div>
          ))}
          {items.length === 0 && <div className="text-slate-400">No connections yet.</div>}
        </div>
      </div>
    </div>
  );
}
