"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Pencil, Trash2, Eye, Send } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import { listTemplates, deleteTemplate } from "@/lib/api-client";
import { TemplateEditor } from "@/components/templates/template-editor";
import { TemplateTestDialog } from "@/components/templates/template-test-dialog";
import { toast } from "sonner";
import type { TemplateResponse } from "@/lib/api-types";

const CATEGORIES = ["all", "welcome", "notification", "promotion", "general"];

export default function TemplatesPage() {
  const { t } = useTranslation();
  const [category, setCategory] = useState("all");
  const [createOpen, setCreateOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<TemplateResponse | null>(null);
  const [testTarget, setTestTarget] = useState<TemplateResponse | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);

  const { data: templates, refresh } = usePolling(
    () => listTemplates(category === "all" ? undefined : category),
    10000,
  );

  async function handleDelete(id: number) {
    try {
      await deleteTemplate(id);
      toast.success(t("success"));
      refresh();
    } catch {
      toast.error(t("error"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <Tabs value={category} onValueChange={setCategory}>
          <TabsList>
            <TabsTrigger value="all">{t("tpl_category_all")}</TabsTrigger>
            {CATEGORIES.slice(1).map((c) => (
              <TabsTrigger key={c} value={c}>{c}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />{t("tpl_create")}
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {!templates || templates.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("tpl_name")}</TableHead>
                  <TableHead>{t("tpl_subject")}</TableHead>
                  <TableHead className="hidden md:table-cell">{t("tpl_category")}</TableHead>
                  <TableHead className="hidden lg:table-cell">{t("tpl_variables")}</TableHead>
                  <TableHead className="hidden lg:table-cell">{t("contact_created")}</TableHead>
                  <TableHead className="text-right">{t("contact_actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templates.map((tpl) => (
                  <TableRow key={tpl.id}>
                    <TableCell className="font-medium">{tpl.name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{tpl.subject}</TableCell>
                    <TableCell className="hidden md:table-cell">
                      <Badge variant="secondary" className="text-xs">{tpl.category}</Badge>
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">
                      <div className="flex gap-1 flex-wrap">
                        {tpl.variables?.slice(0, 3).map((v) => (
                          <Badge key={v} variant="outline" className="text-xs">{`{{${v}}}`}</Badge>
                        ))}
                        {(tpl.variables?.length ?? 0) > 3 && (
                          <Badge variant="outline" className="text-xs">+{tpl.variables.length - 3}</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">{tpl.created_at?.slice(0, 10)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setPreviewHtml(tpl.html_body)} title={t("tpl_preview")}>
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setTestTarget(tpl)} title={t("tpl_test_send")}>
                          <Send className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setEditTemplate(tpl)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(tpl.id)}>
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

      {/* Preview Dialog */}
      {previewHtml !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setPreviewHtml(null)}>
          <div className="bg-white rounded-lg shadow-lg w-full max-w-3xl max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold">{t("tpl_preview")}</h3>
              <Button variant="ghost" size="sm" onClick={() => setPreviewHtml(null)}>{t("close")}</Button>
            </div>
            <iframe
              srcDoc={previewHtml}
              className="w-full h-[60vh]"
              sandbox=""
              title="preview"
            />
          </div>
        </div>
      )}

      <TemplateEditor open={createOpen} onOpenChange={setCreateOpen} template={null} onSuccess={refresh} />
      <TemplateEditor open={!!editTemplate} onOpenChange={(o) => { if (!o) setEditTemplate(null); }} template={editTemplate} onSuccess={refresh} />
      {testTarget && (
        <TemplateTestDialog
          open={!!testTarget}
          onOpenChange={(o) => { if (!o) setTestTarget(null); }}
          templateId={testTarget.id}
          variables={testTarget.variables ?? []}
        />
      )}
    </div>
  );
}
