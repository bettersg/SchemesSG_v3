import {
  getApp,
  getApps,
  initializeApp,
  type FirebaseApp,
} from "firebase/app";
import {
  getAnalytics,
  isSupported,
  type Analytics,
} from "firebase/analytics";
import { getAuth, type Auth } from "firebase/auth";

// TODO make it a configuration variable
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FB_API_KEY,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
  authDomain: `${process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID}.firebaseapp.com`,
};

let app: FirebaseApp | undefined;
let analyticsInitializationStarted = false;

function getFirebaseApp(): FirebaseApp {
  if (!app) {
    app = getApps().length ? getApp() : initializeApp(firebaseConfig);
  }
  return app;
}

function initializeFirebaseAnalytics(firebaseApp: FirebaseApp) {
  if (typeof window === "undefined" || analyticsInitializationStarted) return;

  const globalForAnalytics = globalThis as typeof globalThis & {
    __schemesSgAnalytics?: Analytics;
  };

  if (globalForAnalytics.__schemesSgAnalytics) return;

  analyticsInitializationStarted = true;
  void isSupported()
    .then((supported) => {
      if (supported) {
        globalForAnalytics.__schemesSgAnalytics = getAnalytics(firebaseApp);
      }
    })
    .catch((error) => {
      console.error(
        "Firebase Analytics is not supported in this environment.",
        error,
      );
    });
}

export function getFirebaseAuth(): Auth {
  const firebaseApp = getFirebaseApp();
  initializeFirebaseAnalytics(firebaseApp);
  return getAuth(firebaseApp);
}
