import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ContributePage from "@/app/(main)/contribute/page";
import FeedbackPage from "@/app/(main)/feedback/page";
import { AppProviders } from "@/providers";
import { TEST_API_URL } from "@/test/mocks/handlers";
import { server } from "@/test/mocks/server";

vi.mock("@/lib/auth-gateway", () => ({
  getAuthToken: async () => "test-auth-token",
  observeAuthState: (listener: (user: { uid: string }) => void) => {
    listener({ uid: "test-user" });
    return () => undefined;
  },
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

type CapturedRequest = {
  authorization: string | null;
  body: unknown;
};

type SubmissionEndpoint = "feedback" | "update_scheme";

type MockSubmissionResponse = {
  body: { success: boolean; message?: string };
  status?: number;
};

function renderWithProviders(children: ReactNode) {
  return render(<AppProviders>{children}</AppProviders>);
}

function mockSubmission(
  endpoint: SubmissionEndpoint,
  requests: CapturedRequest[],
  response: MockSubmissionResponse = { body: { success: true } },
) {
  server.use(
    http.post(`${TEST_API_URL}/${endpoint}`, async ({ request }) => {
      requests.push({
        authorization: request.headers.get("authorization"),
        body: await request.json(),
      });
      return HttpResponse.json(response.body, {
        status: response.status ?? 200,
      });
    }),
  );
}

describe("feedback and contribution flows", () => {
  let feedbackRequests: CapturedRequest[];
  let contributionRequests: CapturedRequest[];

  beforeEach(() => {
    feedbackRequests = [];
    contributionRequests = [];
    window.history.replaceState({}, "", "/");
  });

  it("submits scheme feedback with its context and announces success", async () => {
    window.history.replaceState(
      {},
      "",
      "/feedback?source=scheme&schemeId=child-care-subsidy&scheme=Child+Care+Subsidy",
    );
    mockSubmission("feedback", feedbackRequests);

    renderWithProviders(<FeedbackPage />);
    const user = userEvent.setup();
    const feedback = screen.getByRole("textbox", { name: "Your feedback" });

    expect(feedback).toHaveValue(
      "Scheme correction\nScheme ID: child-care-subsidy\nScheme: Child Care Subsidy\n\n",
    );
    await user.type(feedback, "The eligibility information is outdated.");
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Aisha");
    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "aisha@example.com",
    );
    await user.click(
      screen.getByRole("button", { name: "Submit Feedback" }),
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Thank you for your feedback!",
    );
    await waitFor(() => expect(feedbackRequests).toHaveLength(1));
    expect(feedbackRequests[0]).toEqual({
      authorization: "Bearer test-auth-token",
      body: {
        feedbackText:
          "Scheme correction\nScheme ID: child-care-subsidy\nScheme: Child Care Subsidy\n\nThe eligibility information is outdated.",
        userName: "Aisha",
        userEmail: "aisha@example.com",
      },
    });
  });

  it("preserves negative chat feedback context when the API fails", async () => {
    window.history.replaceState(
      {},
      "",
      "/feedback?source=chat&sentiment=negative",
    );
    mockSubmission("feedback", feedbackRequests, {
      body: { success: false, message: "Feedback service unavailable" },
      status: 503,
    });

    renderWithProviders(<FeedbackPage />);
    const user = userEvent.setup();
    const feedback = screen.getByRole("textbox", { name: "Your feedback" });

    expect(feedback).toHaveValue(
      "Chat response feedback (not helpful):\n\n",
    );
    await user.type(feedback, "The response missed the relevant scheme.");
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Ben");
    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "ben@example.com",
    );
    await user.click(
      screen.getByRole("button", { name: "Submit Feedback" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Feedback service unavailable",
    );
    await waitFor(() => expect(feedbackRequests).toHaveLength(1));
    expect(feedbackRequests[0]).toEqual({
      authorization: "Bearer test-auth-token",
      body: {
        feedbackText:
          "Chat response feedback (not helpful):\n\nThe response missed the relevant scheme.",
        userName: "Ben",
        userEmail: "ben@example.com",
      },
    });
  });

  it("does not invent negative sentiment for unrated chat feedback", async () => {
    window.history.replaceState({}, "", "/feedback?source=chat");
    mockSubmission("feedback", feedbackRequests);

    renderWithProviders(<FeedbackPage />);
    const user = userEvent.setup();
    const feedback = screen.getByRole("textbox", { name: "Your feedback" });

    expect(feedback).toHaveValue("Chat response feedback:\n\n");
    await user.type(feedback, "Please explain why this scheme was suggested.");
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Devi");
    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "devi@example.com",
    );
    await user.click(
      screen.getByRole("button", { name: "Submit Feedback" }),
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Thank you for your feedback!",
    );
    await waitFor(() => expect(feedbackRequests).toHaveLength(1));
    expect(feedbackRequests[0].body).toEqual({
      feedbackText:
        "Chat response feedback:\n\nPlease explain why this scheme was suggested.",
      userName: "Devi",
      userEmail: "devi@example.com",
    });
  });

  it("enforces required feedback fields and a valid email before the API", async () => {
    mockSubmission("feedback", feedbackRequests);

    renderWithProviders(<FeedbackPage />);
    const user = userEvent.setup();
    const name = screen.getByRole("textbox", { name: "Name" });
    const email = screen.getByRole("textbox", { name: "Email" });
    const feedback = screen.getByRole("textbox", { name: "Your feedback" });
    const submit = screen.getByRole("button", { name: "Submit Feedback" });

    expect(name).toBeRequired();
    expect(email).toBeRequired();
    expect(feedback).toBeRequired();
    await user.click(submit);
    expect(name).toBeInvalid();
    expect(feedbackRequests).toEqual([]);

    await user.type(name, "Chen");
    await user.type(email, "not-an-email");
    await user.type(feedback, "Please add clearer application dates.");
    await user.click(submit);

    expect(email).toBeInvalid();
    expect(feedbackRequests).toEqual([]);
  });

  it("enforces required contribution fields before the API", async () => {
    mockSubmission("update_scheme", contributionRequests);

    renderWithProviders(<ContributePage />);
    const user = userEvent.setup();
    const schemeName = screen.getByRole("textbox", { name: "Scheme name" });
    const schemeLink = screen.getByRole("textbox", { name: "Scheme link" });

    expect(schemeName).toBeRequired();
    expect(schemeLink).toBeRequired();
    await user.click(screen.getByRole("button", { name: "Submit Scheme" }));

    expect(schemeName).toBeInvalid();
    expect(schemeLink).toBeInvalid();
    expect(contributionRequests).toEqual([]);
  });

  it("rejects a non-HTTP contribution link before the API", async () => {
    mockSubmission("update_scheme", contributionRequests);

    renderWithProviders(<ContributePage />);
    const user = userEvent.setup();
    await user.type(
      screen.getByRole("textbox", { name: "Scheme name" }),
      "Community Support Grant",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Scheme link" }),
      "javascript:alert(1)",
    );
    await user.click(screen.getByRole("button", { name: "Submit Scheme" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Please enter a valid URL (e.g., https://example.com).",
    );
    expect(contributionRequests).toEqual([]);
  });

  it("submits the public contribution contract and announces success", async () => {
    mockSubmission("update_scheme", contributionRequests);

    renderWithProviders(<ContributePage />);
    const user = userEvent.setup();
    const schemeName = screen.getByRole("textbox", { name: "Scheme name" });
    const schemeLink = screen.getByRole("textbox", { name: "Scheme link" });
    await user.type(schemeName, "Community Support Grant");
    await user.type(schemeLink, "https://support.example.test/grant");
    await user.click(screen.getByRole("button", { name: "Submit Scheme" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Thank you! Your submission has been received.",
    );
    await waitFor(() => expect(contributionRequests).toHaveLength(1));
    expect(contributionRequests[0]).toEqual({
      authorization: "Bearer test-auth-token",
      body: {
        typeOfRequest: "New",
        Scheme: "Community Support Grant",
        Link: "https://support.example.test/grant",
      },
    });
    expect(schemeName).toHaveValue("");
    expect(schemeLink).toHaveValue("");
  });

  it("keeps the contribution values and announces an API failure", async () => {
    mockSubmission("update_scheme", contributionRequests, {
      body: { success: false, message: "Contribution service unavailable" },
      status: 503,
    });

    renderWithProviders(<ContributePage />);
    const user = userEvent.setup();
    const schemeName = screen.getByRole("textbox", { name: "Scheme name" });
    const schemeLink = screen.getByRole("textbox", { name: "Scheme link" });
    await user.type(schemeName, "Community Support Grant");
    await user.type(schemeLink, "https://support.example.test/grant");
    await user.click(screen.getByRole("button", { name: "Submit Scheme" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Contribution service unavailable",
    );
    await waitFor(() => expect(contributionRequests).toHaveLength(1));
    expect(schemeName).toHaveValue("Community Support Grant");
    expect(schemeLink).toHaveValue("https://support.example.test/grant");
  });
});
