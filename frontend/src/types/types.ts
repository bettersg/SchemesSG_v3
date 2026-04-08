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

// export type ChatResponse = ChunkResponse | UpdateResponse | AssistantResponse | StateResponse | FollowupResponse

// export interface ChatResponse {
// 	type: 
// 	STATUS = "status"
//     CHUNK = "chunk"
//     SCHEMES_UPDATE = "schemes_update"
//     ASSISTANT = "assistant"
//     STATE = "state"
//     FOLLOWUPS = "followups"
//     DONE = "done"
// }

export interface SearchResponse {
  sessionID?: string;
  data?: Array<RawSchemeData> | RawSchemeData;
  total_count?: number;
  next_cursor?: string;
  has_more?: boolean;
}

// export interface SearchResponse {
//   sessionID?: string;
//   data?: Array<RawSchemeData> | RawSchemeData;
//   mh?: number;
// }

export type FilterObjType = {
  planningArea?: Set<string>;
  agency?: Set<string>;
};

export type SearchResScheme = {
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
  similarity: number;
  quintile: number;
  planningArea: string | string[];
  summary: string;
};

export type BranchContact = {
  planningArea?: string;
  phones?: string[];
  emails?: string[];
  address?: string;
};

export type Scheme = SearchResScheme & {
  lastUpdated?: string;
  eligibility?: EligibilityType;
  application?: ApplicationType;
  contact?: BranchContact[];
  additionalInfo?: AdditionalInfoType;
  howToApply?: string;
  eligibilityText?: string;
  serviceArea?: string;
};

export interface ApiSchemeData {
  scheme_type?: string; scheme?: string; who_is_it_for?: string; agency?: string;
  description?: string; llm_description?: string; scraped_text?: string;
  what_it_gives?: string; link?: string; image?: string; search_booster?: string;
  scheme_id?: string; query?: string; similarity?: number; quintile?: number;
  phone?: string | string[]; email?: string | string[]; address?: string | string[];
  how_to_apply?: string; eligibility?: string; last_modified_date?: number;
  planning_area?: string; service_area?: string; summary?: string;
}