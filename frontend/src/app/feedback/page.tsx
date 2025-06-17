"use client";

import { Button, Card, CardBody, Input, Textarea } from "@nextui-org/react";
import { useState } from "react";
import { fetchWithAuth } from "@/app/utils/api";
import clsx from "clsx";

export default function FeedbackPage() {
  const [feedbackText, setFeedbackText] = useState("");
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const validateForm = () => {
    if (!userName.trim() || !userEmail.trim() || !feedbackText.trim()) {
      setSubmitStatus({
        type: "error",
        message: "Please fill in all required fields",
      });
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(userEmail)) {
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

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`,
        {
          method: "POST",
          body: JSON.stringify({
            feedbackText,
            userName,
            userEmail,
          }),
        }
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
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || "Failed to submit feedback",
        });
      }
    } catch (error) {
      setSubmitStatus({
        type: "error",
        message: "An error occurred while submitting feedback",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
      <div className="max-w-[500px] sm:max-w-[800px] mx-auto p-2 sm:p-4 flex flex-col justify-center">
        <div className={clsx("text-center mb-8", "flex flex-col gap-4")}>
          <p className="text-2xl sm:text-3xl font-extrabold text-schemes-blue">
            Share Your <span>Feedback</span>
          </p>
          <p className="font-medium text-center text-schemes-darkblue">
            Help us improve Schemes SG with your valuable input
          </p>
        </div>

        <Card className="bg-white border border-schemes-lightgray shadow-none">
          <CardBody>
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <Input
                  label="Name"
                  placeholder="Enter your name"
                  value={userName}
                  isRequired
                  onChange={(e) => setUserName(e.target.value)}
                  variant="bordered"
                  labelPlacement="outside"
                />

                <Input
                  label="Email"
                  placeholder="Enter your email"
                  type="email"
                  isRequired
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  variant="bordered"
                  labelPlacement="outside"
                />
              </div>

              <Textarea
                label="Your Feedback"
                isRequired
                placeholder="Please share your thoughts, suggestions, or concerns"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                minRows={6}
              />

              {submitStatus.message && (
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

              <Button
                type="submit"
                color="primary"
                isLoading={isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Submit Feedback"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
  );
}
