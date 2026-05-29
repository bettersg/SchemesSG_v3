"use client";

import { Button, Card, Input, Label, TextField } from "@heroui/react";
import { useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import clsx from "clsx";
import {
  productButtonLg,
  productButtonPrimary,
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

export type SubmitSchemeParams = {
  typeOfRequest: "New";
  Link: string;
  Scheme: string;
};

export default function ContributePage() {
  const [formData, setFormData] = useState<Partial<SubmitSchemeParams>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const handleInputChange = (key: keyof SubmitSchemeParams, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    if (submitStatus?.type === "error") setSubmitStatus(null);
  };

  const validateForm = () => {
    if (!formData.Scheme?.trim()) {
      setSubmitStatus({
        type: "error",
        message: "Please enter the scheme name.",
      });
      return false;
    }
    if (!formData.Link?.trim()) {
      setSubmitStatus({
        type: "error",
        message: "Please enter the scheme link.",
      });
      return false;
    }
    try {
      new URL(formData.Link);
    } catch {
      setSubmitStatus({
        type: "error",
        message: "Please enter a valid URL (e.g., https://example.com).",
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitStatus(null);
    if (!validateForm()) return;
    setIsSubmitting(true);
    try {
      const payload: SubmitSchemeParams = {
        typeOfRequest: "New",
        Scheme: formData.Scheme!,
        Link: formData.Link!,
      };
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/update_scheme`,
        { method: "POST", body: JSON.stringify(payload) },
      );
      const data = await response.json();
      if (response.ok) {
        setSubmitStatus({
          type: "success",
          message:
            "Thank you! Your submission has been received. We'll review it within a week.",
        });
        setFormData({});
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || "Failed to submit. Please try again.",
        });
      }
    } catch {
      setSubmitStatus({
        type: "error",
        message: "An error occurred. Please try again later.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageShell width="form">
      <div className="mb-6 flex flex-col gap-2 text-left">
        <h1 className={productHeading}>Suggest a new scheme</h1>
        <p className={productSubheading}>
          Know a scheme that&apos;s missing from our database? Share it with us!
        </p>
      </div>

      <Card className={`${productCardPadded} shadow-none`}>
        <Card.Content>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4 text-sm">
              <p className="mb-2 font-semibold text-(--schemes-status-info-text)">
                How it works:
              </p>
              <ol className="list-inside list-decimal space-y-1 text-(--schemes-muted)">
                <li>You provide the scheme name and link</li>
                <li>
                  AI agents responsibly gather publicly available details from
                  the webpage
                </li>
                <li>A volunteer reviews and approves the listing</li>
              </ol>
              <p className="mt-3 text-(--schemes-muted)">
                Expected turnaround: ~1 week
              </p>
            </div>

            <TextField isRequired>
              <Label className={productFormLabel}>Scheme name</Label>
              <Input
                placeholder="e.g., ComCare Short-to-Medium Term Assistance"
                value={formData.Scheme || ""}
                onChange={(e) => handleInputChange("Scheme", e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
              />
            </TextField>

            <TextField isRequired>
              <Label className={productFormLabel}>Scheme link</Label>
              <Input
                placeholder="e.g., https://www.msf.gov.sg/comcare"
                type="url"
                value={formData.Link || ""}
                onChange={(e) => handleInputChange("Link", e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
              />
              <p className="mt-1 text-xs text-(--schemes-muted)">
                The official webpage where details about this scheme can be
                found
              </p>
            </TextField>

            {submitStatus && (
              <div
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
              className={`${productButtonPrimary} ${productButtonLg} w-full sm:w-fit sm:self-end`}
            >
              {isSubmitting ? "Submitting..." : "Submit Scheme"}
            </Button>
          </form>
        </Card.Content>
      </Card>
    </PageShell>
  );
}
