"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, RefreshCw, Trash2, Pencil, Users } from "lucide-react";
import { toast } from "sonner";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import { listSegments, deleteSegment, refreshSegment } from "@/lib/api-client";
import { SegmentDialog } from "@/components/segments/segment-dialog";
import type { SegmentResponse } from "@/lib/api-types";

export default function SegmentsPage() {
  const { t } = useTranslation();
  const { data: segments, refresh } = usePolling(() => listSegments(), 10000);
  const [createOpen, setCreateOpen] = useState(false);
  const [editSeg, setEditSeg] = useState<SegmentResponse | null>(null);

  async function handleDelete(id: number) {
    try {
      await deleteSegment(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  async function handleRefresh(id: number) {
    try {
      const res = await refreshSegment(id);
      toast.success(res.message);
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("nav_segments")}</h2>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />{t("seg_create")}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {!segments || segments.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("seg_name")}</TableHead>
                  <TableHead>{t("seg_desc")}</TableHead>
                  <TableHead>{t("seg_type")}</TableHead>
                  <TableHead className="text-right">{t("seg_contacts")}</TableHead>
                  <TableHead className="text-right">{t("contact_actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {segments.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{s.name}</TableCell>
                    <TableCell className="text-muted-foreground">{s.description || "—"}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {s.is_dynamic ? t("seg_type_dynamic") : t("seg_type_static")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Users className="h-3.5 w-3.5 text-muted-foreground" />
                        {s.contact_count}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {s.is_dynamic && (
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleRefresh(s.id)}>
                            <RefreshCw className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setEditSeg(s)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(s.id)}>
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

      <SegmentDialog open={createOpen} onOpenChange={setCreateOpen} segment={null} onSuccess={refresh} />
      <SegmentDialog
        open={!!editSeg}
        onOpenChange={(open) => { if (!open) setEditSeg(null); }}
        segment={editSeg}
        onSuccess={refresh}
      />
    </div>
  );
}
