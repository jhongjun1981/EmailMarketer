"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { createCampaign, listTemplates, listSegments } from "@/lib/api-client";
import type { TemplateResponse, SegmentResponse } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function CampaignDialog({ open, onOpenChange, onSuccess }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [segmentId, setSegmentId] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [senderName, setSenderName] = useState("");
  const [replyTo, setReplyTo] = useState("");
  const [rateLimit, setRateLimit] = useState("5");
  const [saving, setSaving] = useState(false);

  const [templates, setTemplates] = useState<TemplateResponse[]>([]);
  const [segments, setSegments] = useState<SegmentResponse[]>([]);

  useEffect(() => {
    if (open) {
      listTemplates().then(setTemplates).catch(() => {});
      listSegments().then(setSegments).catch(() => {});
      setName("");
      setTemplateId("");
      setSegmentId("");
      setSenderEmail("");
      setSenderName("");
      setReplyTo("");
      setRateLimit("5");
    }
  }, [open]);

  async function handleSave() {
    if (!name.trim() || !templateId || !senderEmail.trim()) return;
    setSaving(true);
    try {
      await createCampaign({
        name,
        template_id: Number(templateId),
        segment_id: segmentId ? Number(segmentId) : undefined,
        sender_email: senderEmail,
        sender_name: senderName || undefined,
        reply_to: replyTo || undefined,
        rate_limit: Number(rateLimit) || 5,
      });
      toast.success(t("success"));
      onOpenChange(false);
      onSuccess();
    } catch {
      toast.error(t("error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("camp_create")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>{t("camp_name")}</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>{t("camp_template")}</Label>
              <Select value={templateId} onValueChange={setTemplateId}>
                <SelectTrigger><SelectValue placeholder="—" /></SelectTrigger>
                <SelectContent>
                  {templates.map((tpl) => (
                    <SelectItem key={tpl.id} value={String(tpl.id)}>{tpl.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>{t("camp_segment")}</Label>
              <Select value={segmentId} onValueChange={setSegmentId}>
                <SelectTrigger><SelectValue placeholder={t("camp_segment_all")} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t("camp_segment_all")}</SelectItem>
                  {segments.map((seg) => (
                    <SelectItem key={seg.id} value={String(seg.id)}>{seg.name} ({seg.contact_count})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>{t("camp_sender")}</Label>
              <Input value={senderEmail} onChange={(e) => setSenderEmail(e.target.value)} placeholder="noreply@example.com" />
            </div>
            <div className="space-y-1.5">
              <Label>{t("camp_sender_name")}</Label>
              <Input value={senderName} onChange={(e) => setSenderName(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>{t("camp_reply_to")}</Label>
              <Input value={replyTo} onChange={(e) => setReplyTo(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>{t("camp_rate_limit")}</Label>
              <Input type="number" value={rateLimit} onChange={(e) => setRateLimit(e.target.value)} min={1} max={100} />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
            <Button onClick={handleSave} disabled={saving || !name.trim() || !templateId || !senderEmail.trim()}>
              {saving ? t("loading") : t("save")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
