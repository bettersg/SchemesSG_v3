"use client";

import { LanguageProvider } from "@/lib/landing-i18n";
import type { ReactNode } from "react";
import { AuthProvider } from "./auth-provider";
import { ChatProvider } from "./chat-provider";
import { SchemesProvider } from "./schemes-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <LanguageProvider>
      <AuthProvider>
        <ChatProvider>
          <SchemesProvider>{children}</SchemesProvider>
        </ChatProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}
