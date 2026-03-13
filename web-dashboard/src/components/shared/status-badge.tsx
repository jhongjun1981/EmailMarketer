import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/i18n";

const CAMPAIGN_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  scheduled: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  sending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  sent: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  paused: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
};

const CONTACT_STYLES: Record<string, string> = {
  active: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  unsubscribed: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  bounced: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  complained: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
};

const WORKFLOW_STYLES: Record<string, string> = {
  active: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  paused: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

function StatusBadge({ status, styles }: { status: string; styles: Record<string, string> }) {
  const { t } = useTranslation();
  const label = t(`status_${status}`) || status;
  const isAnimated = status === "sending" || (styles === WORKFLOW_STYLES && status === "active");

  return (
    <Badge variant="outline" className={cn("text-xs font-medium border-0", styles[status])}>
      {isAnimated && (
        <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
      )}
      {label}
    </Badge>
  );
}

export function CampaignStatusBadge({ status }: { status: string }) {
  return <StatusBadge status={status} styles={CAMPAIGN_STYLES} />;
}

export function ContactStatusBadge({ status }: { status: string }) {
  return <StatusBadge status={status} styles={CONTACT_STYLES} />;
}

export function WorkflowStatusBadge({ status }: { status: string }) {
  return <StatusBadge status={status} styles={WORKFLOW_STYLES} />;
}
