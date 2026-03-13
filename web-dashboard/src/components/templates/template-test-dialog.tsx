"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { testSendTemplate } from "@/lib/api-client";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId: number;
  variables: string[];
}

export function TemplateTestDialog({ open, onOpenChange, templateId, variables }: Props) {
  const { t } = useTranslation();
  const [toEmail, setToEmail] = useState("");
  const [varData, setVarData] = useState<Record<string, string>>({});
  const [sending, setSending] = useState(false);

  async function handleSend() {
    if (!toEmail.trim()) return;
    setSending(true);
    try {
      await testSendTemplate(templateId, toEmail, varData);
      toast.success(t("success"));
      onOpenChange(false);
    } catch {
      toast.error(t("error"));
    } finally {
      setSending(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t("tpl_test_send")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>{t("tpl_test_to")}</Label>
            <Input value={toEmail} onChange={(e) => setToEmail(e.target.value)} placeholder="test@example.com" />
          </div>
          {variables.length > 0 && (
            <div className="space-y-3">
              <Label>{t("tpl_sample_data")}</Label>
              {variables.map((v) => (
                <div key={v} className="flex items-center gap-2">
                  <span className="text-xs min-w-[80px] text-muted-foreground">{`{{${v}}}`}</span>
                  <Input
                    value={varData[v] || ""}
                    onChange={(e) => setVarData((prev) => ({ ...prev, [v]: e.target.value }))}
                    className="h-8"
                  />
                </div>
              ))}
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
            <Button onClick={handleSend} disabled={sending || !toEmail.trim()}>
              {sending ? t("loading") : t("confirm")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
