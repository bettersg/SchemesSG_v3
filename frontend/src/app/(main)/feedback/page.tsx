"use client";

import { Button, Card, Input, Label, TextArea, TextField } from "@heroui/react";
import { Suspense, useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import clsx from "clsx";
import { Trans, useLingui } from "@lingui/react/macro";
import { msg } from "@lingui/core/macro";
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
import { useSearchParams } from "next/navigation";

function getFeedbackContext(searchParams: URLSearchParams) {
  const source = searchParams.get("source");

  if (source === "chat") {
    const sentiment = searchParams.get("sentiment");
    let sentimentContext = "";
    if (sentiment === "positive") sentimentContext = " (helpful)";
    if (sentiment === "negative") sentimentContext = " (not helpful)";
    return {
      label: msg`Feedback about a chat response`,
      draft: `Chat response feedback${sentimentContext}:\n\n`,
    };
  }

  if (source === "scheme") {
    const schemeId = searchParams.get("schemeId")?.trim();
    const schemeName = searchParams.get("scheme")?.trim();
    const details = [
      schemeId ? `Scheme ID: ${schemeId}` : null,
      schemeName ? `Scheme: ${schemeName}` : null,
    ].filter(Boolean);

    return {
      label: schemeName
        ? msg`Suggest a correction for ${schemeName}`
        : msg`Suggest a scheme correction`,
      draft: `Scheme correction${details.length ? `\n${details.join("\n")}` : ""}\n\n`,
    };
  }

  return null;
}

function FeedbackForm() {
  const { t, i18n } = useLingui();
  const searchParams = useSearchParams();
  const feedbackContext = getFeedbackContext(searchParams);
  const [feedbackText, setFeedbackText] = useState(
    () => feedbackContext?.draft ?? "",
  );
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const validateForm = () => {
    if (!userName.trim() || !userEmail.trim() || !feedbackText.trim()) {
      setSubmitStatus({
        type: "error",
        message: t`Fill in all the required fields.`,
      });
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(userEmail)) {
      setSubmitStatus({
        type: "error",
        message: t`Please enter a valid email address`,
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setIsSubmitting(true);
    try {
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`,
        {
          method: "POST",
          body: JSON.stringify({ feedbackText, userName, userEmail }),
        },
      );
      const data = await response.json();
      if (response.ok) {
        setSubmitStatus({
          type: "success",
          message: t`Thanks for your feedback.`,
        });
        setFeedbackText("");
        setUserName("");
        setUserEmail("");
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || t`We couldn’t send your feedback. Check your connection and try again.`,
        });
      }
    } catch {
      setSubmitStatus({
        type: "error",
        message: t`We couldn’t send your feedback. Check your connection and try again.`,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageShell width="form">
      <div className="mb-6 flex flex-col gap-2 text-left">
        <h1 className={productHeading}>
          <Trans>Share feedback</Trans>
        </h1>
        <p className={productSubheading}>
          <Trans>Help us improve Schemes.sg with your valuable input</Trans>
        </p>
        {feedbackContext && (
          <p className="mt-1 text-sm font-semibold text-(--schemes-blue-600)">
            {i18n._(feedbackContext.label)}
          </p>
        )}
      </div>
      <Card className={`${productCardPadded} shadow-none`}>
        <Card.Content>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <TextField isRequired>
                <Label className={productFormLabel}>
                  <Trans>Name</Trans>
                </Label>
                <Input
                  placeholder={t`Enter your name`}
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  variant="primary"
                  className={`${productInputSurface} ${productInputText}`}
                />
              </TextField>
              <TextField isRequired>
                <Label className={productFormLabel}>
                  <Trans>Email</Trans>
                </Label>
                <Input
                  placeholder={t`Enter your email`}
                  type="email"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  variant="primary"
                  className={`${productInputSurface} ${productInputText}`}
                />
              </TextField>
            </div>
            <TextField isRequired>
              <Label className={productFormLabel}>
                <Trans>Your feedback</Trans>
              </Label>
              <TextArea
                placeholder={t`Share your thoughts, suggestions, or concerns`}
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
                rows={6}
              />
            </TextField>
            {submitStatus && (
              <div
                role={submitStatus.type === "success" ? "status" : "alert"}
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
              {isSubmitting ? t`Submitting…` : t`Send feedback`}
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
        <h1 className={productHeading}>
          <Trans>Share feedback</Trans>
        </h1>
        <p className={productSubheading}>
          <Trans>Help us improve Schemes.sg with your valuable input</Trans>
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
