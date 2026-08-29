import { getFirebaseAuth } from "@/app/firebaseConfig";
import {
  signInAnonymously,
  type Unsubscribe,
  type User,
  type UserCredential,
} from "firebase/auth";

export function observeAuthState(
  listener: (user: User | null) => void,
): Unsubscribe {
  const auth = getFirebaseAuth();
  return auth.onAuthStateChanged(listener);
}

export async function getAuthToken(): Promise<string> {
  const auth = getFirebaseAuth();
  let user: User;
  if (auth.currentUser) {
    user = auth.currentUser;
  } else {
    const credential: UserCredential = await signInAnonymously(auth);
    user = credential.user;
  }

  return user.getIdToken();
}
