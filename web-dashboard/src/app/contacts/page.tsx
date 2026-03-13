"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Upload, Search } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import { listContacts, deleteContact } from "@/lib/api-client";
import { ContactTable } from "@/components/contacts/contact-table";
import { ContactDialog } from "@/components/contacts/contact-dialog";
import { ImportDialog } from "@/components/contacts/import-dialog";
import { Pagination } from "@/components/shared/pagination";
import { toast } from "sonner";
import type { ContactResponse } from "@/lib/api-types";

export default function ContactsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editContact, setEditContact] = useState<ContactResponse | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const fetcher = useCallback(
    () => listContacts({ page, page_size: 50, status: statusFilter || undefined, search: search || undefined }),
    [page, statusFilter, search]
  );
  const { data, refresh } = usePolling(fetcher, 10000);

  async function handleDelete(id: number) {
    try {
      await deleteContact(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder={t("contact_search")}
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <Select value={statusFilter} onValueChange={(v: string) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder={t("status_all")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">{t("status_all")}</SelectItem>
              <SelectItem value="active">{t("status_active")}</SelectItem>
              <SelectItem value="unsubscribed">{t("status_unsubscribed")}</SelectItem>
              <SelectItem value="bounced">{t("status_bounced")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            <Upload className="h-4 w-4 mr-1" />{t("contact_import")}
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />{t("contact_create")}
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <ContactTable
            contacts={data?.items ?? []}
            onEdit={(c) => setEditContact(c)}
            onDelete={handleDelete}
          />
        </CardContent>
      </Card>

      {data && (
        <Pagination page={page} pageSize={50} total={data.total} onPageChange={setPage} />
      )}

      <ContactDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        contact={null}
        onSuccess={refresh}
      />
      <ContactDialog
        open={!!editContact}
        onOpenChange={(open) => { if (!open) setEditContact(null); }}
        contact={editContact}
        onSuccess={refresh}
      />
      <ImportDialog open={importOpen} onOpenChange={setImportOpen} onSuccess={refresh} />
    </div>
  );
}
