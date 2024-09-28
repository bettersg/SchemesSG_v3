import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Schemes SG",
  description: "One stop directory and AI-enabled search to help make sense of assistance schemes in Singapore.",
};

import MainHeader from '@/components/main-header/main-header';
import { NextUIProvider } from '@nextui-org/system';
import React from 'react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <NextUIProvider>
          <MainHeader/>
          {children}
        </NextUIProvider>
      </body>
    </html>
  )
}
