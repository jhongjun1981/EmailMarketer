"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";
import { ContactStatusBadge } from "@/components/shared/status-badge";
import { useTranslation } from "@/i18n";
import type { ContactResponse } from "@/lib/api-types";

interface Props {
  contacts: ContactResponse[];
  onEdit: (contact: ContactResponse) => void;
  onDelete: (id: number) => void;
}

export function ContactTable({ contacts, onEdit, onDelete }: Props) {
  const { t } = useTranslation();

  if (contacts.length === 0) {
    return <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("contact_email")}</TableHead>
          <TableHead>{t("contact_name")}</TableHead>
          <TableHead className="hidden md:table-cell">{t("contact_company")}</TableHead>
          <TableHead>{t("contact_status")}</TableHead>
          <TableHead className="hidden lg:table-cell">{t("contact_source")}</TableHead>
          <TableHead className="hidden lg:table-cell">{t("contact_created")}</TableHead>
          <TableHead className="text-right">{t("contact_actions")}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {contacts.map((c) => (
          <TableRow key={c.id}>
            <TableCell className="font-medium">{c.email}</TableCell>
            <TableCell>{c.name || "—"}</TableCell>
            <TableCell className="hidden md:table-cell">{c.company || "—"}</TableCell>
            <TableCell><ContactStatusBadge status={c.status} /></TableCell>
            <TableCell className="hidden lg:table-cell">{c.source}</TableCell>
            <TableCell className="hidden lg:table-cell">{c.created_at?.slice(0, 10)}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(c)}>
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => onDelete(c.id)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
