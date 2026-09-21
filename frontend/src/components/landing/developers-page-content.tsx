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
import StatusBanner from "@/components/feedback/status-banner";
import { Body, Headline, Title } from "@/components/ui/typography";
import { useLanguage } from "@/lib/landing-i18n";
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

const PROSE = "max-w-[62ch]";
const BODY = "text-[15px] leading-[1.65]";

export default function DevelopersPageContent() {
  const { t } = useLanguage();
  const d = t.developers;
  const s = d.sections;
  const l = d.labels;

  const navItems: NavItem[] = [
    { id: "access", label: s.access.heading },
    { id: "quick-start", label: s.quickStart.heading },
    { id: "authentication", label: s.auth.heading },
    { id: "base-url", label: s.baseUrl.heading },
    { id: "operations", label: s.operations.heading },
    ...OPERATIONS.map((operation) => ({
      id: operation.id,
      label: operation.name,
      method: operation.method,
      nested: true,
    })),
    { id: "fields", label: s.fields.heading },
    { id: "errors", label: s.errors.heading },
    { id: "rate-limits", label: s.rateLimits.heading },
    { id: "retired", label: s.retired.heading },
  ];

  const quickStart = `curl "${PARTNER_API_BASE}/${PARTNER_API_VERSION}/schemes?limit=1" \\
  -H "${API_KEY_HEADER}: $SCHEMES_API_KEY"`;

  return (
    <div className="bg-(--schemes-bg)">
      <div className="mx-auto w-full max-w-[100rem] lg:grid lg:grid-cols-[16rem_minmax(0,1fr)]">
        <DocsSidebar heading={d.contentsHeading} items={navItems} />

        <div className="min-w-0 px-4 sm:px-8 lg:px-10">
          {/* Header. No hero image and no orbs: the reader came for the endpoint.
              Only lg needs pt-nav: below it the sidebar strip sits above this and
              already carries the offset past the fixed navbar. */}
          <header className="lg:pt-nav">
            <div className="pt-10 pb-8">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                <Headline as="h1" className="text-3xl sm:text-[2.25rem]">
                  {d.heading}
                </Headline>
                <span className="rounded-full border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) px-2.5 py-1 text-[11px] font-semibold text-(--schemes-status-alert-text)">
                  {d.accessBadge}
                </span>
              </div>

              <Body className={cn("mt-3", BODY, PROSE)}>{d.subtitle}</Body>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/feedback"
                  className={cn(
                    productButtonSolidAmber,
                    productButtonDefault,
                    "w-fit",
                  )}
                >
                  {d.requestAccess}
                </Link>
                <code className="w-fit rounded-md border border-(--schemes-border) bg-(--schemes-surface) px-3 py-2 font-mono text-[12.5px] break-all text-(--schemes-ink-soft)">
                  {PARTNER_API_BASE}
                </code>
              </div>
            </div>
          </header>

          <Row id="access" heading={s.access.heading}>
            <Body className={cn(BODY, PROSE)}>{s.access.body}</Body>
            <StatusBanner variant="info" className="mt-4 max-w-[62ch]">
              {s.access.gate}
            </StatusBanner>
          </Row>

          <Row
            id="quick-start"
            heading={s.quickStart.heading}
            code={
              <CodeBlock
                language="cURL"
                caption={l.exampleRequest}
                code={quickStart}
                copyLabel={l.copy}
                copiedLabel={l.copied}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>{s.quickStart.body}</Body>
          </Row>

          <Row
            id="authentication"
            heading={s.auth.heading}
            code={
              <CodeBlock
                language="HTTP"
                caption={l.header}
                code={`${API_KEY_HEADER}: sk_schemes_xxxxxxxxxxxxxxxxxxxxxxxx`}
                copyLabel={l.copy}
                copiedLabel={l.copied}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>
              {s.auth.body} Send it as{" "}
              <InlineCode>{API_KEY_HEADER}</InlineCode>.
            </Body>
            <StatusBanner variant="alert" className="mt-4 max-w-[62ch]">
              {s.auth.warning}
            </StatusBanner>
          </Row>

          <Row
            id="base-url"
            heading={s.baseUrl.heading}
            code={
              <CodeBlock
                language="HTTP"
                caption="base"
                code={`${PARTNER_API_BASE}/${PARTNER_API_VERSION}`}
                copyLabel={l.copy}
                copiedLabel={l.copied}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>{s.baseUrl.body}</Body>
            <Body className={cn("mt-3 text-[14px] leading-[1.6]", PROSE)}>
              {s.baseUrl.versionNote}
            </Body>
          </Row>

          <Row id="operations" heading={s.operations.heading}>
            <Body className={cn(BODY, PROSE)}>{s.operations.body}</Body>
          </Row>

          {OPERATIONS.map((operation) => (
            <OperationRow key={operation.id} operation={operation} labels={l} />
          ))}

          <Row id="fields" heading={s.fields.heading} wide>
            <Body className={cn(BODY, PROSE)}>{s.fields.body}</Body>
            <div className="mt-5 max-w-3xl overflow-hidden rounded-md border border-(--schemes-border)">
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">{s.fields.heading}</caption>
                <thead className="bg-(--schemes-surface)">
                  <tr>
                    <Th>{l.field}</Th>
                    <Th>{l.type}</Th>
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
              {s.fields.omitted}
            </Body>
          </Row>

          <Row
            id="errors"
            heading={s.errors.heading}
            wide
            code={
              <CodeBlock
                language="JSON"
                caption={l.exampleResponse}
                code={ERROR_ENVELOPE}
                copyLabel={l.copy}
                copiedLabel={l.copied}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>{s.errors.body}</Body>
            <div className="mt-5 overflow-hidden rounded-md border border-(--schemes-border)">
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">{s.errors.heading}</caption>
                <thead className="bg-(--schemes-surface)">
                  <tr>
                    <Th>{l.status}</Th>
                    <Th>{l.code}</Th>
                    <Th>{l.meaning}</Th>
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
                        {d.errorMeanings[error.code]}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Row>

          <Row id="rate-limits" heading={s.rateLimits.heading}>
            <Body className={cn(BODY, PROSE)}>{s.rateLimits.body}</Body>
            <dl className="mt-5 divide-y divide-(--schemes-border-neutral)">
              {RATE_LIMIT_HEADERS.map((header) => (
                <div key={header} className="py-3 first:pt-0 last:pb-0">
                  <dt>
                    <code className="font-mono text-[12.5px] font-semibold text-(--schemes-blue-900)">
                      {header}
                    </code>
                  </dt>
                  <dd className="mt-1 text-[14px] leading-[1.6] text-(--schemes-ink-soft)">
                    {d.rateLimitHeaderNotes[header]}
                  </dd>
                </div>
              ))}
            </dl>
          </Row>

          <Row
            id="retired"
            heading={s.retired.heading}
            code={
              <CodeBlock
                language="JSON"
                caption="404"
                code={RETIRED_RESPONSE}
                copyLabel={l.copy}
                copiedLabel={l.copied}
              />
            }
          >
            <Body className={cn(BODY, PROSE)}>{s.retired.body}</Body>
          </Row>

          <div className="h-16" />
        </div>
      </div>
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

function OperationRow({
  operation,
  labels,
}: {
  operation: ApiOperation;
  labels: ReturnType<typeof useLanguage>["t"]["developers"]["labels"];
}) {
  const paramsHeading = {
    query: labels.queryParams,
    path: labels.pathParams,
    body: labels.bodyParams,
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
            requiredLabel={labels.required}
            optionalLabel={labels.optional}
            exampleLabel={labels.example}
          />
        </div>

        <div className="min-w-0 space-y-4">
          <CodeBlock
            language="cURL"
            caption={labels.exampleRequest}
            code={operation.request}
            copyLabel={labels.copy}
            copiedLabel={labels.copied}
          />
          <CodeBlock
            language="JSON"
            caption={labels.exampleResponse}
            code={operation.response}
            copyLabel={labels.copy}
            copiedLabel={labels.copied}
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
