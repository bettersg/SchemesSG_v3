import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import classes from "../components/main-layout/main-layout.module.css"

const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 300 500 900",
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
      <body className={`${geistSans.variable} antialiased`}>
        <NextUIProvider>
          <MainHeader/>
          <div className={classes.contentWrapper}>
            {children}
          </div>
        </NextUIProvider>
      </body>
    </html>
  )
}
