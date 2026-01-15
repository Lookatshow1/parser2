"use client";
export const dynamic = "force-dynamic";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import { getExperimentReport, ExperimentReport } from "../../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";

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
        const message = (err as Error).message;
        setError(message);
        toast.error(message);
      }
    };
    if (id) {
      load();
    }
  }, [id]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Отчёт эксперимента #{id}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
          {report && <div className="text-sm text-muted">Статус: {report.status}</div>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Метрики</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Дата</TableHead>
                <TableHead>Платформа</TableHead>
                <TableHead>Показы</TableHead>
                <TableHead>Клики</TableHead>
                <TableHead>Расход</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {report?.metrics.map((metric, index) => (
                <TableRow key={index}>
                  <TableCell>{metric.date}</TableCell>
                  <TableCell>{metric.platform}</TableCell>
                  <TableCell>{metric.impressions}</TableCell>
                  <TableCell>{metric.clicks}</TableCell>
                  <TableCell>{metric.spend}</TableCell>
                </TableRow>
              ))}
              {report && report.metrics.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted">Данных пока нет.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
