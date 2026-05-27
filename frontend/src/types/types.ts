export interface RawSchemeData {
  "Scheme Type"?: string[];
  Scheme?: string;
  "Who's it for"?: string[];
  Agency?: string;
  Description?: string;
  scraped_text?: string;
  "What it gives"?: string[];
  Link?: string;
  Image?: string;
  "search_booster(WL)"?: string;
  scheme_id?: string;
  id?: string;
  query?: string;
  Similarity?: number;
  Quintile?: number;

  // Lowercase properties from the backend
  scheme_type?: string[];
  scheme?: string;
  who_is_it_for?: string[];
  agency?: string;
  description?: string;
  what_it_gives?: string[];
  link?: string;
  image?: string;
  search_booster?: string;
  similarity?: number;
  quintile?: number;
  summary?: string;
  planning_area?: string;
}

export interface EligibilityType {
  criteria: string;
  requiredDocuments: string[];
}

export interface ApplicationType {
  process: string;
  deadline: string;
  formLink: string;
  termsAndConditions: string;
}

export interface ContactType {
  phone: string;
  email: string;
  address: string;
  website: string;
  socialMedia?: {
    facebook?: string;
    instagram?: string;
    linkedin?: string;
  };
  feedbackLink: string;
}

export interface AdditionalInfoType {
  faqs?: { question: string; answer: string }[];
  successStories?: { title: string; url: string }[];
  relatedSchemes?: {
    id: string;
    scheme: string;
    agency: string;
    link: string;
  }[];
  additionalResources?: { title: string; url: string }[];
  programmeDuration?: string;
  languageOptions?: string[];
}

export interface SearchResponse {
  sessionID?: string;
  data?: Array<RawSchemeData> | RawSchemeData;
  total_count?: number;
  next_cursor?: string;
  has_more?: boolean;
}

export type FilterObjType = {
  planningArea?: Set<string>;
  agency?: Set<string>;
};

export interface Scheme {
  schemeId: string;
  schemeType: string[];
  schemeName: string;
  agency: string;
  description: string;
  targetAudience: string[];
  scrapedText: string;
  benefits: string[];
  link: string;
  image: string;
  searchBooster: string;
  query: string;
  planningArea: string | string[];
  summary: string;
  contact: BranchContact[];
  howToApply: string;
  eligibility?: EligibilityType;
  eligibilityText: string;
  lastUpdated: string;
  application?: ApplicationType;
  additionalInfo?: AdditionalInfoType;
  serviceArea: string;
}

export type BranchContact = {
  planningArea?: string;
  phones?: string[];
  emails?: string[];
  address?: string;
};

export interface FirestoreTimestamp {
  _seconds: number;
  _nanoseconds: number;
}

export interface RawScheme {
  scheme?: string;
  agency?: string;
  description?: string;
  llm_description?: string;
  scraped_text?: string;
  link?: string;
  image?: string;
  search_booster?: string;
  summary?: string;
  service_area?: string;
  scheme_type?: string[];
  who_is_it_for?: string[];
  what_it_gives?: string[];
  planning_area?: string | string[];
  phone?: string | string[] | null;
  email?: string | string[] | null;
  address?: string | string[] | null;
  how_to_apply?: string | null;
  eligibility?: string | null;
  last_link_check?: string;
  last_scraped_update?: FirestoreTimestamp;
  last_llm_processed_update?: FirestoreTimestamp;
  link_check_status_code?: number;
  scheme_id?: string;
}
