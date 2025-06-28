"use client";

import {
  AdditionalInfoType,
  ApplicationType,
  ContactType,
  EligibilityType,
  RawSchemeData,
} from "@/app/interfaces/schemes";
import styles from "./scheme.module.css";
import { fetchWithAuth } from "@/app/utils/api";
import { SearchResScheme } from "@/components/schemes/schemes-list";
import {
  Button,
  Chip,
  Image,
  Link,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
} from "@heroui/react";
import SchemeSkeleton from "@/components/schemes/scheme-skeleton";
import Markdown from "react-markdown";
import { MailIcon } from "@/assets/icons/mail-icon";
import { LinkIcon } from "@/assets/icons/link-icon";
import { LocationIcon } from "@/assets/icons/location-icon";
import { PhoneIcon } from "@/assets/icons/phone-icon";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";

// Type for full scheme properties
type Scheme = SearchResScheme & {
  lastUpdated?: string;
  eligibility?: EligibilityType;
  application?: ApplicationType;
  contact?: ContactType;
  additionalInfo?: AdditionalInfoType;
  // Additional fields directly from API
  phone?: string;
  email?: string;
  address?: string;
  howToApply?: string;
  eligibilityText?: string;
};

interface FullSchemeData extends RawSchemeData {
  "Last Updated": string;
  Eligibility?: EligibilityType;
  Application?: ApplicationType;
  Contact?: ContactType;
  "Additional Info"?: AdditionalInfoType;
  // Additional fields that might be in the API response
  phone?: string;
  email?: string;
  address?: string;
  how_to_apply?: string;
  eligibility?: string;
}

interface ApiSchemeData {
  scheme_type?: string;
  scheme?: string;
  who_is_it_for?: string;
  agency?: string;
  description?: string;
  llm_description?: string;
  scraped_text?: string;
  what_it_gives?: string;
  link?: string;
  image?: string;
  search_booster?: string;
  scheme_id?: string;
  query?: string;
  similarity?: number;
  quintile?: number;
  phone?: string;
  email?: string;
  address?: string;
  how_to_apply?: string;
  eligibility?: string;
  last_modified_date?: number;
}

const mapToFullScheme = (rawData: FullSchemeData): Scheme => {
  return {
    // Properties from Scheme
    schemeType: rawData["Scheme Type"] || "",
    schemeName: rawData["Scheme"] || "",
    targetAudience: rawData["Who's it for"] || "",
    agency: rawData["Agency"] || "",
    description: rawData["Description"] || "",
    scrapedText: rawData["scraped_text"] || "",
    benefits: rawData["What it gives"] || "",
    link: rawData["Link"] || "",
    image: rawData["Image"] || "",
    searchBooster: rawData["search_booster(WL)"] || "",
    schemeId: rawData["scheme_id"] || "",
    query: rawData["query"] || "",
    similarity: rawData["Similarity"] || 0,
    quintile: rawData["Quintile"] || 0,
    planningArea: rawData["planning_area"] || "",
    summary: rawData["summary"] || "",

    // Direct access to contact fields
    phone: rawData["phone"] || "",
    email: rawData["email"] || "",
    address: rawData["address"] || "",
    howToApply: rawData["how_to_apply"] || "",
    eligibilityText: rawData["eligibility"] || "",

    // Additional properties for FullScheme
    lastUpdated: rawData["Last Updated"] || "",
    eligibility: rawData["Eligibility"] || undefined,
    application: rawData["Application"] || undefined,
    contact: rawData["Contact"] || undefined,
    additionalInfo: rawData["Additional Info"] || undefined,
  };
};

