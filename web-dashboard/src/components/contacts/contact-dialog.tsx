"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useTranslation } from "@/i18n";
import { createContact, updateContact } from "@/lib/api-client";
import type { ContactResponse } from "@/lib/api-types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contact: ContactResponse | null;
  onSuccess: () => void;
}

export function ContactDialog({ open, onOpenChange, contact, onSuccess }: Props) {
  const { t } = useTranslation();
  const isEdit = !!contact;
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [phone, setPhone] = useState("");
  const [source, setSource] = useState("manual");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (contact) {
      setEmail(contact.email);
      setName(contact.name);
      setCompany(contact.company);
      setPhone(contact.phone);
      setSource(contact.source);
    } else {
      setEmail("");
      setName("");
      setCompany("");
      setPhone("");
      setSource("manual");
    }
  }, [contact, open]);

  async function handleSave() {
    if (!email.trim()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await updateContact(contact!.id, { name, company, phone });
      } else {
        await createContact({ email: email.trim(), name, company, phone, source });
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
          <DialogTitle>{isEdit ? t("contact_edit") : t("contact_create")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>{t("contact_email")}</Label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} disabled={isEdit} placeholder="user@example.com" />
          </div>
          <div className="space-y-1.5">
            <Label>{t("contact_name")}</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t("contact_company")}</Label>
            <Input value={company} onChange={(e) => setCompany(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t("contact_phone")}</Label>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>{t("cancel")}</Button>
            <Button onClick={handleSave} disabled={saving || !email.trim()}>
              {saving ? t("loading") : t("save")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
