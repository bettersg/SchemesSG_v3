import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";

// TODO make it a configuration variable
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

const app = initializeApp(firebaseConfig);

let analytics: ReturnType<typeof getAnalytics> | undefined;

isSupported()
  .then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  })
  .catch((error) => {
    console.error("Firebase Analytics is not supported in this environment.", error);
  });

export { app, analytics };
