"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Plus, Play, Pause, Trash2 } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import {
  listWorkflows, activateWorkflow, pauseWorkflow, deleteWorkflow,
} from "@/lib/api-client";
import { WorkflowStatusBadge } from "@/components/shared/status-badge";
import { WorkflowDialog } from "@/components/workflows/workflow-dialog";
import { toast } from "sonner";

export default function WorkflowsPage() {
  const { t } = useTranslation();
  const [createOpen, setCreateOpen] = useState(false);

  const { data: workflows, refresh } = usePolling(() => listWorkflows(), 10000);

  async function handleActivate(id: number) {
    try {
      await activateWorkflow(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handlePause(id: number) {
    try {
      await pauseWorkflow(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handleDelete(id: number) {
    if (!confirm(t("confirm") + "?")) return;
    try {
      await deleteWorkflow(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  const triggerLabel = (type: string) => t(`trigger_${type}`) || type;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("nav_workflows")}</h2>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />{t("wf_create")}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {!workflows || workflows.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("wf_name")}</TableHead>
                  <TableHead>{t("wf_trigger")}</TableHead>
                  <TableHead>{t("contact_status")}</TableHead>
                  <TableHead className="hidden md:table-cell">{t("contact_created")}</TableHead>
                  <TableHead className="text-right">{t("contact_actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflows.map((wf) => (
                  <TableRow key={wf.id}>
                    <TableCell className="font-medium">{wf.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs">{triggerLabel(wf.trigger_type)}</Badge>
                    </TableCell>
                    <TableCell><WorkflowStatusBadge status={wf.status} /></TableCell>
                    <TableCell className="hidden md:table-cell">{wf.created_at?.slice(0, 10)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {(wf.status === "draft" || wf.status === "paused") && (
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleActivate(wf.id)} title={t("wf_activate")}>
                            <Play className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {wf.status === "active" && (
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handlePause(wf.id)} title={t("wf_pause")}>
                            <Pause className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(wf.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <WorkflowDialog open={createOpen} onOpenChange={setCreateOpen} onSuccess={refresh} />
    </div>
  );
}
