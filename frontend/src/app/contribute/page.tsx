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
import { fetchWithAuth } from "@/app/utils/api";
import clsx from "clsx";

export type UpdateSchemeParams = {
  typeOfRequest?: "Update" | "New";
  Changes?: string;
  Description?: string;
  Link?: string;
  Scheme?: string;
  Status?: string;
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
    if (!updates.Scheme) {
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
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/update_scheme`,
        {
          method: "POST",
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
    <div className="w-full h-full overflow-y-scroll flex justify-center grow">
      <div className="max-w-[500px] sm:max-w-[800px] mx-auto p-2 sm:p-4">
        <div className={clsx("text-center mb-8", "flex flex-col gap-4")}>
          <p className="text-2xl sm:text-3xl font-extrabold">
            <span className="text-schemes-blue">Add or Edit a Listing</span>
          </p>
          <p className="font-medium text-center text-schemes-darkblue">
            Help us make the Schemes Bank more complete and accurate, and
            improve Schemes SG on the whole.
          </p>
        </div>

        <Card className="bg-white border border-schemes-lightgray shadow-none">
          <CardBody>
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <Input
                  label="Name"
                  placeholder="Enter your name"
                  value={updates.userName || ""}
                  onChange={(e) =>
                    handleInputChange("userName", e.target.value)
                  }
                  variant="bordered"
                  labelPlacement="outside"
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
                />
              </div>

              <Input
                label="Scheme"
                isRequired
                placeholder="Enter the scheme name"
                value={updates.Scheme || ""}
                onChange={(e) => handleInputChange("Scheme", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
              />

              <Input
                label="Link"
                placeholder="Enter the scheme link"
                type="url"
                value={updates.Link || ""}
                onChange={(e) => handleInputChange("Link", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
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
                value={updates.Description || ""}
                onChange={(e) =>
                  handleInputChange("Description", e.target.value)
                }
                variant="bordered"
                labelPlacement="outside"
                minRows={4}
              />

              <Textarea
                label="Changes"
                placeholder="Describe the changes"
                value={updates.Changes || ""}
                onChange={(e) => handleInputChange("Changes", e.target.value)}
                variant="bordered"
                labelPlacement="outside"
                minRows={4}
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
                {isSubmitting ? <Spinner color="white" size="sm" /> : "Submit"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