export default function SchemePage() {
  const { schemeId } = useParams();
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchScheme() {
      if (!schemeId) {
        console.error("schemeId is undefined or missing.");
        setError("Invalid schemeId");
        setIsLoading(false);
        return;
      }
      try {
        const id = Array.isArray(schemeId) ? schemeId[0] : schemeId;
        console.log("Fetching scheme data for ID:", id);

        const response = await fetchWithAuth(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes/${id}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch scheme");
        }
        const res = await response.json();
        console.log("Response data:", res); // Debug

        const schemeData = res.data as ApiSchemeData;

        // Handle the scheme data structure - map to our frontend format
        const schemeRes = {
          // Map from our formatted object
          ...mapToFullScheme({
            "Scheme Type": schemeData.scheme_type || "",
            Scheme: schemeData.scheme || "",
            "Who's it for": schemeData.who_is_it_for || "",
            Agency: schemeData.agency || "",
            Description:
              schemeData.llm_description || schemeData.description || "",
            scraped_text: schemeData.scraped_text || "",
            "What it gives": schemeData.what_it_gives || "",
            Link: schemeData.link || "",
            Image: schemeData.image || "",
            "search_booster(WL)": schemeData.search_booster || "",
            scheme_id: id, // Use the ID from the URL parameter
            query: "", // No query for single scheme view
            Similarity: 0, // Not applicable for single scheme view
            Quintile: 0, // Not applicable for single scheme view
            "Last Updated": schemeData.last_modified_date
              ? new Date(schemeData.last_modified_date).toLocaleString()
              : "",
            // Add additional fields from API response directly here instead of later
            phone: schemeData.phone || "",
            email: schemeData.email || "",
            address: schemeData.address || "",
            how_to_apply: schemeData.how_to_apply || "",
            eligibility: schemeData.eligibility || "",
          }),
        } as Scheme; // Use type assertion for the whole object

        console.log("Mapped scheme:", schemeRes); // Debug
        setScheme(schemeRes);
      } catch (err) {
        console.error("Error fetching scheme:", err);
        setError("An error occurred");
      } finally {
        setIsLoading(false);
      }
    }

    fetchScheme();

    console.log("Scheme page mounted, ID:", schemeId);
  }, [schemeId]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <p className="text-error text-center">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="h-full overflow-hidden bg-background p-4 w-full">
        <div className="max-w-5xl mx-auto">
          <SchemeSkeleton />
        </div>
      </div>
    );
  }

  return (
    scheme && (
      <div className="overflow-y-auto bg-background p-4 w-full">
        <div className="max-w-5xl mx-auto">
          {/* Title Section */}
          <div
            className={clsx(
              "text-center sm:text-left gap-4 mb-8",
              "flex flex-col sm:flex-row items-center",
            )}
          >
            <Image
              width={120}
              height={120}
              alt={`${scheme.agency} logo`}
              radius="sm"
              className="w-24 h-24 md:w-32 md:h-32 object-contain shadow-lg md:mb-0 mb-4"
              src={scheme.image}
            />
            <div className="flex flex-col gap-1">
              {scheme.agency && (
                <h1 className="text-3xl font-bold">{scheme.agency}</h1>
              )}
              {scheme.schemeName && (
                <h6 className="text-medium">{scheme.schemeName}</h6>
              )}
              {/* Action Buttons */}
              <div className="flex justify-center sm:justify-start gap-2 mt-2">
                {scheme.link && (
                  <Button
                    isIconOnly
                    size="sm"
                    aria-label="website"
                    color="primary"
                    variant="flat"
                    as={Link}
                    href={scheme.link}
                    isExternal
                  >
                    <LinkIcon size={20} />
                  </Button>
                )}
                {scheme.email && (
                  <Button
                    isIconOnly
                    size="sm"
                    aria-label="email"
                    color="primary"
                    variant="flat"
                    as={Link}
                    href={`mailto:${scheme.email}`}
                  >
                    <MailIcon size={20} />
                  </Button>
                )}
                {scheme.phone && (
                  <Button
                    isIconOnly
                    size="sm"
                    aria-label="phone"
                    color="primary"
                    variant="flat"
                    as={Link}
                    href={`tel:${scheme.phone.slice(
                      0,
                      scheme.phone.indexOf(",")
                    )}`}
                  >
                    <PhoneIcon size={20} />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Description Card */}
          <Card className="p-6 text-slate-700">
            <CardHeader>
              <h1 className="text-xl font-bold">Description</h1>
            </CardHeader>
            <CardBody>
              {scheme.description && (
                <Markdown className={`mb-5 ${styles.showMarker}`}>
                  {scheme.description}
                </Markdown>
              )}
            </CardBody>
          </Card>

          {/* Details Card */}
          <Card className="p-6 mt-10 text-slate-700">
            <CardHeader>
              <h1 className="text-xl font-bold">Details</h1>
            </CardHeader>
            <CardBody>
              <div className="sm:flex gap-5 mb-4">
                {/* main details */}
                <div className="flex-[2]">
                  <div className="sm:flex gap-5 mb-4">
                    {/* who */}
                    <div className="flex-1 mb-4">
                      <span className="font-bold uppercase text-xs text-slate-500 mb-2">
                        Who is it for
                      </span>
                      {scheme.targetAudience && (
                        <ul className="list-disc list-inside marker:text-slate-500">
                          {scheme.targetAudience.split(",").map((target) => (
                            <li key={target}>{target.trim()}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                    {/* what */}
                    <div className="flex-1">
                      <span className="font-bold uppercase text-xs text-slate-500 mb-2">
                        What it gives
                      </span>
                      {scheme.benefits && (
                        <ul className="list-disc list-inside marker:text-slate-500">
                          {scheme.benefits.split(",").map((benefit) => (
                            <li key={benefit}>{benefit.trim()}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                  <div className="mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500 mb-2">
                      Who can apply
                    </span>
                    {scheme.eligibilityText && <p>{scheme.eligibilityText}</p>}
                  </div>
                  <div className="mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500 mb-2">
                      How to apply
                    </span>
                    {scheme.howToApply && <p>{scheme.howToApply}</p>}
                  </div>
                </div>
                {/* other details */}
                <div className="flex-1">
                  {/* type */}
                  <div className="mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500 mb-2">
                      Type
                    </span>
                    {scheme.schemeType && (
                      <div className="flex flex-wrap gap-2">
                        {scheme.schemeType.split(",").map((type) => (
                          <Chip
                            key={type}
                            size="sm"
                            radius="sm"
                            color="primary"
                            variant="flat"
                          >
                            {type.trim()}
                          </Chip>
                        ))}
                      </div>
                    )}
                  </div>
                  {/* contacts */}
                  <div className="flex flex-col gap-2 mt-6">
                    {scheme.phone && (
                      <div>
                        <p className="font-bold uppercase text-xs text-slate-500 mb-1">
                          Phone
                        </p>
                        <p>{scheme.phone}</p>
                      </div>
                    )}
                    {scheme.email && (
                      <div>
                        <p className="font-bold uppercase text-xs text-slate-500 mb-1">
                          Email
                        </p>
                        <p>{scheme.email}</p>
                      </div>
                    )}
                    {scheme.address && (
                      <div>
                        <p className="font-bold uppercase text-xs text-slate-500 mb-1">
                          Location
                        </p>
                        {scheme.planningArea && (
                          <p>
                            <LocationIcon size={20} />
                            <span>{scheme.planningArea}</span>
                          </p>
                        )}
                        <p>{scheme.address}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardBody>
            <CardFooter className="gap-4 justify-center sm:justify-end">
              {scheme.address && (
                <Button
                  color="primary"
                  endContent={<LocationIcon size={20} />}
                  variant="ghost"
                  as={Link}
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                    scheme.address
                  )}`}
                  isExternal
                >
                  Get Directions
                </Button>
              )}
              {scheme.link && (
                <Button
                  color="primary"
                  endContent={<LinkIcon size={20} />}
                  variant="ghost"
                  as={Link}
                  href={scheme.link}
                  isExternal
                >
                  Find out more
                </Button>
              )}
            </CardFooter>
          </Card>

          {/* Add disclaimer section at the bottom */}
          <section className="mt-20 mb-8 border border-neutral-200 rounded-lg p-4 bg-neutral-50">
            <div className="flex items-start gap-3">
              <div className="text-neutral-500 text-lg">ⓘ</div>
              <div>
                <h3 className="text-sm font-semibold text-neutral-700 mb-1">
                  Important Information
                </h3>
                <p className="text-sm text-neutral-600">
                  We strive to provide accurate information about assistance
                  schemes in Singapore. Program details may change over time, so
                  please visit the official website for the most current
                  information.{" "}
                  <Link href="/feedback" className="text-primary text-sm">
                    Help us improve with your feedback
                  </Link>
                  .
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    )
  );
}
