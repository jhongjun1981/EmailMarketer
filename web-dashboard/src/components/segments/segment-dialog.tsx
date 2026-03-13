"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { createSegment, updateSegment } from "@/lib/api-client";
import type { SegmentResponse } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  segment: SegmentResponse | null;
  onSuccess: () => void;
}

export function SegmentDialog({ open, onOpenChange, segment, onSuccess }: Props) {
  const { t } = useTranslation();
  const isEdit = !!segment;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isDynamic, setIsDynamic] = useState(false);
  const [field, setField] = useState("company");
  const [op, setOp] = useState("eq");
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (segment) {
      setName(segment.name);
      setDescription(segment.description);
      setIsDynamic(segment.is_dynamic);
      if (segment.rules) {
        const r = segment.rules as Record<string, string>;
        setField(r.field || "company");
        setOp(r.op || "eq");
        setValue(r.value || "");
      }
    } else {
      setName("");
      setDescription("");
      setIsDynamic(false);
      setField("company");
      setOp("eq");
      setValue("");
    }
  }, [segment, open]);

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const rules = isDynamic ? { field, op, value } : undefined;
      if (isEdit) {
        await updateSegment(segment!.id, { name, description, rules });
      } else {
        await createSegment({ name, description, is_dynamic: isDynamic, rules });
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
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? t("seg_edit") : t("seg_create")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>{t("seg_name")}</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t("seg_desc")}</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={isDynamic} onCheckedChange={setIsDynamic} disabled={isEdit} />
            <Label>{t("seg_type_dynamic")}</Label>
          </div>
          {isDynamic && (
            <div className="space-y-3 rounded-md border p-3">
              <p className="text-sm font-medium">{t("seg_rules")}</p>
              <div className="grid grid-cols-3 gap-2">
                <Select value={field} onValueChange={setField}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="email">{t("contact_email")}</SelectItem>
                    <SelectItem value="name">{t("contact_name")}</SelectItem>
                    <SelectItem value="company">{t("contact_company")}</SelectItem>
                    <SelectItem value="source">{t("contact_source")}</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={op} onValueChange={setOp}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="eq">{t("seg_op_eq")}</SelectItem>
                    <SelectItem value="ne">{t("seg_op_ne")}</SelectItem>
                    <SelectItem value="contains">{t("seg_op_contains")}</SelectItem>
                  </SelectContent>
                </Select>
                <Input value={value} onChange={(e) => setValue(e.target.value)} placeholder={t("seg_value")} />
              </div>
            </div>
          )}
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
