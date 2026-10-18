"use client";

import {
  Button,
  Card,
  Input,
  Label,
  TextArea,
  TextField,
} from "@heroui/react";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchWithAuth } from "@/lib/api";
import clsx from "clsx";
import {
  productButtonProminent,
  productButtonSolidAmber,
  productCardPadded,
  productFormAlertMessage,
  productFormInfoMessage,
  productFormLabel,
  productHeading,
  productInputSurface,
  productInputText,
  productSubheading,
} from "@/lib/design-system/product-styles";
import PageShell from "@/components/layout/page-shell";

const FEEDBACK_CATEGORIES = [
  "Report wrong / missing information",
  "Report a bug",
  "Suggest a feature",
  "Partnerships & collaborations",
  "General feedback",
] as const;

type FeedbackCategory = (typeof FEEDBACK_CATEGORIES)[number];

function getFeedbackContext(searchParams: URLSearchParams) {
  const source = searchParams.get("source");

  if (source === "chat") {
    const sentiment = searchParams.get("sentiment");
    let sentimentContext = "";
    if (sentiment === "positive") sentimentContext = " (helpful)";
    if (sentiment === "negative") sentimentContext = " (not helpful)";
    return {
      label: "Feedback about a chat response",
      draft: `Chat response feedback${sentimentContext}:\n\n`,
      source: "chat",
      sentiment:
        sentiment === "positive" || sentiment === "negative"
          ? sentiment
          : null,
      schemeId: null,
      schemeName: null,
    };
  }

  if (source === "scheme") {
    const schemeId = searchParams.get("schemeId")?.trim() || null;
    const schemeName = searchParams.get("scheme")?.trim() || null;

    const details = [
      schemeId ? `Scheme ID: ${schemeId}` : null,
      schemeName ? `Scheme: ${schemeName}` : null,
    ].filter(Boolean);

    return {
      label: schemeName
        ? `Suggest a correction for ${schemeName}`
        : "Suggest a scheme correction",
      draft: `Scheme correction${
        details.length ? `\n${details.join("\n")}` : ""
      }\n\n`,
      source: "scheme",
      sentiment: null,
      schemeId,
      schemeName,
    };
  }

  return null;
}

function FeedbackForm() {
  const searchParams = useSearchParams();
  const feedbackContext = getFeedbackContext(searchParams);
  const [feedbackText, setFeedbackText] = useState(
    () => feedbackContext?.draft ?? "",
  );
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [feedbackCategory, setFeedbackCategory] =
    useState<FeedbackCategory | "">(
      feedbackContext?.source === "scheme"
        ? "Report wrong / missing information"
        : "General feedback",
    );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const validateForm = () => {
    if (
      !userName.trim() ||
      !userEmail.trim() ||
      !feedbackText.trim() ||
      !feedbackCategory
    ) {
      setSubmitStatus({
        type: "error",
        message: "Please fill in all required fields",
      });
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(userEmail.trim())) {
      setSubmitStatus({
        type: "error",
        message: "Please enter a valid email address",
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isSubmitting || !validateForm()) return;

    setIsSubmitting(true);
    setSubmitStatus(null);
    try {
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`,
        {
          method: "POST",
          body: JSON.stringify({
            feedbackText: feedbackText.trim(),
            userName: userName.trim(),
            userEmail: userEmail.trim(),
            feedbackCategory,
            source: feedbackContext?.source ?? "general",
            sentiment: feedbackContext?.sentiment ?? null,
            schemeId: feedbackContext?.schemeId ?? null,
            schemeName: feedbackContext?.schemeName ?? null,
          }),
        },
      );
      const data = await response.json();
      if (response.ok) {
        setSubmitStatus({
          type: "success",
          message: "Thank you for your feedback!",
        });
        setFeedbackText("");
        setUserName("");
        setUserEmail("");
        setFeedbackCategory("");
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || "Failed to submit feedback",
        });
      }
    } catch {
      setSubmitStatus({
        type: "error",
        message: "An error occurred while submitting feedback",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageShell width="form">
      <div className="mb-6 flex flex-col gap-2 text-left">
        <h1 className={productHeading}>Share feedback</h1>
        <p className={productSubheading}>
          Help us improve Schemes.sg with your valuable input
        </p>
        {feedbackContext && (
          <p className="mt-1 text-sm font-semibold text-(--schemes-blue-600)">
            {feedbackContext.label}
          </p>
        )}
      </div>
      <Card className={`${productCardPadded} shadow-none`}>
        <Card.Content>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <TextField isRequired>
                <Label className={productFormLabel}>Name</Label>
                <Input
                  placeholder="Enter your name"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  variant="primary"
                  className={`${productInputSurface} ${productInputText}`}
                />
              </TextField>
              <TextField isRequired>
                <Label className={productFormLabel}>Email</Label>
                <Input
                  placeholder="Enter your email"
                  type="email"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  variant="primary"
                  className={`${productInputSurface} ${productInputText}`}
                />
              </TextField>
            </div>
            <div className="flex flex-col gap-2">
              <label
                htmlFor="feedback-category"
                className={productFormLabel}
              >
                Feedback category
                <span aria-hidden="true"> *</span>
              </label>
              <select
                id="feedback-category"
                required
                value={feedbackCategory}
                onChange={(e) =>
                  setFeedbackCategory(
                    e.target.value as FeedbackCategory | "",
                  )
                }
                className={clsx(
                  productInputSurface,
                  productInputText,
                  "w-full rounded-lg px-3 py-3",
                )}
              >
                <option value="" disabled>
                  Select a feedback category
                </option>
                {FEEDBACK_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
            <TextField isRequired>
              <Label className={productFormLabel}>Your feedback</Label>
              <TextArea
                placeholder="Please share your thoughts, suggestions, or concerns"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
                rows={6}
              />
            </TextField>
            {submitStatus && (
              <div
                role={
                  submitStatus.type === "success" ? "status" : "alert"
                }
                className={clsx(
                  "leading-5",
                  submitStatus.type === "success"
                    ? productFormInfoMessage
                    : productFormAlertMessage,
                )}
              >
                {submitStatus.message}
              </div>
            )}
            <Button
              type="submit"
              variant="primary"
              isPending={isSubmitting}
              className={`${productButtonSolidAmber} ${productButtonProminent} w-full sm:w-fit sm:self-end`}
            >
              {isSubmitting ? "Submitting..." : "Submit Feedback"}
            </Button>
          </form>
        </Card.Content>
      </Card>
    </PageShell>
  );
}

function FeedbackFallback() {
  return (
    <PageShell width="form">
      <div className="mb-6 flex flex-col gap-2 text-left">
        <h1 className={productHeading}>Share feedback</h1>
        <p className={productSubheading}>
          Help us improve Schemes.sg with your valuable input
        </p>
      </div>
    </PageShell>
  );
}

export default function FeedbackPage() {
  return (
    <Suspense fallback={<FeedbackFallback />}>
      <FeedbackForm />
    </Suspense>
  );
}
