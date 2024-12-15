"use client";

import {
  Button,
  Card,
  CardBody,
  Input,
  Radio,
  RadioGroup,
  Spinner,
  Textarea,
} from "@nextui-org/react";
import { useState } from "react";
import classes from "./styleClasses.module.css";

export type UpdateSchemeParams = {
  typeOfRequest?: "Update" | "New";
  changes?: string;
  description?: string;
  link?: string;
  scheme?: string;
  status?: string;
  userName?: string;
  userEmail?: string;
};

export default function UpdateSchemesPage() {
  const [updates, setUpdates] = useState<UpdateSchemeParams>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const handleInputChange = (key: keyof UpdateSchemeParams, value: string) => {
    setUpdates((prev) => ({ ...prev, [key]: value }));
  };

  const validateForm = () => {
    if (!updates.scheme) {
      setSubmitStatus({
        type: "error",
        message: "Please fill in all required fields.",
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
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/${process.env.NEXT_PUBLIC_API_PROJECT}/${process.env.NEXT_PUBLIC_API_REGION}/update_scheme`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updates),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setSubmitStatus({
          type: "success",
          message: "Request for scheme update successfully added",
        });
        setUpdates({});
      } else {
        setSubmitStatus({
          type: "error",
          message: data.message || "Failed to submit the request",
        });
      }
    } catch (error) {
      setSubmitStatus({
        type: "error",
        message: "An error occurred while submitting the request",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <div className={classes.contentContainer}>
        <div className={classes.headerSection}>
          <p className={classes.title}>
            <span className={classes.highlight}>Add or Edit a Listing</span>
          </p>
          <p className="font-medium text-center" style={{ color: "#171347" }}>
            Help us make the Schemes Bank more complete and accurate, and
            improve Schemes SG on the whole.
          </p>
        </div>

        <Card className={classes.card}>
          <CardBody className={classes.cardBody}>
            <form onSubmit={handleSubmit} className={classes.form}>
              <div className={classes.inputGroup}>
                <Input
                  label="Name"
                  placeholder="Enter your name"
                  value={updates.userName || ""}
                  onChange={(e) =>
                    handleInputChange("userName", e.target.value)
                  }
                  variant="bordered"
                  labelPlacement="outside"
                  className={classes.input}
                />

                <Input
                  label="Email"
                  placeholder="Enter your email"
                  type="email"
                  value={updates.userEmail || ""}
                  onChange={(e) =>
                    handleInputChange("userEmail", e.target.value)
                  }
                  variant="bordered"
                  labelPlacement="outside"
                  className={classes.input}
                />
              </div>

              <Input
                label="Scheme"
                isRequired
                placeholder="Enter the scheme name"
                value={updates.scheme || ""}
                onChange={(e) => handleInputChange("scheme", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                className={classes.input}
              />

              <Input
                label="Link"
                placeholder="Enter the scheme link"
                type="url"
                value={updates.link || ""}
                onChange={(e) => handleInputChange("link", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                className={classes.input}
              />

              <RadioGroup
                label="Type of Request"
                size="sm"
                isRequired
                value={updates.typeOfRequest || ""}
                onValueChange={(val) => handleInputChange("typeOfRequest", val)}
                orientation="horizontal"
                aria-labelledby="type-of-request"
              >
                <Radio value="Update">Update</Radio>
                <Radio value="New">New</Radio>
              </RadioGroup>

              <Textarea
                label="Description"
                placeholder="Enter a description"
                value={updates.description || ""}
                onChange={(e) =>
                  handleInputChange("description", e.target.value)
                }
                variant="bordered"
                labelPlacement="outside"
                minRows={4}
                className={classes.textarea}
              />

              <Textarea
                label="Changes"
                placeholder="Describe the changes"
                value={updates.changes || ""}
                onChange={(e) => handleInputChange("changes", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                minRows={4}
                className={classes.textarea}
              />

              {submitStatus && (
                <div
                  className={
                    submitStatus.type === "success"
                      ? classes.successMessage
                      : classes.errorMessage
                  }
                >
                  {submitStatus.message}
                </div>
              )}

              <Button
                type="submit"
                color="primary"
                className={classes.submitButton}
                isDisabled={isSubmitting}
              >
                {isSubmitting ? <Spinner color="white" size="sm" /> : "Submit"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
