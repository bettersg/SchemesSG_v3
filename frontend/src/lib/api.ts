import { auth } from "../app/firebaseConfig";
import { signInAnonymously, User, UserCredential } from "firebase/auth";

export async function getAuthToken(): Promise<string> {
  try {
    // Get current user or sign in anonymously
    let user: User;
    if (auth.currentUser) {
      user = auth.currentUser;
    } else {
      const credential: UserCredential = await signInAnonymously(auth);
      user = credential.user;
    }
    const token = await user.getIdToken();
    return token;
  } catch (error) {
    console.error("Error getting auth token:", error);
    throw error;
  }
}

export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  try {
    const headers = new Headers(options.headers);
    headers.set("Authorization", `Bearer ${await getAuthToken()}`);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    return await fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    console.error("Error in fetchWithAuth:", error);
    throw error;
  }
}
