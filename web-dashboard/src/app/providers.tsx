"use client";

import { I18nProvider } from "@/i18n";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
        </div>
      </div>
    </I18nProvider>
  );
}
