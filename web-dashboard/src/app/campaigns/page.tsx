"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Play, Pause, XCircle, BarChart3 } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import {
  listCampaigns, sendCampaign, pauseCampaign, cancelCampaign,
} from "@/lib/api-client";
import { CampaignStatusBadge } from "@/components/shared/status-badge";
import { CampaignDialog } from "@/components/campaigns/campaign-dialog";
import { toast } from "sonner";
import type { CampaignResponse } from "@/lib/api-types";
import Link from "next/link";

export default function CampaignsPage() {
  const { t } = useTranslation();
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);

  const { data: campaigns, refresh } = usePolling(() => listCampaigns(), 10000);

  const filtered = campaigns?.filter(
    (c) => !statusFilter || c.status === statusFilter
  ) ?? [];

  async function handleSend(id: number) {
    if (!confirm(t("camp_confirm_send"))) return;
    try {
      await sendCampaign(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handlePause(id: number) {
    try {
      await pauseCampaign(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handleCancel(id: number) {
    if (!confirm(t("camp_confirm_cancel"))) return;
    try {
      await cancelCampaign(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder={t("status_all")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">{t("status_all")}</SelectItem>
            <SelectItem value="draft">{t("status_draft")}</SelectItem>
            <SelectItem value="scheduled">{t("status_scheduled")}</SelectItem>
            <SelectItem value="sending">{t("status_sending")}</SelectItem>
            <SelectItem value="sent">{t("status_sent")}</SelectItem>
            <SelectItem value="paused">{t("status_paused")}</SelectItem>
            <SelectItem value="cancelled">{t("status_cancelled")}</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />{t("camp_create")}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("camp_name")}</TableHead>
                  <TableHead>{t("camp_status")}</TableHead>
                  <TableHead className="hidden md:table-cell">{t("camp_sender")}</TableHead>
                  <TableHead className="hidden lg:table-cell text-right">{t("camp_sent")}</TableHead>
                  <TableHead className="hidden lg:table-cell text-right">{t("camp_opened")}</TableHead>
                  <TableHead className="hidden lg:table-cell text-right">{t("camp_clicked")}</TableHead>
                  <TableHead className="text-right">{t("contact_actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">
                      <Link href={`/campaigns/${c.id}`} className="hover:underline">{c.name}</Link>
                    </TableCell>
                    <TableCell><CampaignStatusBadge status={c.status} /></TableCell>
                    <TableCell className="hidden md:table-cell">{c.sender_email}</TableCell>
                    <TableCell className="hidden lg:table-cell text-right">{c.sent_count}/{c.total_recipients}</TableCell>
                    <TableCell className="hidden lg:table-cell text-right">{c.open_count}</TableCell>
                    <TableCell className="hidden lg:table-cell text-right">{c.click_count}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {c.status === "draft" && (
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleSend(c.id)} title={t("camp_send")}>
                            <Play className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {c.status === "sending" && (
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handlePause(c.id)} title={t("camp_pause")}>
                            <Pause className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {(c.status === "draft" || c.status === "sending" || c.status === "paused") && (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleCancel(c.id)} title={t("camp_cancel")}>
                            <XCircle className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Link href={`/campaigns/${c.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8" title={t("camp_stats")}>
                            <BarChart3 className="h-3.5 w-3.5" />
                          </Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <CampaignDialog open={createOpen} onOpenChange={setCreateOpen} onSuccess={refresh} />
    </div>
  );
}
