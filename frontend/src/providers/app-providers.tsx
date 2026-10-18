"use client";

import { LanguageProvider } from "@/lib/landing-i18n";
import type { ReactNode } from "react";
import { AnalyticsProvider } from "./analytics-provider";
import { ChatProvider } from "./chat-provider";
import { SchemesProvider } from "./schemes-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <AnalyticsProvider>
      <LanguageProvider>
        <ChatProvider>
          <SchemesProvider>{children}</SchemesProvider>
        </ChatProvider>
      </LanguageProvider>
    </AnalyticsProvider>
  );
}
