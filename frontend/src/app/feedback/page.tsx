"use client";

import { Button, Card, CardBody, Input, Textarea } from "@nextui-org/react";
import { useState } from "react";
import styles from "./feedback.module.css";

export default function FeedbackPage() {
  const [feedbackText, setFeedbackText] = useState("");
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!feedbackText.trim()) {
      setSubmitStatus({
        type: "error",
        message: "Please provide your feedback",
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus({ type: null, message: "" });

    try {
      const response = await fetch(
        "http://localhost:5001/schemessg-v3-dev/asia-southeast1/feedback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
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
    <div>
      <div className={styles.contentContainer}>
        <div className={styles.headerSection}>
          <p className={styles.title}>
            Share Your <span className={styles.highlight}>Feedback</span>
          </p>
          <p className="font-medium text-center" style={{ color: "#171347" }}>
            Help us improve Schemes SG with your valuable input
          </p>
        </div>

        <Card className={styles.card}>
          <CardBody className={styles.cardBody}>
            <form onSubmit={handleSubmit} className={styles.form}>
              <div className={styles.inputGroup}>
                <Input
                  label="Name"
                  placeholder="Enter your name"
                  value={userName}
                  required
                  onChange={(e) => setUserName(e.target.value)}
                  variant="bordered"
                  labelPlacement="outside"
                  className={styles.input}
                />

                <Input
                  label="Email"
                  placeholder="Enter your email"
                  type="email"
                  required
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  variant="bordered"
                  labelPlacement="outside"
                  className={styles.input}
                />
              </div>

              <Textarea
                label="Your Feedback"
                required
                placeholder="Please share your thoughts, suggestions, or concerns"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                isRequired
                minRows={6}
                className={styles.textarea}
              />

              {submitStatus.message && (
                <div
                  className={`${styles.statusMessage} ${
                    submitStatus.type === "success"
                      ? styles.successMessage
                      : styles.errorMessage
                  }`}
                >
                  {submitStatus.message}
                </div>
              )}

              <Button
                type="submit"
                color="primary"
                className={styles.submitButton}
                isLoading={isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Submit Feedback"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
