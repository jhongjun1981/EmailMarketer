"use client";

import { usePolling } from "@/hooks/use-polling";
import { getOverview, getTrends, listCampaigns } from "@/lib/api-client";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { RecentCampaigns } from "@/components/dashboard/recent-campaigns";

export default function DashboardPage() {
  const { data: overview } = usePolling(() => getOverview(), 30000);
  const { data: trends } = usePolling(() => getTrends(30), 60000);
  const { data: campaigns } = usePolling(() => listCampaigns(), 30000);

  return (
    <div className="space-y-6">
      <StatsCards data={overview} />
      <TrendChart data={trends} />
      <RecentCampaigns campaigns={campaigns} />
    </div>
  );
}
