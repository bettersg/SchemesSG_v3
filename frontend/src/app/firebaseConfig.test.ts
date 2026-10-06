import { describe, expect, it, vi } from "vitest";

const firebaseMocks = vi.hoisted(() => {
  const app = { name: "test-app" };
  const auth = { name: "test-auth" };

  return {
    app,
    auth,
    getAnalytics: vi.fn(),
    getApp: vi.fn(() => app),
    getApps: vi.fn(() => []),
    getAuth: vi.fn(() => auth),
    initializeApp: vi.fn(() => app),
    isSupported: vi.fn(async () => false),
  };
});

vi.mock("firebase/app", () => ({
  getApp: firebaseMocks.getApp,
  getApps: firebaseMocks.getApps,
  initializeApp: firebaseMocks.initializeApp,
}));

vi.mock("firebase/analytics", () => ({
  getAnalytics: firebaseMocks.getAnalytics,
  isSupported: firebaseMocks.isSupported,
}));

vi.mock("firebase/auth", () => ({
  getAuth: firebaseMocks.getAuth,
}));

import { getFirebaseAuth, getFirebaseApp } from "./firebaseConfig";

const importCalls = {
  getAuth: firebaseMocks.getAuth.mock.calls.length,
  initializeApp: firebaseMocks.initializeApp.mock.calls.length,
};

describe("Firebase configuration", () => {
  it("does not initialize Firebase while the module is imported", () => {
    expect(importCalls).toEqual({ getAuth: 0, initializeApp: 0 });
  });

  it("initializes Firebase when authentication is requested", () => {
    expect(getFirebaseAuth()).toBe(firebaseMocks.auth);
    expect(firebaseMocks.initializeApp).toHaveBeenCalledOnce();
    expect(firebaseMocks.getAuth).toHaveBeenCalledWith(firebaseMocks.app);
  });

  it("analytics initialization does not depend on getFirebaseAuth", () => {
    // getFirebaseApp can be called independently without triggering auth
    // App is already initialized from previous test, so getAuth should still be at 1 call
    const authCallsBefore = firebaseMocks.getAuth.mock.calls.length;

    expect(getFirebaseApp()).toBe(firebaseMocks.app);
    expect(firebaseMocks.getAuth).toHaveBeenCalledTimes(authCallsBefore);
  });
});
