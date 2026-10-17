"use client";

import { getAnalytics, isSupported, type Analytics } from "firebase/analytics";
import { useEffect, type ReactNode } from "react";
import { getFirebaseApp } from "@/app/firebaseConfig";
import { flushPendingEvents } from "@/lib/analytics";

export function AnalyticsProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID) {
      return;
    }

    const globalForAnalytics = globalThis as typeof globalThis & {
      __schemesSgAnalytics?: Analytics;
    };

    if (globalForAnalytics.__schemesSgAnalytics) {
      return;
    }

    void isSupported()
      .then((supported) => {
        if (supported) {
          const app = getFirebaseApp();
          // getAnalytics, not initializeAnalytics with send_page_view: false.
          // Enhanced Measurement is the intended source of page_view.
          globalForAnalytics.__schemesSgAnalytics = getAnalytics(app);
          flushPendingEvents();
        }
      })
      .catch((error) => {
        console.error(
          "Firebase Analytics is not supported in this environment.",
          error,
        );
      });
  }, []);

  return <>{children}</>;
}
