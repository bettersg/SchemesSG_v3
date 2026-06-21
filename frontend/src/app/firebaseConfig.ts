import { getApp, getApps, initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import { getAuth } from "firebase/auth";

// TODO make it a configuration variable
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FB_API_KEY,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
  authDomain: `${process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID}.firebaseapp.com`,
};

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);

let analytics: ReturnType<typeof getAnalytics> | undefined;

if (typeof window !== "undefined") {
  const globalForAnalytics = globalThis as typeof globalThis & {
    __schemesSgAnalytics?: ReturnType<typeof getAnalytics>;
  };

  if (globalForAnalytics.__schemesSgAnalytics) {
    analytics = globalForAnalytics.__schemesSgAnalytics;
  } else {
    isSupported()
      .then((supported) => {
        if (supported) {
          analytics = getAnalytics(app);
          globalForAnalytics.__schemesSgAnalytics = analytics;
        }
      })
      .catch((error) => {
        console.error(
          "Firebase Analytics is not supported in this environment.",
          error,
        );
      });
  }
}

export { app, auth, analytics };
