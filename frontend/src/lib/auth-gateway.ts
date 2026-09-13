import { getFirebaseAuth } from "@/app/firebaseConfig";
import {
  signInAnonymously,
  type User,
  type UserCredential,
} from "firebase/auth";

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
