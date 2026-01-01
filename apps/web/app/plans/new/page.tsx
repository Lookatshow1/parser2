"use client";

import { useState } from "react";
import { createPlan } from "../../../lib/api";

export default function NewPlanPage() {
  const [url, setUrl] = useState("");
  const [businessDescription, setBusinessDescription] = useState("");
  const [kpi, setKpi] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setNotice(null);
    try {
      await createPlan({
        url,
        business_description: businessDescription || null,
        kpi: kpi || null
      });
      setNotice("Plan created");
      setUrl("");
      setBusinessDescription("");
      setKpi("");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="card max-w-2xl">
      <h1 className="text-xl font-semibold mb-4">Create plan</h1>
      {error && <div className="text-red-400 mb-2">{error}</div>}
      {notice && <div className="text-green-400 mb-2">{notice}</div>}
      <div className="space-y-3">
        <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="Landing URL" />
        <textarea
          value={businessDescription}
          onChange={(event) => setBusinessDescription(event.target.value)}
          placeholder="Business description"
          rows={3}
        />
        <input value={kpi} onChange={(event) => setKpi(event.target.value)} placeholder="KPI" />
        <button onClick={handleSubmit}>Create</button>
      </div>
    </div>
  );
}
