"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import { useTranslation } from "@/i18n";
import type { TrendDataPoint } from "@/lib/api-types";

export function TrendChart({ data }: { data: TrendDataPoint[] | null }) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{t("trend_title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {!data || data.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
            {t("empty")}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data}>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(v) => v.slice(5)}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="sent"
                name={t("trend_sent")}
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="opened"
                name={t("trend_opened")}
                stroke="var(--chart-2)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="clicked"
                name={t("trend_clicked")}
                stroke="var(--chart-3)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
