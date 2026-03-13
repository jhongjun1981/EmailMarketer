"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { createTemplate, updateTemplate } from "@/lib/api-client";
import type { TemplateResponse } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template: TemplateResponse | null;
  onSuccess: () => void;
}

function extractVariables(html: string): string[] {
  const matches = html.match(/\{\{(\w+)\}\}/g);
  if (!matches) return [];
  return [...new Set(matches.map((m) => m.replace(/\{|\}/g, "")))];
}

export function TemplateEditor({ open, onOpenChange, template, onSuccess }: Props) {
  const { t } = useTranslation();
  const isEdit = !!template;
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("general");
  const [htmlBody, setHtmlBody] = useState("");
  const [textBody, setTextBody] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (template) {
      setName(template.name);
      setSubject(template.subject);
      setCategory(template.category);
      setHtmlBody(template.html_body);
      setTextBody(template.text_body);
    } else {
      setName("");
      setSubject("");
      setCategory("general");
      setHtmlBody("");
      setTextBody("");
    }
  }, [template, open]);

  const variables = extractVariables(htmlBody + subject);

  async function handleSave() {
    if (!name.trim() || !subject.trim()) return;
    setSaving(true);
    try {
      const data = { name, subject, html_body: htmlBody, text_body: textBody, category, variables };
      if (isEdit) {
        await updateTemplate(template!.id, data);
      } else {
        await createTemplate(data);
      }
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
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? t("tpl_edit") : t("tpl_create")}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>{t("tpl_name")}</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("tpl_category")}</Label>
                <Input value={category} onChange={(e) => setCategory(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>{t("tpl_subject")}</Label>
              <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>{t("tpl_html_body")}</Label>
              <Textarea
                rows={16}
                value={htmlBody}
                onChange={(e) => setHtmlBody(e.target.value)}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label>{t("tpl_text_body")}</Label>
              <Textarea rows={4} value={textBody} onChange={(e) => setTextBody(e.target.value)} className="font-mono text-sm" />
            </div>
            {variables.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-muted-foreground">{t("tpl_variables")}:</span>
                {variables.map((v) => (
                  <Badge key={v} variant="secondary" className="text-xs">{`{{${v}}}`}</Badge>
                ))}
              </div>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
              <Button onClick={handleSave} disabled={saving || !name.trim() || !subject.trim()}>
                {saving ? t("loading") : t("save")}
              </Button>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>{t("tpl_preview")}</Label>
            <div className="border rounded-md overflow-hidden bg-white" style={{ minHeight: 400 }}>
              <iframe
                srcDoc={htmlBody || "<p style='color:#999;padding:20px;'>Preview</p>"}
                className="w-full h-full min-h-[400px]"
                sandbox=""
                title="preview"
              />
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
