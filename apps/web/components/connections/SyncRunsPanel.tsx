"use client";

import { STR } from "@/lib/strings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const syncStatusVariant: Record<string, "success" | "danger" | "warning" | "muted"> = {
    success: "success",
    failed: "danger",
    running: "warning",
    queued: "warning",
};

const formatStatus = (value?: string | null) => {
    if (!value) return "—";
    return STR.statuses[value as keyof typeof STR.statuses] || value;
};

interface SyncRun {
    id: number;
    status: string;
    run_type: string;
    created_at: string;
    result_json?: Record<string, unknown>;
    error_text?: string | null;
}

interface SyncRunsPanelProps {
    syncRuns: SyncRun[];
    loading: boolean;
    selectedConnectionId: number | null;
    dateFrom: string;
    dateTo: string;
    onConnectionIdChange: (id: number | null) => void;
    onDateFromChange: (date: string) => void;
    onDateToChange: (date: string) => void;
    onSync: () => void;
    onRefreshRuns: () => void;
    onRefreshMetrics: () => void;
}

export function SyncRunsPanel({
    syncRuns,
    loading,
    selectedConnectionId,
    dateFrom,
    dateTo,
    onConnectionIdChange,
    onDateFromChange,
    onDateToChange,
    onSync,
    onRefreshRuns,
    onRefreshMetrics,
}: SyncRunsPanelProps) {
    return (
        <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
                <Input
                    type="number"
                    placeholder="ID подключения"
                    value={selectedConnectionId ?? ""}
                    onChange={(e) => onConnectionIdChange(Number(e.target.value) || null)}
                />
                <Input type="date" value={dateFrom} onChange={(e) => onDateFromChange(e.target.value)} />
                <Input type="date" value={dateTo} onChange={(e) => onDateToChange(e.target.value)} />
            </div>
            <div className="flex flex-wrap gap-2">
                <Button onClick={onSync}>{STR.actions.sync}</Button>
                {selectedConnectionId && (
                    <>
                        <Button variant="secondary" onClick={onRefreshRuns}>
                            Обновить синки
                        </Button>
                        <Button variant="secondary" onClick={onRefreshMetrics}>
                            Обновить метрики
                        </Button>
                    </>
                )}
            </div>
            {loading ? (
                <Skeleton className="h-16 w-full" />
            ) : (
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>Тип</TableHead>
                            <TableHead>{STR.labels.status}</TableHead>
                            <TableHead>Создан</TableHead>
                            <TableHead>Результат</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {syncRuns.map((run) => (
                            <TableRow key={run.id}>
                                <TableCell>#{run.id}</TableCell>
                                <TableCell>{run.run_type}</TableCell>
                                <TableCell>
                                    <Badge variant={syncStatusVariant[run.status] || "muted"}>{formatStatus(run.status)}</Badge>
                                </TableCell>
                                <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                                <TableCell className="text-muted">
                                    {run.result_json && "inserted" in run.result_json
                                        ? `${run.result_json.inserted}/${run.result_json.updated}/${run.result_json.unchanged}`
                                        : run.error_text
                                            ? String(run.error_text).slice(0, 80)
                                            : "—"}
                                </TableCell>
                            </TableRow>
                        ))}
                        {syncRuns.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center text-muted">
                                    Синхронизаций пока нет.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            )}
        </div>
    );
}
