"use client";

import MainHeader from "@/components/main-header";
import { HeroUIProvider } from "@heroui/system";
import React from "react";
import { ChatProvider } from "./providers";
import { AuthProvider } from "./providers/AuthProvider";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <HeroUIProvider>
      <AuthProvider>
        <ChatProvider>
          <div className="h-screen flex flex-col">
            <MainHeader />
            <div className="h-[calc(100vh-64px)] bg-[linear-gradient(117deg,#EFF6FF_0%,#FFF_50%,#FAF5FF_100%)] overflow-y-scroll">
              {children}
            </div>
          </div>
        </ChatProvider>
      </AuthProvider>
    </HeroUIProvider>
  );
}
