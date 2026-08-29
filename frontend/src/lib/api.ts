import { getAuthToken } from "@/lib/auth-gateway";

export { getAuthToken } from "@/lib/auth-gateway";

export async function fetchWithAuth(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  try {
    const token = await getAuthToken();

    // Merge the authorization header with existing headers
    const headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
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
