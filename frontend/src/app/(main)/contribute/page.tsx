"use client";

import { Button, Card, Input, Label, TextField } from "@heroui/react";
import { useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import clsx from "clsx";
import { Trans, useLingui } from "@lingui/react/macro";
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

export type SubmitSchemeParams = {
  typeOfRequest: "New";
  Link: string;
  Scheme: string;
};

export default function ContributePage() {
  const { t } = useLingui();
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
        message: t`Enter the scheme name.`,
      });
      return false;
    }
    if (!formData.Link?.trim()) {
      setSubmitStatus({
        type: "error",
        message: t`Enter the link to the scheme's page.`,
      });
      return false;
    }
    try {
      const schemeUrl = new URL(formData.Link);
      if (
        !["http:", "https:"].includes(schemeUrl.protocol) ||
        !schemeUrl.hostname
      ) {
        throw new Error("Unsupported scheme URL");
      }
    } catch {
      setSubmitStatus({
        type: "error",
        message: t`Enter the full link, including http:// or https://`,
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
          message: t`Thanks, we’ve received your suggestion. A volunteer will review it.`,
        });
        setFormData({});
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || t`We couldn’t send your suggestion. Check your connection and try again.`,
        });
      }
    } catch {
      setSubmitStatus({
        type: "error",
        message: t`We couldn’t send your suggestion. Try again in a few minutes.`,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageShell width="form">
      <div className="mb-6 flex flex-col gap-2 text-left">
        <h1 className={productHeading}>
          <Trans>Suggest a new scheme</Trans>
        </h1>
        <p className={productSubheading}>
          <Trans>
            Know a scheme that&apos;s missing from our database? Share it with us!
          </Trans>
        </p>
      </div>

      <Card className={`${productCardPadded} shadow-none`}>
        <Card.Content>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4 text-sm">
              <p className="mb-2 font-semibold text-(--schemes-status-info-text)">
                <Trans>How it works:</Trans>
              </p>
              <ol className="list-inside list-decimal space-y-1 text-(--schemes-muted)">
                <li>
                  <Trans>You provide the scheme name and link</Trans>
                </li>
                <li>
                  <Trans>
                    An AI tool collects the public details from the page
                  </Trans>
                </li>
                <li>
                  <Trans>A volunteer reviews and approves the listing</Trans>
                </li>
              </ol>
            </div>

            <TextField isRequired>
              <Label className={productFormLabel}>
                <Trans>Scheme name</Trans>
              </Label>
              <Input
                placeholder={t`e.g., ComCare Short-to-Medium Term Assistance`}
                value={formData.Scheme || ""}
                onChange={(e) => handleInputChange("Scheme", e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
              />
            </TextField>

            <TextField isRequired>
              <Label className={productFormLabel}>
                <Trans>Scheme link</Trans>
              </Label>
              <Input
                placeholder={t`e.g., https://www.msf.gov.sg/comcare`}
                type="url"
                value={formData.Link || ""}
                onChange={(e) => handleInputChange("Link", e.target.value)}
                variant="primary"
                className={`${productInputSurface} ${productInputText}`}
              />
              <p className="mt-1 text-xs text-(--schemes-muted)">
                <Trans>
                  The official webpage where details about this scheme can be
                  found
                </Trans>
              </p>
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
              className={`${productButtonSolidAmber} ${productButtonProminent} h-auto w-full whitespace-normal text-center sm:w-fit sm:self-end`}
            >
              {isSubmitting ? t`Submitting…` : t`Submit scheme`}
            </Button>
          </form>
        </Card.Content>
      </Card>
    </PageShell>
  );
}
