export interface RawSchemeData {
  "Scheme Type"?: string;
  Scheme?: string;
  "Who's it for"?: string;
  Agency?: string;
  Description?: string;
  scraped_text?: string;
  "What it gives"?: string;
  Link?: string;
  Image?: string;
  "search_booster(WL)"?: string;
  scheme_id?: string;
  query?: string;
  Similarity?: number;
  Quintile?: number;

  // Lowercase properties from the backend
  scheme_type?: string;
  scheme?: string;
  who_is_it_for?: string;
  agency?: string;
  description?: string;
  what_it_gives?: string;
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
  has_more?: boolean;
  next_cursor?: string;
}

// export interface SearchResponse {
//   sessionID?: string;
//   data?: Array<RawSchemeData> | RawSchemeData;
//   mh?: number;
// }
