import "server-only";

type NextRequestInit = RequestInit & {
  next?: { revalidate?: number };
};

const REFRESH_MARGIN_MS = 60_000;
let cachedToken: { token: string; expiresAt: number } | undefined;
let inFlightToken: Promise<string> | undefined;

async function requestToken() {
  const apiKey = process.env.NEXT_PUBLIC_FB_API_KEY;
  if (!apiKey) throw new Error("Missing NEXT_PUBLIC_FB_API_KEY");

  const response = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${encodeURIComponent(apiKey)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ returnSecureToken: true }),
      cache: "no-store",
    },
  );
  if (!response.ok) {
    throw new Error(
      `Firebase anonymous sign-in failed with status ${response.status}`,
    );
  }

  const payload = (await response.json()) as {
    idToken?: unknown;
    expiresIn?: unknown;
  };
  if (typeof payload.idToken !== "string" || !payload.idToken) {
    throw new Error("Firebase anonymous sign-in response missing idToken");
  }
  const expiresInSeconds = Number(payload.expiresIn);
  if (!Number.isFinite(expiresInSeconds) || expiresInSeconds <= 0) {
    throw new Error(
      "Firebase anonymous sign-in response has invalid expiresIn",
    );
  }

  cachedToken = {
    token: payload.idToken,
    expiresAt: Date.now() + expiresInSeconds * 1_000 - REFRESH_MARGIN_MS,
  };
  return cachedToken.token;
}

export async function getServerAuthToken() {
  if (cachedToken && Date.now() < cachedToken.expiresAt) {
    return cachedToken.token;
  }
  if (!inFlightToken) {
    inFlightToken = requestToken().finally(() => {
      inFlightToken = undefined;
    });
  }
  return inFlightToken;
}

export async function serverFetchWithAuth(
  input: string | URL,
  init: NextRequestInit = {},
) {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${await getServerAuthToken()}`);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(input, { ...init, headers });
}
