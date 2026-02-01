"use client";

import { STR } from "@/lib/strings";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface MetricsTableProps {
    metrics: Array<Record<string, unknown>>;
    loading: boolean;
}

export function MetricsTable({ metrics, loading }: MetricsTableProps) {
    if (loading) {
        return <Skeleton className="h-16 w-full" />;
    }

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Дата</TableHead>
                    <TableHead>Показы</TableHead>
                    <TableHead>Клики</TableHead>
                    <TableHead>Расход</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {metrics.map((row, idx) => (
                    <TableRow key={idx}>
                        <TableCell>{String(row.date || "")}</TableCell>
                        <TableCell>{String(row.impressions || 0)}</TableCell>
                        <TableCell>{String(row.clicks || 0)}</TableCell>
                        <TableCell>{String(row.spend || 0)}</TableCell>
                    </TableRow>
                ))}
                {metrics.length === 0 && (
                    <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted">
                            {STR.messages.noMetrics}
                        </TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );
}
