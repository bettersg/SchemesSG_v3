"use client";

/**
 * Partner API reference: a two-pane shell (dense section sidebar, content rows
 * pairing prose with a dark code panel), built from the existing landing
 * primitives and palette.
 *
 * One deviation from DESIGN.md, which keeps dark surfaces to the landing CTA
 * fold: the code panel is dark, because a reference page's defining element is
 * the sample. It stays in palette via `--schemes-blue-900`. See
 * docs/adr/0004-dark-code-panel-on-the-developers-reference.md.
 */

import Link from "next/link";
import { useEffect } from "react";
import StatusBanner from "@/components/feedback/status-banner";
import { Body, Headline, Title } from "@/components/ui/typography";
import { track } from "@/lib/analytics";
import {
  API_ERRORS,
  API_KEY_HEADER,
  ERROR_ENVELOPE,
  OPERATIONS,
  PARTNER_API_BASE,
  PARTNER_API_VERSION,
  RATE_LIMIT_HEADERS,
  RETIRED_RESPONSE,
  SCHEME_FIELDS,
  SYNC_REQUEST,
  type ApiOperation,
} from "@/lib/partner-api-reference";
import {
  productButtonDefault,
  productButtonSolidAmber,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";
import {
  InlineCode,
  MethodBadge,
  ParamList,
} from "./developers/api-primitives";
import { CodeBlock } from "./developers/code-block";
import { DocsSidebar, type NavItem } from "./developers/docs-sidebar";
import { ScrollToTop } from "./shared/scroll-to-top";

const PROSE = "max-w-[62ch]";
const BODY = "text-[15px] leading-[1.65]";

const ERROR_MEANINGS: Record<string, string> = {
  invalid_request: "The parameters are wrong. The message names which one.",
  missing_key: "No X-API-Key header was sent.",
  invalid_key: "The key is not one we issued.",
  revoked_key: "The key was valid and has been turned off. Talk to us.",
  not_found: "No such scheme, or it is no longer published.",
  scheme_retired: "The scheme was retired and merged. The body carries merged_into.",
  unsupported_version: "The version segment is missing or unknown.",
  method_not_allowed: "Right path, wrong HTTP method.",
  rate_limited: "Your per-minute budget is spent. Retry-After says when.",
  internal_error: "Something broke on our side. Safe to retry.",
};

const RATE_LIMIT_HEADER_NOTES: Record<string, string> = {
  "X-RateLimit-Limit": "Your budget, in requests per minute.",
  "X-RateLimit-Remaining": "What is left in the current minute.",
  "Retry-After": "Seconds to wait. Only sent with a 429.",
};

export default function DevelopersPageContent() {

  const navItems: NavItem[] = [
    { id: "access", label: `Getting access` },
    { id: "quick-start", label: `Quick start` },
    { id: "authentication", label: `Authentication` },
    { id: "base-url", label: `Base URL and versioning` },
    { id: "operations", label: `Operations` },
    ...OPERATIONS.map((operation) => ({
      id: operation.id,
      label: operation.name,
      method: operation.method,
      nested: true,
    })),
    { id: "fields", label: `Scheme fields` },
    { id: "errors", label: `Errors` },
    { id: "rate-limits", label: `Rate limits` },
    { id: "sync", label: `Keeping in sync` },
    { id: "retired", label: `When a scheme goes away` },
  ];

  const quickStart = `curl "${PARTNER_API_BASE}/${PARTNER_API_VERSION}/schemes?limit=1" \\
  -H "${API_KEY_HEADER}: $SCHEMES_API_KEY"`;

  // Reports each section the reader actually reaches, once per visit, so the
  // reference can be trimmed where nobody goes. Observed here rather than in
  // DocsSidebar, which is deliberately a server component and ships no JS.
  useEffect(() => {
    const reported = new Set<string>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = entry.target.id;
          if (!entry.isIntersecting || reported.has(id)) continue;
          reported.add(id);
          track("docs_section_view", { section_id: id });
        }
      },
      // Half the section visible, so a scroll straight past does not count it.
      { threshold: 0.5 },
    );

    for (const { id } of navItems) {
      const node = document.getElementById(id);
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
    // navItems is rebuilt per render from static copy; the ids never change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    // The docs stay English in every site language, for technical readers.
    <div lang="en" className="bg-(--schemes-bg)">
      <div className="mx-auto w-full max-w-7xl lg:grid lg:grid-cols-[16rem_minmax(0,1fr)] lg:px-6">
        <DocsSidebar heading={`Contents`} items={navItems} />

        <div className="min-w-0 px-4 sm:px-8 lg:pr-0 lg:pl-10">
          {/* Header. No hero image and no orbs: the reader came for the endpoint.
              Only lg needs pt-nav: below it the sidebar strip sits above this and
              already carries the offset past the fixed navbar. */}
          <header className="lg:pt-nav">
            <div className="pt-10 pb-8">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                <Headline as="h1" className="text-3xl sm:text-[2.25rem]">
                  {`Partner API`}
                </Headline>
                <span className="rounded-full border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) px-2.5 py-1 text-[11px] font-semibold text-(--schemes-status-alert-text)">
                  {"By request"}
                </span>
              </div>

              <Body className={cn("mt-3", BODY, PROSE)}>
                {`Read access to the Schemes.sg catalogue, so partner organisations can surface the right scheme inside their own product.`}
              </Body>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/feedback"
                  onClick={() =>
                    track("generate_lead", { method: "developers_page" })
                  }
                  className={cn(
                    productButtonSolidAmber,
                    productButtonDefault,
                    "w-fit",
                  )}
                >
                  {`Request access`}
                </Link>
                <code className="w-fit rounded-md border border-(--schemes-border) bg-(--schemes-surface) px-3 py-2 font-mono text-[12.5px] break-all text-(--schemes-ink-soft)">
                  {PARTNER_API_BASE}
                </code>
              </div>
            </div>
          </header>

          <Row id="access" heading={`Getting access`}>
            <Body className={cn(BODY, PROSE)}>
              {`This is not a self-serve API. We work with a small number of partner organisations, and each key is issued by hand so we know who is using the data and can reach them if something changes.`}
            </Body>
            <StatusBanner variant="info" className="mt-4 max-w-[62ch]">
              {`Before a key is issued, we confirm our terms of use and privacy policy cover sharing scheme data with your organisation. You will get a sandbox key first, pointed at our development data, so you can build and test before touching anything live.`}
            </StatusBanner>
          </Row>

          <Row
            id="quick-start"
            heading={`Quick start`}
            code={
              <CodeBlock
                operation="quick-start"
                language="cURL"
                caption={`Request`}
                code={quickStart}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              {`One request, to check your key works and see the shape of a scheme.`}
            </Body>
          </Row>

          <Row
            id="authentication"
            heading={`Authentication`}
            code={
              <CodeBlock
                operation="authentication"
                language="HTTP"
                caption={`Header`}
                code={`${API_KEY_HEADER}: sk_schemes_xxxxxxxxxxxxxxxxxxxxxxxx`}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              Every request carries your key in a header. There is no token
              exchange, no OAuth flow, and no expiry. Send it as{" "}
              <InlineCode>{API_KEY_HEADER}</InlineCode>.
            </Body>
            <StatusBanner variant="alert" className="mt-4 max-w-[62ch]">
              {`Keep the key on your server. It is not safe in a browser, a mobile app, or anything a user can read, because it grants your whole quota to whoever holds it.`}
            </StatusBanner>
          </Row>

          <Row
            id="base-url"
            heading={`Base URL and versioning`}
            code={
              <CodeBlock
                operation="base-url"
                language="HTTP"
                caption="base"
                code={`${PARTNER_API_BASE}/${PARTNER_API_VERSION}`}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              {`The version is a path segment, so a future version can ship alongside this one without changing any URL you have already built against.`}
            </Body>
            <Body className={cn("mt-3 text-[14px] leading-[1.6]", PROSE)}>
              {`There is one version today. A request with no version, or an unknown one, returns 404 rather than quietly falling back to v1.`}
            </Body>
          </Row>

          <Row id="operations" heading={`Operations`}>
            <Body className={cn(BODY, PROSE)}>
              {`Three read operations. One key covers all of them.`}
            </Body>
          </Row>

          {OPERATIONS.map((operation) => (
            <OperationRow key={operation.id} operation={operation} />
          ))}

          <Row id="fields" heading={`Scheme fields`} wide>
            <Body className={cn(BODY, PROSE)}>
              {`Every scheme we return carries exactly these fields, whether it came from list, retrieve, or search. A field with no value is null rather than absent, so the set of keys never changes. A few fields hold either a single string or an array of strings, depending on the scheme — check the type column and handle both.`}
            </Body>
            <div className="mt-5 max-w-3xl overflow-hidden rounded-md border border-(--schemes-border)">
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">{`Scheme fields`}</caption>
                <thead className="bg-(--schemes-surface)">
                  <tr>
                    <Th>{`Field`}</Th>
                    <Th>{`Type`}</Th>
                  </tr>
                </thead>
                <tbody>
                  {SCHEME_FIELDS.map((field) => (
                    <tr
                      key={field.name}
                      className="border-t border-(--schemes-border-neutral)"
                    >
                      <Td>
                        <code className="font-mono text-[12.5px] font-semibold text-(--schemes-blue-900)">
                          {field.name}
                        </code>
                      </Td>
                      <Td>
                        <code className="font-mono text-[12px] text-(--schemes-muted)">
                          {field.type}
                        </code>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Body className={cn("mt-4 text-[14px] leading-[1.6]", PROSE)}>
              {`We hold other fields internally, for review workflow and ranking. Those are deliberately not part of this contract, so our internal changes cannot break your integration.`}
            </Body>
          </Row>

          <Row
            id="errors"
            heading={`Errors`}
            wide
            code={
              <CodeBlock
                operation="errors"
                language="JSON"
                caption={`Response`}
                code={ERROR_ENVELOPE}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              {`Every failure returns the same envelope, so you can branch on error.code and never parse a message.`}
            </Body>
            <div className="mt-5 overflow-hidden rounded-md border border-(--schemes-border)">
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">{`Errors`}</caption>
                <thead className="bg-(--schemes-surface)">
                  <tr>
                    <Th>{`Status`}</Th>
                    <Th>{`Code`}</Th>
                    <Th>{`What it means`}</Th>
                  </tr>
                </thead>
                <tbody>
                  {API_ERRORS.map((error) => (
                    <tr
                      key={error.code}
                      className="border-t border-(--schemes-border-neutral)"
                    >
                      <Td>
                        <code className="font-mono text-[12.5px] font-semibold text-(--schemes-ink)">
                          {error.status}
                        </code>
                      </Td>
                      <Td>
                        <code className="font-mono text-[12.5px] text-(--schemes-blue-900)">
                          {error.code}
                        </code>
                      </Td>
                      <Td className="text-[14px] text-(--schemes-ink-soft)">
                        {ERROR_MEANINGS[error.code] &&
                          ERROR_MEANINGS[error.code]}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Row>

          <Row id="rate-limits" heading={`Rate limits`}>
            <Body className={cn(BODY, PROSE)}>
              {`Each partner gets a per-minute budget, shared across all three operations: spending it on list also spends it for search. Every response tells you where you stand, so you never have to discover the limit by hitting it.`}
            </Body>
            <dl className="mt-5 divide-y divide-(--schemes-border-neutral)">
              {RATE_LIMIT_HEADERS.map((header) => (
                <div key={header} className="py-3 first:pt-0 last:pb-0">
                  <dt>
                    <code className="font-mono text-[12.5px] font-semibold text-(--schemes-blue-900)">
                      {header}
                    </code>
                  </dt>
                  <dd className="mt-1 text-[14px] leading-[1.6] text-(--schemes-ink-soft)">
                    {RATE_LIMIT_HEADER_NOTES[header] &&
                      RATE_LIMIT_HEADER_NOTES[header]}
                  </dd>
                </div>
              ))}
            </dl>
          </Row>

          <Row
            id="sync"
            heading={`Keeping in sync`}
            code={
              <CodeBlock
                operation="sync"
                language="cURL"
                code={SYNC_REQUEST}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              Scheme ids are stable and the same in the development and
              production APIs, so use scheme_id as your key. Every scheme
              carries updated_at: the latest of its last scrape, its last status
              change and its last bulk re-tag. Do one full sync, then ask only
              for what changed with updated_since. Those results also include
              schemes that were retired or went inactive, with their status, so
              you know what to drop. A bulk re-tagging run moves updated_at too,
              so updated_since picks up the new tags.
            </Body>
          </Row>

          <Row
            id="retired"
            heading={`When a scheme goes away`}
            code={
              <CodeBlock
                operation="retired"
                language="JSON"
                caption="404"
                code={RETIRED_RESPONSE}
                copyLabel={"Copy"}
                copiedLabel={"Copied"}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              {`Schemes close, and some are folded into a replacement. If you store scheme ids, handle this case: a retired scheme that was merged returns 404 with the id that replaced it, so you can follow the change instead of silently dropping the record.`}
            </Body>
          </Row>

          <div className="h-16" />
        </div>
      </div>
      <ScrollToTop />
    </div>
  );
}

/**
 * One reference section: prose left, optional code right, hairline above.
 *
 * `wide` lets a section keep the full row for a table that would be unreadable
 * squeezed into the prose column.
 */
function Row({
  id,
  heading,
  children,
  code,
  wide = false,
}: {
  id: string;
  heading: string;
  children: React.ReactNode;
  code?: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <section
      id={id}
      className="scroll-mt-24 border-t border-(--schemes-border) py-10"
    >
      <div
        className={cn(
          "grid gap-x-10 gap-y-6",
          !wide && code && "xl:grid-cols-2",
          wide && code && "2xl:grid-cols-[minmax(0,1fr)_minmax(0,26rem)]",
        )}
      >
        <div className="min-w-0">
          <Headline as="h2" className="mb-3 text-xl sm:text-2xl">
            {heading}
          </Headline>
          {children}
        </div>
        {code ? <div className="min-w-0">{code}</div> : null}
      </div>
    </section>
  );
}

function OperationRow({ operation }: { operation: ApiOperation }) {
  const paramsHeading = {
    query: `Query parameters`,
    path: `Path parameters`,
    body: `Body parameters`,
  }[operation.paramsLabel];

  return (
    <section
      id={operation.id}
      className="scroll-mt-24 border-t border-(--schemes-border) py-10"
    >
      <div className="grid gap-x-10 gap-y-6 xl:grid-cols-2">
        <div className="min-w-0">
          <Title as="h2" className="text-xl">
            {operation.name}
          </Title>
          <p className="mt-2 flex flex-wrap items-center gap-2">
            <MethodBadge method={operation.method} />
            <code className="font-mono text-[13px] break-all text-(--schemes-ink)">
              {operation.path}
            </code>
          </p>
          <Body className={cn("mt-3", BODY, PROSE)}>{operation.summary}</Body>

          <h3 className="mt-6 mb-2 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase">
            {paramsHeading}
          </h3>
          <ParamList
            params={operation.params}
            requiredLabel={"required"}
            optionalLabel={"optional"}
            exampleLabel={`For example`}
          />
        </div>

        <div className="min-w-0 space-y-4">
          <CodeBlock
            operation={operation.id}
            language="cURL"
            caption={`Request`}
            code={operation.request}
            copyLabel={"Copy"}
            copiedLabel={"Copied"}
          />
          <CodeBlock
            operation={operation.id}
            language="JSON"
            caption={`Response`}
            code={operation.response}
            copyLabel={"Copy"}
            copiedLabel={"Copied"}
          />
        </div>
      </div>
    </section>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th
      scope="col"
      className="px-4 py-2.5 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase"
    >
      {children}
    </th>
  );
}

function Td({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={cn("px-4 py-2.5 align-top", className)}>{children}</td>;
}
