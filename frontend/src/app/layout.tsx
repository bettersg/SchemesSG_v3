import MainFooter from "@/components/main-footer/main-footer";
import MainHeader from "@/components/main-header/main-header";
import { NextUIProvider } from "@nextui-org/system";
import type { Metadata } from "next";
import localFont from "next/font/local";
import React from "react";
import classes from "../components/main-layout/main-layout.module.css";
import "./globals.css";
import { ChatProvider } from "./providers";
import { AuthProvider } from "./providers/AuthProvider";

const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 200 300 400 500 600 700 800 900",
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
    <html lang="en">
      <body className={`${geistSans.variable} antialiased`}>
        <NextUIProvider>
          <AuthProvider>
            <ChatProvider>
              <MainHeader />
              <div className={classes.contentWrapper}>{children}</div>
              <MainFooter />
            </ChatProvider>
          </AuthProvider>
        </NextUIProvider>
      </body>
    </html>
  );
}
