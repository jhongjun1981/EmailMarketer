"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { batchImportContacts, listSegments } from "@/lib/api-client";
import type { SegmentResponse } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function ImportDialog({ open, onOpenChange, onSuccess }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [segmentId, setSegmentId] = useState<string>("");
  const [segments, setSegments] = useState<SegmentResponse[]>([]);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    if (open) {
      listSegments().then(setSegments).catch(() => {});
      setText("");
      setSegmentId("");
    }
  }, [open]);

  const lines = text.trim().split("\n").filter((l) => l.trim());

  async function handleImport() {
    if (lines.length === 0) return;
    setImporting(true);
    try {
      const contacts = lines.map((line) => {
        const parts = line.split(",").map((s) => s.trim());
        return {
          email: parts[0],
          name: parts[1] || "",
          company: parts[2] || "",
          source: "import",
        };
      });
      const req = {
        contacts,
        ...(segmentId ? { segment_id: Number(segmentId) } : {}),
      };
      const result = await batchImportContacts(req);
      toast.success(
        t("contact_import_result")
          .replace("{created}", String(result.created))
          .replace("{skipped}", String(result.skipped))
      );
      onOpenChange(false);
      onSuccess();
    } catch {
      toast.error(t("error"));
    } finally {
      setImporting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("contact_import")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>{t("contact_import_hint")}</Label>
            <Textarea
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={"user1@example.com,John,Acme\nuser2@example.com"}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">{lines.length} emails</p>
          </div>
          <div className="space-y-1.5">
            <Label>{t("camp_segment")}</Label>
            <Select value={segmentId} onValueChange={setSegmentId}>
              <SelectTrigger><SelectValue placeholder="—" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">—</SelectItem>
                {segments.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
            <Button onClick={handleImport} disabled={importing || lines.length === 0}>
              {importing ? t("loading") : t("confirm")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
