import type { I18n, MessageDescriptor } from "@lingui/core";
import { msg, plural } from "@lingui/core/macro";
import type { StatusStep } from "@/types/chat";

type StepCopy = {
  label: (params: StepParams) => MessageDescriptor;
  message: (params: StepParams) => MessageDescriptor;
};
type StepParams = Record<string, string | number | undefined>;

const count = (params: StepParams) => Number(params.count ?? 0);
const text = (params: StepParams, key: string) => String(params[key] ?? "");

/**
 * Translatable wording for the agent's status steps, keyed by the `code` each
 * tool in backend/functions/agent/tools sends with its action_message. This is
 * the wording the chat shows; the tools' English label and message are only
 * the fallback for steps without a code. Add a code here when a tool gains one.
 */
const STEP_COPY: Record<string, StepCopy> = {
  "search.start": {
    label: () => msg({ message: "Searching schemes database", comment: "Chat status step: the assistant is searching the scheme list" }),
    message: (p) => {
      const query = text(p, "query");
      return msg({ message: `Finding the schemes that best match "${query}"`, comment: "Chat status step detail; query is the search the assistant ran" });
    },
  },
  "search.end": {
    label: (p) => msg({ message: plural(count(p), { one: "# scheme found", other: "# schemes found" }), comment: "Chat status step: the scheme search finished" }),
    message: (p) => {
      const query = text(p, "query");
      return msg({ message: plural(count(p), { one: `Found # scheme matching "${query}".`, other: `Found # schemes matching "${query}".` }), comment: "Chat status step detail; query is the search the assistant ran" });
    },
  },
  "filter.start": {
    label: () => msg({ message: "Filtering schemes", comment: "Chat status step: the assistant is narrowing the current results" }),
    message: (p) => {
      const directive = text(p, "directive");
      return msg({ message: `Filtering and re-ranking the schemes. Instructions: ${directive}`, comment: "Chat status step detail; directive is the assistant's own filtering instruction, in English" });
    },
  },
  "filter.end": {
    label: () => msg({ message: "Schemes filtered", comment: "Chat status step: narrowing the results finished" }),
    message: (p) => msg({ message: plural(count(p), { one: "Filtered and re-ranked the list to # scheme.", other: "Filtered and re-ranked the list to # schemes." }), comment: "Chat status step detail" }),
  },
  "websearch.start": {
    label: () => msg({ message: "Searching web", comment: "Chat status step: the assistant is searching the web" }),
    message: (p) => {
      const query = text(p, "query");
      return msg({ message: `Searching the web for "${query}"`, comment: "Chat status step detail; query is the web search the assistant ran" });
    },
  },
  "websearch.end": {
    label: () => msg({ message: "Web results found", comment: "Chat status step: the web search finished" }),
    message: (p) => {
      const query = text(p, "query");
      return msg({ message: plural(count(p), { one: `Found # result for "${query}".`, other: `Found # results for "${query}".` }), comment: "Chat status step detail; query is the web search the assistant ran" });
    },
  },
  "fetch.start": {
    label: () => msg({ message: "Reading a web page", comment: "Chat status step: the assistant is opening a web page" }),
    message: (p) => {
      const url = text(p, "url");
      return msg({ message: `Reading the page "${url}"`, comment: "Chat status step detail; url is the page address" });
    },
  },
  "fetch.end": {
    label: () => msg({ message: "Web page read", comment: "Chat status step: the web page was read" }),
    message: (p) => {
      const url = text(p, "url");
      return msg({ message: `Read "${url}".`, comment: "Chat status step detail; url is the page address" });
    },
  },
  "fetch.fail": {
    label: () => msg({ message: "Web page unavailable", comment: "Chat status step: the web page could not be read" }),
    message: (p) => {
      const url = text(p, "url");
      return msg({ message: `Couldn’t read "${url}".`, comment: "Chat status step detail; url is the page address" });
    },
  },
  "retrieve.start": {
    label: () => msg({ message: "Fetching scheme details", comment: "Chat status step: the assistant is loading full scheme details" }),
    message: () => msg({ message: "Searching our database for more information about selected schemes.", comment: "Chat status step detail" }),
  },
  "retrieve.end": {
    label: () => msg({ message: "Scheme details found", comment: "Chat status step: full scheme details loaded" }),
    message: (p) => msg({ message: plural(count(p), { one: "Retrieved detailed information for # scheme.", other: "Retrieved detailed information for # schemes." }), comment: "Chat status step detail" }),
  },
};

/**
 * The status step's label and detail in the current language. Steps from an
 * older backend, or with a code this list does not know, keep the English the
 * backend sent.
 */
export function statusStepCopy(i18n: I18n, step: StatusStep) {
  const copy = step.code ? STEP_COPY[step.code] : undefined;
  if (!copy) return { label: step.label, message: step.message };
  const params = step.params ?? {};
  return { label: i18n._(copy.label(params)), message: i18n._(copy.message(params)) };
}
