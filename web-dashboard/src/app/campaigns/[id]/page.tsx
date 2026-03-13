"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Play, Pause, XCircle } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import {
  getCampaignStats, getCampaignLogs,
  sendCampaign, pauseCampaign, cancelCampaign,
} from "@/lib/api-client";
import { CampaignStatusBadge } from "@/components/shared/status-badge";
import { Pagination } from "@/components/shared/pagination";
import { toast } from "sonner";
import Link from "next/link";

export default function CampaignDetailPage() {
  const { t } = useTranslation();
  const params = useParams();
  const id = Number(params.id);
  const [logPage, setLogPage] = useState(1);

  const { data: stats, refresh: refreshStats } = usePolling(
    useCallback(() => getCampaignStats(id), [id]),
    5000,
  );

  const { data: logs, refresh: refreshLogs } = usePolling(
    useCallback(() => getCampaignLogs(id, logPage, 50), [id, logPage]),
    10000,
  );

  async function handleSend() {
    if (!confirm(t("camp_confirm_send"))) return;
    try {
      await sendCampaign(id);
      toast.success(t("success"));
      refreshStats();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handlePause() {
    try {
      await pauseCampaign(id);
      toast.success(t("success"));
      refreshStats();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handleCancel() {
    if (!confirm(t("camp_confirm_cancel"))) return;
    try {
      await cancelCampaign(id);
      toast.success(t("success"));
      refreshStats();
    } catch {
      toast.error(t("error"));
    }
  }

  const pct = (n: number, d: number) => d > 0 ? `${(n / d * 100).toFixed(1)}%` : "0%";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/campaigns">
            <Button variant="ghost" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
          </Link>
          <div>
            <h2 className="text-lg font-semibold">{stats?.name ?? `#${id}`}</h2>
            {stats && <CampaignStatusBadge status={stats.status} />}
          </div>
        </div>
        {stats && (
          <div className="flex gap-2">
            {stats.status === "draft" && (
              <Button size="sm" onClick={handleSend}><Play className="h-3.5 w-3.5 mr-1" />{t("camp_send")}</Button>
            )}
            {stats.status === "sending" && (
              <Button size="sm" variant="outline" onClick={handlePause}><Pause className="h-3.5 w-3.5 mr-1" />{t("camp_pause")}</Button>
            )}
            {["draft", "sending", "paused"].includes(stats.status) && (
              <Button size="sm" variant="destructive" onClick={handleCancel}><XCircle className="h-3.5 w-3.5 mr-1" />{t("camp_cancel")}</Button>
            )}
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: t("camp_total"), value: stats.total },
            { label: t("camp_sent"), value: stats.sent },
            { label: t("camp_opened"), value: `${stats.opened} (${pct(stats.opened, stats.sent)})` },
            { label: t("camp_clicked"), value: `${stats.clicked} (${pct(stats.clicked, stats.sent)})` },
            { label: t("camp_bounced"), value: stats.bounced },
            { label: t("camp_unsub"), value: stats.unsubscribed },
          ].map((s) => (
            <Card key={s.label}>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className="text-xl font-bold mt-1">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Logs */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{t("camp_logs")}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {!logs || logs.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("contact_email")}</TableHead>
                  <TableHead>{t("contact_status")}</TableHead>
                  <TableHead className="hidden md:table-cell">{t("camp_sent")}</TableHead>
                  <TableHead className="hidden lg:table-cell">{t("camp_opened")}</TableHead>
                  <TableHead className="hidden lg:table-cell text-right">{t("camp_clicked")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">{log.email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{log.status}</Badge>
                    </TableCell>
                    <TableCell className="hidden md:table-cell">{log.sent_at?.slice(0, 19).replace("T", " ") ?? "—"}</TableCell>
                    <TableCell className="hidden lg:table-cell">{log.opened_at?.slice(0, 19).replace("T", " ") ?? "—"}</TableCell>
                    <TableCell className="hidden lg:table-cell text-right">{log.click_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {logs && logs.length >= 50 && (
        <Pagination page={logPage} pageSize={50} total={logPage * 50 + 1} onPageChange={setLogPage} />
      )}
    </div>
  );
}
