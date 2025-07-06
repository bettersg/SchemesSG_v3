"use client";

import {
  AdditionalInfoType,
  ApplicationType,
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
  Accordion,
  AccordionItem,
} from "@heroui/react";
import SchemeSkeleton from "@/components/schemes/scheme-skeleton";
import Markdown from "react-markdown";
import { LinkIcon } from "@/assets/icons/link-icon";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { parseArrayString } from "@/app/utils/helper";
import SchemeContactCard from "@/components/schemes/scheme-contact-card";

// Type for full scheme properties
type Scheme = SearchResScheme & {
  lastUpdated?: string;
  eligibility?: EligibilityType;
  application?: ApplicationType;
  contact?: BranchContact[];
  additionalInfo?: AdditionalInfoType;
  // Additional fields directly from API
  howToApply?: string;
  eligibilityText?: string;
  serviceArea?: string;
};

export type BranchContact = {
  planningArea?: string;
  phones?: string[];
  emails?: string[];
  address?: string;
};

interface FullSchemeData extends RawSchemeData {
  "Last Updated": string;
  Eligibility?: EligibilityType;
  Application?: ApplicationType;
  "Additional Info"?: AdditionalInfoType;
  // Additional fields that might be in the API response
  phone?: string[] | undefined;
  email?: string[] | undefined;
  address?: string[] | undefined;
  how_to_apply?: string;
  eligibility?: string;
  service_area?: string;
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
  phone?: string | string[];
  email?: string | string[];
  address?: string | string[];
  how_to_apply?: string;
  eligibility?: string;
  last_modified_date?: number;
  planning_area?: string;
  service_area?: string;
}

const mapToFullScheme = (rawData: FullSchemeData): Scheme => {
  const contacts: BranchContact[] = [];
  const planningArea = rawData.planning_area && rawData.planning_area != "No location" && parseArrayString(rawData.planning_area)
  // address field is defined. No of branch is length of address array
  if (planningArea) {
    for (let i = 0; i < planningArea.length; i++) {
      // if phone / email data is type string, display that phone / email for all branches
      contacts.push({
        planningArea: planningArea[i],
        phones:
          rawData.phone &&
          rawData.phone[Math.min(i, rawData.phone.length - 1)].split(","),
        emails:
          rawData.email &&
          rawData.email[Math.min(i, rawData.email.length - 1)].split(","),
        address: rawData.address && rawData.address[i],
      });
    }
  } else {
    // no physical branch. Group contact details together
    contacts.push({
      phones: rawData.phone && rawData.phone,
      emails: rawData.email && rawData.email,
    });
  }
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
    contact: contacts,
    howToApply: rawData["how_to_apply"] || "",
    eligibilityText: rawData["eligibility"] || "",

    // Additional properties for FullScheme
    lastUpdated: rawData["Last Updated"] || "",
    eligibility: rawData["Eligibility"] || undefined,
    application: rawData["Application"] || undefined,
    // contact: rawData["Contact"] || undefined,
    additionalInfo: rawData["Additional Info"] || undefined,
    serviceArea: rawData["service_area"] || "",
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
        const fullSchemeData: FullSchemeData = {
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
        phone: parseArrayString(schemeData.phone),
        email: parseArrayString(schemeData.email),
        address: parseArrayString(schemeData.address),
        how_to_apply: schemeData.how_to_apply || "",
        eligibility: schemeData.eligibility || "",
        planning_area: schemeData.planning_area || "",
        service_area: schemeData.service_area || "",
        };
        // Map from our formatted object
        const schemeRes = mapToFullScheme(fullSchemeData) as Scheme; // Use type assertion for the whole object

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
              "flex flex-col sm:flex-row items-center"
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
            <div className="flex flex-col gap-2 items-center sm:items-start">
              {scheme.agency && (
                <h1 className="text-3xl font-bold">{scheme.agency}</h1>
              )}
              {scheme.schemeName && (
                <h6 className="text-medium">{scheme.schemeName}</h6>
              )}
              {/* Action Buttons */}
              {scheme.link && (
                <Button
                  className="w-min"
                  color="primary"
                  endContent={<LinkIcon size={20} />}
                  variant="light"
                  as={Link}
                  href={scheme.link}
                  isExternal
                >
                  Find out more
                </Button>
              )}
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
                    <div className="flex flex-col gap-2 flex-1 mb-4">
                      <span className="font-bold uppercase text-xs text-slate-500">
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
                    <div className="flex flex-col gap-2 flex-1">
                      <span className="font-bold uppercase text-xs text-slate-500">
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
                  <div className="flex flex-col gap-2 mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500">
                      Who can apply
                    </span>
                    {scheme.eligibilityText && <p>{scheme.eligibilityText}</p>}
                  </div>
                  <div className="flex flex-col gap-2 mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500">
                      How to apply
                    </span>
                    {scheme.howToApply && <p>{scheme.howToApply}</p>}
                  </div>
                </div>
                {/* other details */}
                <div className="flex flex-col flex-1 overflow-y-hidden">
                  {/* type */}
                  <div className="flex flex-col gap-2 mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500">
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
                  {/* service area */}
                  {scheme.serviceArea && (
                    <div className="flex flex-col gap-2 mb-4">
                    <span className="font-bold uppercase text-xs text-slate-500">
                      Service Area
                    </span>
                    <p>{scheme.serviceArea}</p>
                    </div>
                  )}
                  {/* contacts */}
                  {scheme.contact && scheme.planningArea && (
                    <div className="flex flex-col gap-2">
                      <span className="font-bold uppercase text-xs text-slate-500">
                        Contact
                      </span>
                      {/* multiple planning areas */}
                      {typeof scheme.planningArea == "object" ? (
                        <Accordion
                          defaultExpandedKeys={
                            Array.from(new Set(scheme.planningArea)).length === 1
                              ? Array.from(new Set(scheme.planningArea))
                              : []
                          }
                        >
                          {Array.from(new Set(scheme.planningArea)).map((area, index) => (
                            <AccordionItem key={area} title={area}>
                              <div className="flex flex-col gap-4">
                                {scheme.contact && scheme.contact.filter(contact => contact.planningArea == area).map((contact, index) => (
                                  <SchemeContactCard
                                    contact={contact}
                                    key={index}
                                  />
                                ))}
                              </div>
                            </AccordionItem>
                          ))}
                        </Accordion>
                      ) : (
                        // one or no planning areas
                        <div className="flex flex-col gap-4 p-1">
                          {scheme.contact.map((contact, index) => (
                            <SchemeContactCard contact={contact} key={index} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardBody>
            <CardFooter className="flex flex-wrap gap-4 justify-center sm:justify-end">
              {scheme.link && (
                <Button
                  color="primary"
                  endContent={<LinkIcon size={20} />}
                  variant="solid"
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
