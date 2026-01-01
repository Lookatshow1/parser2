"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listExperiments, startExperiment, startExperimentRun, ExperimentListItem } from "../../lib/api";

export default function ExperimentsPage() {
  const [items, setItems] = useState<ExperimentListItem[]>([]);
  const [projectId, setProjectId] = useState("");
  const [budget, setBudget] = useState("10000");
  const [platforms, setPlatforms] = useState("yandex,ozon,vk");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await listExperiments();
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
      const experiment = await startExperiment({
        project_id: Number(projectId),
        total_budget: Number(budget),
        platforms: platforms.split(",").map((item) => item.trim())
      });
      await startExperimentRun(experiment.id);
      setNotice(`Experiment ${experiment.id} started`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-xl font-semibold mb-4">Experiments</h1>
        {error && <div className="text-red-400 mb-2">{error}</div>}
        {notice && <div className="text-green-400 mb-2">{notice}</div>}
        <div className="grid gap-3 md:grid-cols-3">
          <input
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
            placeholder="Project ID"
          />
          <input value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="Total budget" />
          <input
            value={platforms}
            onChange={(event) => setPlatforms(event.target.value)}
            placeholder="Platforms (comma-separated)"
          />
          <button onClick={handleCreate}>Create & Start</button>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Existing experiments</h2>
        <div className="grid gap-2 text-sm">
          {items.map((item) => (
            <div key={item.id} className="flex justify-between border-b border-slate-800 pb-2">
              <span>#{item.id}</span>
              <span>{item.status}</span>
              <span>Project {item.project_id ?? "-"}</span>
              <Link className="text-blue-400" href={`/experiments/${item.id}`}>
                Report
              </Link>
            </div>
          ))}
          {items.length === 0 && <div className="text-slate-400">No experiments yet.</div>}
        </div>
      </div>
    </div>
  );
}
