"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CampaignStatusBadge } from "@/components/shared/status-badge";
import { useTranslation } from "@/i18n";
import type { CampaignResponse } from "@/lib/api-types";

export function RecentCampaigns({ campaigns }: { campaigns: CampaignResponse[] | null }) {
  const { t } = useTranslation();
  const recent = campaigns?.slice(0, 5) ?? [];

  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-base">{t("recent_campaigns")}</CardTitle>
        <Link href="/campaigns">
          <Button variant="ghost" size="sm" className="text-xs">{t("view_all")}</Button>
        </Link>
      </CardHeader>
      <CardContent>
        {recent.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground text-sm">{t("empty")}</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("camp_name")}</TableHead>
                <TableHead>{t("camp_status")}</TableHead>
                <TableHead className="text-right">{t("camp_sent")}</TableHead>
                <TableHead className="text-right">{t("camp_open_rate")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((c) => {
                const openRate = c.sent_count > 0 ? ((c.open_count / c.sent_count) * 100).toFixed(1) : "0.0";
                return (
                  <TableRow key={c.id}>
                    <TableCell>
                      <Link href={`/campaigns/${c.id}`} className="hover:underline font-medium">
                        {c.name}
                      </Link>
                    </TableCell>
                    <TableCell><CampaignStatusBadge status={c.status} /></TableCell>
                    <TableCell className="text-right">{c.sent_count}</TableCell>
                    <TableCell className="text-right">{openRate}%</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
