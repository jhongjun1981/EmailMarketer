"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { createWorkflow, listTemplates, listSegments } from "@/lib/api-client";
import type { TemplateResponse, SegmentResponse, WorkflowStepData } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const TRIGGER_TYPES = ["contact_added", "email_opened", "link_clicked", "date_field", "manual"];
const ACTION_TYPES = ["send_email", "wait", "condition", "add_to_segment", "remove_from_segment", "update_contact"];

export function WorkflowDialog({ open, onOpenChange, onSuccess }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [triggerType, setTriggerType] = useState("contact_added");
  const [steps, setSteps] = useState<WorkflowStepData[]>([]);
  const [saving, setSaving] = useState(false);

  const [templates, setTemplates] = useState<TemplateResponse[]>([]);
  const [segments, setSegments] = useState<SegmentResponse[]>([]);

  useEffect(() => {
    if (open) {
      listTemplates().then(setTemplates).catch(() => {});
      listSegments().then(setSegments).catch(() => {});
      setName("");
      setDescription("");
      setTriggerType("contact_added");
      setSteps([]);
    }
  }, [open]);

  function addStep() {
    setSteps([...steps, { action_type: "send_email", config: {} }]);
  }

  function removeStep(index: number) {
    setSteps(steps.filter((_, i) => i !== index));
  }

  function updateStep(index: number, field: string, value: unknown) {
    setSteps(steps.map((s, i) => {
      if (i !== index) return s;
      if (field === "action_type") return { action_type: value as string, config: {} };
      return { ...s, config: { ...s.config, [field]: value } };
    }));
  }

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await createWorkflow({
        name,
        description: description || undefined,
        trigger_type: triggerType,
        steps,
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
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t("wf_create")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>{t("wf_name")}</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>{t("wf_trigger")}</Label>
              <Select value={triggerType} onValueChange={setTriggerType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TRIGGER_TYPES.map((tt) => (
                    <SelectItem key={tt} value={tt}>{t(`trigger_${tt}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>{t("wf_desc")}</Label>
            <Textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>

          {/* Steps */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t("wf_steps")}</Label>
              <Button variant="outline" size="sm" onClick={addStep}>
                <Plus className="h-3.5 w-3.5 mr-1" />{t("wf_add_step")}
              </Button>
            </div>

            {steps.map((step, idx) => (
              <Card key={idx}>
                <CardContent className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">#{idx + 1}</Badge>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => removeStep(idx)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">{t("contact_actions")}</Label>
                      <Select value={step.action_type} onValueChange={(v) => updateStep(idx, "action_type", v)}>
                        <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {ACTION_TYPES.map((at) => (
                            <SelectItem key={at} value={at}>{t(`action_${at}`)}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {step.action_type === "send_email" && (
                      <div className="space-y-1">
                        <Label className="text-xs">{t("camp_template")}</Label>
                        <Select
                          value={String(step.config.template_id ?? "")}
                          onValueChange={(v) => updateStep(idx, "template_id", Number(v))}
                        >
                          <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="—" /></SelectTrigger>
                          <SelectContent>
                            {templates.map((tpl) => (
                              <SelectItem key={tpl.id} value={String(tpl.id)}>{tpl.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {step.action_type === "wait" && (
                      <div className="space-y-1">
                        <Label className="text-xs">{t("action_wait")}</Label>
                        <Input
                          className="h-8 text-xs"
                          type="number"
                          placeholder="hours"
                          value={String(step.config.hours ?? "")}
                          onChange={(e) => updateStep(idx, "hours", Number(e.target.value))}
                        />
                      </div>
                    )}

                    {(step.action_type === "add_to_segment" || step.action_type === "remove_from_segment") && (
                      <div className="space-y-1">
                        <Label className="text-xs">{t("camp_segment")}</Label>
                        <Select
                          value={String(step.config.segment_id ?? "")}
                          onValueChange={(v) => updateStep(idx, "segment_id", Number(v))}
                        >
                          <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="—" /></SelectTrigger>
                          <SelectContent>
                            {segments.map((seg) => (
                              <SelectItem key={seg.id} value={String(seg.id)}>{seg.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}

            {steps.length === 0 && (
              <div className="text-center text-muted-foreground text-xs py-4 border rounded-md border-dashed">
                {t("empty")}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
            <Button onClick={handleSave} disabled={saving || !name.trim()}>
              {saving ? t("loading") : t("save")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
