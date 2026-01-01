"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getExperimentReport, ExperimentReport } from "../../../lib/api";

export default function ExperimentReportPage() {
  const params = useParams();
  const id = Number(params?.id);
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getExperimentReport(id);
        setReport(data);
      } catch (err) {
        setError((err as Error).message);
      }
    };
    if (id) {
      load();
    }
  }, [id]);

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-xl font-semibold mb-2">Experiment #{id} report</h1>
        {error && <div className="text-red-400">{error}</div>}
        {report && (
          <div className="text-sm text-slate-300">Status: {report.status}</div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Metrics</h2>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-400">
              <tr>
                <th className="py-2">Date</th>
                <th>Platform</th>
                <th>Impressions</th>
                <th>Clicks</th>
                <th>Spend</th>
              </tr>
            </thead>
            <tbody>
              {report?.metrics.map((metric, index) => (
                <tr key={index} className="border-b border-slate-800">
                  <td className="py-2">{metric.date}</td>
                  <td>{metric.platform}</td>
                  <td>{metric.impressions}</td>
                  <td>{metric.clicks}</td>
                  <td>{metric.spend}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {report && report.metrics.length === 0 && (
            <div className="text-slate-400 py-2">No metrics yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
