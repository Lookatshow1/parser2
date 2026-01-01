"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  createExperiment,
  listExperiments,
  listPlans,
  startExperiment,
  ExperimentListItem,
  PlanResponse
} from "../../lib/api";

export default function ExperimentsPage() {
  const [items, setItems] = useState<ExperimentListItem[]>([]);
  const [plans, setPlans] = useState<PlanResponse[]>([]);
  const [planId, setPlanId] = useState("");
  const [budget, setBudget] = useState("10000");
  const [platforms, setPlatforms] = useState("yandex,ozon,vk");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    try {
      const [experimentsData, plansData] = await Promise.all([listExperiments(), listPlans()]);
      setItems(experimentsData.items);
      setPlans(plansData.items);
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
      if (!planId) {
        setError("Select a plan before starting an experiment.");
        return;
      }
      const experiment = await createExperiment({
        plan_id: Number(planId),
        budget: Number(budget),
        platforms: platforms.split(",").map((item) => item.trim())
      });
      await startExperiment(experiment.id);
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
          <select value={planId} onChange={(event) => setPlanId(event.target.value)}>
            <option value="">Select plan</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>
                {plan.id} - {plan.url}
              </option>
            ))}
          </select>
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
              <span>Plan {item.plan_id ?? "-"}</span>
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
