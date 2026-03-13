"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Plus, TestTube, CheckCircle, XCircle, Copy, Pencil, Trash2 } from "lucide-react";
import { usePolling } from "@/hooks/use-polling";
import { useTranslation } from "@/i18n";
import { listSmtpAccounts, addSmtpAccount, updateSmtpAccount, deleteSmtpAccount, testSmtp, getHealth } from "@/lib/api-client";
import { toast } from "sonner";
import type { SmtpAccount } from "@/lib/api-types";

export default function SettingsPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState("smtp");
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const { data: smtpAccounts, refresh: refreshSmtp } = usePolling(() => listSmtpAccounts(), 30000);
  const { data: health } = usePolling(() => getHealth(), 30000);

  // Add SMTP form
  const [smtpName, setSmtpName] = useState("");
  const [smtpEmail, setSmtpEmail] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("465");
  const [smtpSsl, setSmtpSsl] = useState(true);
  const [smtpLimit, setSmtpLimit] = useState("500");
  const [smtpActive, setSmtpActive] = useState(true);
  const [saving, setSaving] = useState(false);

  // Test SMTP
  const [testEmail, setTestEmail] = useState("");
  const [testPwd, setTestPwd] = useState("");
  const [testTo, setTestTo] = useState("");
  const [testing, setTesting] = useState(false);

  const selectedAccount = smtpAccounts?.find((a) => a.id === selectedId) ?? null;

  useEffect(() => {
    if (addOpen) {
      setSmtpName("");
      setSmtpEmail("");
      setSmtpPassword("");
      setSmtpHost("");
      setSmtpPort("465");
      setSmtpSsl(true);
      setSmtpLimit("500");
      setSmtpActive(true);
    }
  }, [addOpen]);

  useEffect(() => {
    if (editOpen && selectedAccount) {
      setSmtpName(selectedAccount.name);
      setSmtpEmail(selectedAccount.email);
      setSmtpPassword("");
      setSmtpHost(selectedAccount.smtp_host);
      setSmtpPort(String(selectedAccount.smtp_port));
      setSmtpSsl(selectedAccount.use_ssl);
      setSmtpLimit(String(selectedAccount.daily_limit));
      setSmtpActive(selectedAccount.is_active);
    }
  }, [editOpen, selectedAccount]);

  async function handleAddSmtp() {
    if (!smtpName.trim() || !smtpEmail.trim() || !smtpPassword.trim()) return;
    setSaving(true);
    try {
      await addSmtpAccount({
        name: smtpName,
        email: smtpEmail,
        password: smtpPassword,
        smtp_host: smtpHost || undefined,
        smtp_port: smtpPort ? Number(smtpPort) : undefined,
        use_ssl: smtpSsl,
        daily_limit: Number(smtpLimit) || 500,
      });
      toast.success(t("success"));
      setAddOpen(false);
      refreshSmtp();
    } catch {
      toast.error(t("error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSmtp() {
    if (!selectedId || !smtpName.trim() || !smtpEmail.trim()) return;
    setSaving(true);
    try {
      const updates: Record<string, unknown> = {
        name: smtpName,
        email: smtpEmail,
        smtp_host: smtpHost || undefined,
        smtp_port: smtpPort ? Number(smtpPort) : undefined,
        use_ssl: smtpSsl,
        daily_limit: Number(smtpLimit) || 500,
        is_active: smtpActive,
      };
      if (smtpPassword.trim()) {
        updates.password = smtpPassword;
      }
      await updateSmtpAccount(selectedId, updates);
      toast.success(t("success"));
      setEditOpen(false);
      refreshSmtp();
    } catch {
      toast.error(t("error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteSmtp() {
    if (!selectedId) return;
    if (!confirm(t("smtp_delete_confirm"))) return;
    setDeleting(true);
    try {
      await deleteSmtpAccount(selectedId);
      toast.success(t("success"));
      setSelectedId(null);
      refreshSmtp();
    } catch {
      toast.error(t("error"));
    } finally {
      setDeleting(false);
    }
  }

  async function handleTestSmtp() {
    if (!testEmail.trim() || !testPwd.trim() || !testTo.trim()) return;
    setTesting(true);
    try {
      const result = await testSmtp(testEmail, testPwd, testTo);
      toast.success(result.message || t("success"));
    } catch {
      toast.error(t("error"));
    } finally {
      setTesting(false);
    }
  }

  const apiKey = process.env.NEXT_PUBLIC_API_KEY || "changeme-your-secret-key";

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("nav_settings")}</h2>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="smtp">{t("smtp_accounts")}</TabsTrigger>
          <TabsTrigger value="api">{t("api_key_label")}</TabsTrigger>
          <TabsTrigger value="system">{t("sys_status")}</TabsTrigger>
        </TabsList>

        {/* SMTP Tab */}
        <TabsContent value="smtp" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              {selectedId && (
                <>
                  <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
                    <Pencil className="h-4 w-4 mr-1" />{t("smtp_edit")}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleDeleteSmtp} disabled={deleting}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950">
                    <Trash2 className="h-4 w-4 mr-1" />{deleting ? t("loading") : t("smtp_delete")}
                  </Button>
                </>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setTab("test")}>
                <TestTube className="h-4 w-4 mr-1" />{t("smtp_test")}
              </Button>
              <Button onClick={() => setAddOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />{t("smtp_add")}
              </Button>
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              {!smtpAccounts || smtpAccounts.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground text-sm">{t("empty")}</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("smtp_name")}</TableHead>
                      <TableHead>{t("smtp_email")}</TableHead>
                      <TableHead className="hidden md:table-cell">{t("smtp_host")}</TableHead>
                      <TableHead className="hidden md:table-cell">{t("smtp_port")}</TableHead>
                      <TableHead className="hidden lg:table-cell text-right">{t("smtp_sent_today")}</TableHead>
                      <TableHead className="hidden lg:table-cell text-right">{t("smtp_daily_limit")}</TableHead>
                      <TableHead>{t("smtp_active")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {smtpAccounts.map((acc) => (
                      <TableRow
                        key={acc.id}
                        className={`cursor-pointer transition-colors ${
                          selectedId === acc.id
                            ? "bg-primary/10 hover:bg-primary/15 dark:bg-primary/20 dark:hover:bg-primary/25"
                            : "hover:bg-muted/50"
                        }`}
                        onClick={() => setSelectedId(selectedId === acc.id ? null : acc.id)}
                      >
                        <TableCell className="font-medium">{acc.name}</TableCell>
                        <TableCell>{acc.email}</TableCell>
                        <TableCell className="hidden md:table-cell">{acc.smtp_host}</TableCell>
                        <TableCell className="hidden md:table-cell">{acc.smtp_port}</TableCell>
                        <TableCell className="hidden lg:table-cell text-right">{acc.sent_today}</TableCell>
                        <TableCell className="hidden lg:table-cell text-right">{acc.daily_limit}</TableCell>
                        <TableCell>
                          {acc.is_active ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-muted-foreground" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Test SMTP Tab (virtual) */}
        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">{t("smtp_test")}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>{t("smtp_email")}</Label>
                  <Input value={testEmail} onChange={(e) => setTestEmail(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>{t("smtp_password")}</Label>
                  <Input type="password" value={testPwd} onChange={(e) => setTestPwd(e.target.value)} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_test_to")}</Label>
                <Input value={testTo} onChange={(e) => setTestTo(e.target.value)} placeholder="test@example.com" />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setTab("smtp")}>{t("cancel")}</Button>
                <Button onClick={handleTestSmtp} disabled={testing || !testEmail.trim() || !testPwd.trim() || !testTo.trim()}>
                  {testing ? t("loading") : t("smtp_test")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Key Tab */}
        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">{t("api_key_label")}</CardTitle></CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Input readOnly value={apiKey} className="font-mono text-sm" />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => { navigator.clipboard.writeText(apiKey); toast.success("Copied"); }}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">{t("sys_health")}</CardTitle></CardHeader>
            <CardContent>
              {health ? (
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                    {health.status}
                  </Badge>
                  <span className="text-sm text-muted-foreground">{health.service}</span>
                </div>
              ) : (
                <span className="text-sm text-muted-foreground">{t("loading")}</span>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add SMTP Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{t("smtp_add")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>{t("smtp_name")}</Label>
              <Input value={smtpName} onChange={(e) => setSmtpName(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>{t("smtp_email")}</Label>
                <Input value={smtpEmail} onChange={(e) => setSmtpEmail(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_password")}</Label>
                <Input type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label>{t("smtp_host")}</Label>
                <Input value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} placeholder="smtp.gmail.com" />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_port")}</Label>
                <Input type="number" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_ssl")}</Label>
                <div className="pt-2">
                  <Switch checked={smtpSsl} onCheckedChange={setSmtpSsl} />
                </div>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>{t("smtp_daily_limit")}</Label>
              <Input type="number" value={smtpLimit} onChange={(e) => setSmtpLimit(e.target.value)} />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setAddOpen(false)}>{t("cancel")}</Button>
              <Button onClick={handleAddSmtp} disabled={saving || !smtpName.trim() || !smtpEmail.trim() || !smtpPassword.trim()}>
                {saving ? t("loading") : t("save")}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit SMTP Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{t("smtp_edit")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>{t("smtp_name")}</Label>
              <Input value={smtpName} onChange={(e) => setSmtpName(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>{t("smtp_email")}</Label>
                <Input value={smtpEmail} onChange={(e) => setSmtpEmail(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_password")}</Label>
                <Input type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)} placeholder={t("smtp_password_hint")} />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label>{t("smtp_host")}</Label>
                <Input value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_port")}</Label>
                <Input type="number" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_ssl")}</Label>
                <div className="pt-2">
                  <Switch checked={smtpSsl} onCheckedChange={setSmtpSsl} />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>{t("smtp_daily_limit")}</Label>
                <Input type="number" value={smtpLimit} onChange={(e) => setSmtpLimit(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>{t("smtp_active")}</Label>
                <div className="pt-2">
                  <Switch checked={smtpActive} onCheckedChange={setSmtpActive} />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setEditOpen(false)}>{t("cancel")}</Button>
              <Button onClick={handleEditSmtp} disabled={saving || !smtpName.trim() || !smtpEmail.trim()}>
                {saving ? t("loading") : t("save")}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
