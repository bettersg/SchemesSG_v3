import { getAuthToken } from "@/lib/auth-gateway";

export { getAuthToken } from "@/lib/auth-gateway";

export async function fetchWithAuth(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  try {
    const headers = new Headers(options.headers);
    headers.set("Authorization", `Bearer ${await getAuthToken()}`);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    return fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    console.error("Error in fetchWithAuth:", error);
    throw error;
  }
}
