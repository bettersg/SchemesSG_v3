// import MainFooter from "@/components/main-footer/main-footer";
import MainHeader from "@/components/main-header";
// import Footer from "@/components/footer";
import { HeroUIProvider } from "@heroui/system";
import type { Metadata } from "next";
import localFont from "next/font/local";
import React from "react";
import "./globals.css";
import { ChatProvider } from "./providers";
import { AuthProvider } from "./providers/AuthProvider";

const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 200 300 400 500 600 700 800 900",
  fallback: ['ui-sans-serif', 'system-ui', 'sans-serif']
});

export const metadata: Metadata = {
  title: "Schemes SG",
  description:
    "One stop directory and AI-enabled search to help make sense of assistance schemes in Singapore.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="!p-0 !overflow-visible">
      <body className={`${geistSans.className} antialiased`}>
        <HeroUIProvider>
          <AuthProvider>
            <ChatProvider>
              <div className="h-screen flex flex-col">
                <MainHeader />
                <div className="h-[calc(100vh-64px)] bg-[linear-gradient(117deg,#EFF6FF_0%,#FFF_50%,#FAF5FF_100%)] overflow-y-scroll">{children}</div>
                {/* <Footer /> */}
              </div>
            </ChatProvider>
          </AuthProvider>
        </HeroUIProvider>
      </body>
    </html>
  );
}
