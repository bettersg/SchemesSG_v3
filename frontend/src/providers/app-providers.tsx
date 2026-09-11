"use client";

import { LanguageProvider } from "@/lib/landing-i18n";
import type { ReactNode } from "react";
import { ChatProvider } from "./chat-provider";
import { SchemesProvider } from "./schemes-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <LanguageProvider>
      <ChatProvider>
        <SchemesProvider>{children}</SchemesProvider>
      </ChatProvider>
    </LanguageProvider>
  );
}
