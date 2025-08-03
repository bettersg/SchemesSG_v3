import { auth } from "../firebaseConfig";
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
    const token = await getAuthToken();
    
    // Merge the authorization header with existing headers
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    return fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    console.error("Error in fetchWithAuth:", error);
    throw error;
  }
}