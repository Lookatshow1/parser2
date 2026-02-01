"use client";

import { ConnectionResponse } from "@/lib/api";
import { STR } from "@/lib/strings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useRouter } from "next/navigation";

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

interface ConnectionListProps {
    items: ConnectionResponse[];
    loading: boolean;
    syncingId: number | null;
    selectedConnectionId: number | null;
    onSelect: (id: number) => void;
    onSync: (id: number) => void;
    onTest: (id: number) => void;
    onToggleAutoSync: (id: number, enabled: boolean) => void;
    onCreate: () => void;
}

export function ConnectionList({
    items,
    loading,
    syncingId,
    onSelect,
    onSync,
    onTest,
    onToggleAutoSync,
    onCreate,
}: ConnectionListProps) {
    const router = useRouter();

    if (loading) {
        return <Skeleton className="h-20 w-full" />;
    }

    if (items.length === 0) {
        return (
            <EmptyState
                title={STR.messages.noConnections}
                description={STR.pages.connectionsEmptyDesc}
                action={<Button size="sm" onClick={onCreate}>{STR.actions.create}</Button>}
            />
        );
    }

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>{STR.labels.platform}</TableHead>
                    <TableHead>{STR.labels.status}</TableHead>
                    <TableHead>Последний синк</TableHead>
                    <TableHead>Автосинк</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {items.map((item) => (
                    <TableRow key={item.id}>
                        <TableCell>#{item.id}</TableCell>
                        <TableCell>
                            <div className="flex items-center gap-2">
                                <span className="capitalize">{item.platform}</span>
                                {item.name?.toLowerCase().includes("демо") && <Badge variant="info">Демо</Badge>}
                            </div>
                        </TableCell>
                        <TableCell>
                            <Badge variant={syncStatusVariant[item.last_sync_status || ""] || "muted"}>
                                {formatStatus(item.last_sync_status)}
                            </Badge>
                        </TableCell>
                        <TableCell className="text-muted">
                            {item.last_sync_finished_at ?? "—"}
                        </TableCell>
                        <TableCell className="text-muted">
                            {item.auto_sync_enabled ? `Да (${item.auto_sync_every_minutes ?? 0}м / ${item.auto_sync_window_days ?? 0}д)` : "Нет"}
                        </TableCell>
                        <TableCell className="text-right">
                            <div className="flex flex-wrap justify-end gap-2">
                                <Button variant="secondary" size="sm" onClick={() => onSelect(item.id)}>
                                    {STR.actions.open}
                                </Button>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => onSync(item.id)}
                                    disabled={syncingId === item.id || item.last_sync_status === "queued" || item.last_sync_status === "running"}
                                >
                                    {item.platform === "yandex" ? STR.actions.runDemo : STR.actions.sync}
                                </Button>
                                <Button variant="secondary" size="sm" onClick={() => onToggleAutoSync(item.id, !item.auto_sync_enabled)}>
                                    {item.auto_sync_enabled ? "Выключить авто" : "Включить авто"}
                                </Button>
                                <Button variant="secondary" size="sm" onClick={() => onTest(item.id)}>
                                    {STR.actions.check}
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => router.push(`/connections/${item.id}`)}>
                                    Детали
                                </Button>
                            </div>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
