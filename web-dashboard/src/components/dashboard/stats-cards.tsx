"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Users, UserCheck, Send, Mail, MailOpen, MousePointerClick } from "lucide-react";
import { useTranslation } from "@/i18n";
import type { OverviewReport } from "@/lib/api-types";

const STATS = [
  { key: "total_contacts", icon: Users, format: "number" },
  { key: "active_contacts", icon: UserCheck, format: "number" },
  { key: "total_campaigns", icon: Send, format: "number" },
  { key: "total_sent", icon: Mail, format: "number" },
  { key: "avg_open_rate", icon: MailOpen, format: "percent" },
  { key: "avg_click_rate", icon: MousePointerClick, format: "percent" },
] as const;

export function StatsCards({ data }: { data: OverviewReport | null }) {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {STATS.map(({ key, icon: Icon, format }) => {
        const value = data ? data[key as keyof OverviewReport] : 0;
        const display = format === "percent" ? `${(value as number).toFixed(1)}%` : String(value);

        return (
          <Card key={key}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">{t(`stat_${key}`)}</span>
              </div>
              <p className="text-2xl font-bold">{data ? display : "—"}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
