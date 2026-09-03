import { beforeEach, describe, expect, it, vi } from "vitest";

const firebase = vi.hoisted(() => ({
  getFirebaseAuth: vi.fn(),
  signInAnonymously: vi.fn(),
}));

vi.mock("@/app/firebaseConfig", () => ({
  getFirebaseAuth: firebase.getFirebaseAuth,
}));

vi.mock("firebase/auth", () => ({
  signInAnonymously: firebase.signInAnonymously,
}));

import { getAuthToken, observeAuthState } from "./auth-gateway";

describe("auth gateway", () => {
  beforeEach(() => {
    firebase.getFirebaseAuth.mockReset();
    firebase.signInAnonymously.mockReset();
  });

  it("delivers authentication changes and returns the unsubscribe handle", () => {
    const user = { uid: "user-123" };
    const unsubscribe = vi.fn();
    firebase.getFirebaseAuth.mockReturnValue({
      onAuthStateChanged: (listener: (value: typeof user) => void) => {
        listener(user);
        return unsubscribe;
      },
    });
    const observedUsers: string[] = [];

    const stopObserving = observeAuthState((value) => {
      if (value) observedUsers.push(value.uid);
    });

    expect(observedUsers).toEqual(["user-123"]);
    expect(stopObserving).toBe(unsubscribe);
  });

  it("returns the current user's token without signing in again", async () => {
    firebase.getFirebaseAuth.mockReturnValue({
      currentUser: { getIdToken: async () => "current-token" },
    });

    await expect(getAuthToken()).resolves.toBe("current-token");
    expect(firebase.signInAnonymously).not.toHaveBeenCalled();
  });

  it("signs in anonymously when no current user exists", async () => {
    const auth = { currentUser: null };
    firebase.getFirebaseAuth.mockReturnValue(auth);
    firebase.signInAnonymously.mockResolvedValue({
      user: { getIdToken: async () => "anonymous-token" },
    });

    await expect(getAuthToken()).resolves.toBe("anonymous-token");
  });
});
