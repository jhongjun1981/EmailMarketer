"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, FolderTree, FileText, Send, GitBranch, Settings } from "lucide-react";
import { useTranslation } from "@/i18n";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", icon: LayoutDashboard, labelKey: "nav_dashboard" },
  { href: "/contacts", icon: Users, labelKey: "nav_contacts" },
  { href: "/segments", icon: FolderTree, labelKey: "nav_segments" },
  { href: "/templates", icon: FileText, labelKey: "nav_templates" },
  { href: "/campaigns", icon: Send, labelKey: "nav_campaigns" },
  { href: "/workflows", icon: GitBranch, labelKey: "nav_workflows" },
  { href: "/settings", icon: Settings, labelKey: "nav_settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();

  return (
    <aside className="hidden md:flex w-56 flex-col border-r bg-card h-screen sticky top-0">
      <div className="p-4 border-b">
        <h1 className="font-bold text-lg">{t("title")}</h1>
        <p className="text-xs text-muted-foreground">{t("subtitle")}</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map(({ href, icon: Icon, labelKey }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {t(labelKey)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
