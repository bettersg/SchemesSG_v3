"use client";

import {
  Button,
  Card,
  CardBody,
  Input,
  Spinner,
} from "@heroui/react";
import { useState } from "react";
import { fetchWithAuth } from "@/app/utils/api";
import clsx from "clsx";

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
    // Clear error when user starts typing
    if (submitStatus?.type === "error") {
      setSubmitStatus(null);
    }
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
    // Basic URL validation
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

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload: SubmitSchemeParams = {
        typeOfRequest: "New",
        Scheme: formData.Scheme!,
        Link: formData.Link!,
      };

      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/update_scheme`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setSubmitStatus({
          type: "success",
          message: "Thank you! Your submission has been received. We'll review it within a week.",
        });
        setFormData({});
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || "Failed to submit. Please try again.",
        });
      }
    } catch (error) {
      setSubmitStatus({
        type: "error",
        message: "An error occurred. Please try again later.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full overflow-y-auto">
      <div
        className={clsx(
          "max-w-[400px] sm:max-w-[600px]",
          "mx-auto p-2 sm:p-4"
        )}
      >
        <div className={clsx("text-center my-8", "flex flex-col gap-4")}>
          <p className="text-2xl sm:text-3xl font-extrabold">
            <span className="text-schemes-blue">Suggest a New Scheme</span>
          </p>
          <p className="font-medium text-center text-schemes-darkblue">
            Know a scheme that&apos;s missing from our database? Share it with us!
          </p>
        </div>

        <Card className="bg-white border border-schemes-lightgray shadow-none">
          <CardBody>
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              {/* How it works section */}
              <div className="bg-blue-50 p-4 rounded-lg text-sm">
                <p className="font-semibold mb-2 text-schemes-darkblue">How it works:</p>
                <ol className="list-decimal list-inside space-y-1 text-gray-600">
                  <li>You provide the scheme name and link</li>
                  <li>AI agents responsibly gather publicly available details from the webpage</li>
                  <li>A volunteer reviews and approves the listing</li>
                </ol>
                <p className="mt-3 text-gray-500 text-xs">
                  Expected turnaround: ~1 week
                </p>
              </div>

              <Input
                label="Scheme Name"
                isRequired
                placeholder="e.g., ComCare Short-to-Medium Term Assistance"
                value={formData.Scheme || ""}
                onChange={(e) => handleInputChange("Scheme", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
              />

              <Input
                label="Scheme Link"
                isRequired
                placeholder="e.g., https://www.msf.gov.sg/comcare"
                type="url"
                value={formData.Link || ""}
                onChange={(e) => handleInputChange("Link", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                description="The official webpage where details about this scheme can be found"
              />

              {submitStatus && (
                <div
                  className={clsx(
                    "p-4 rounded-lg",
                    submitStatus.type === "success"
                      ? "successMessage"
                      : "errorMessage"
                  )}
                >
                  {submitStatus.message}
                </div>
              )}

              <Button type="submit" color="primary" isDisabled={isSubmitting}>
                {isSubmitting ? <Spinner color="white" size="sm" /> : "Submit Scheme"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
