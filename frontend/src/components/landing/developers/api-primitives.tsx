import type { ApiParam, HttpMethod } from "@/lib/partner-api-reference";
import { cn } from "@/lib/utils";

/**
 * HTTP method label.
 *
 * Method is meaning, so it earns color under the Wayfinding Rule. GET borrows the
 * info tokens (a read), POST the alert tokens (a deliberate action). No new
 * tokens are introduced for this.
 */
export function MethodBadge({
  method,
  className,
}: {
  method: HttpMethod;
  className?: string;
}) {
  const isRead = method === "GET";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold",
        isRead
          ? "border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) text-(--schemes-status-info-text)"
          : "border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) text-(--schemes-status-alert-text)",
        className,
      )}
    >
      {method}
    </span>
  );
}

/** Inline identifier inside prose, as a bordered pill. */
export function InlineCode({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded border border-(--schemes-border) bg-(--schemes-surface) px-1 py-0.5 font-mono text-[12px] text-(--schemes-blue-900)">
      {children}
    </code>
  );
}

/** A method plus path, the way a partner reads it in their own client. */
export function EndpointLine({
  method,
  path,
  className,
}: {
  method: HttpMethod;
  path: string;
  className?: string;
}) {
  return (
    <p className={cn("flex flex-wrap items-center gap-2", className)}>
      <MethodBadge method={method} />
      <code className="font-mono text-[13px] break-all text-(--schemes-ink)">
        {path}
      </code>
    </p>
  );
}

/**
 * Parameter list, in the Stripe attribute-list arrangement: name, type and
 * requiredness on one line, description beneath, hairline between rows.
 *
 * A definition list rather than a table, because each description is a sentence
 * and a table cell would force it into an unreadable column.
 */
export function ParamList({
  params,
  requiredLabel,
  optionalLabel,
  exampleLabel,
}: {
  params: ApiParam[];
  requiredLabel: string;
  optionalLabel: string;
  exampleLabel: string;
}) {
  return (
    <dl className="divide-y divide-(--schemes-border-neutral)">
      {params.map((param) => (
        <div key={param.name} className="py-3 first:pt-0 last:pb-0">
          <dt className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <code className="font-mono text-[13px] font-semibold text-(--schemes-blue-900)">
              {param.name}
            </code>
            <span className="font-mono text-[11px] text-(--schemes-muted)">
              {param.type}
            </span>
            <span
              className={cn(
                "text-[11px] font-semibold",
                param.required
                  ? "text-(--schemes-status-alert-text)"
                  : "text-(--schemes-muted)",
              )}
            >
              {param.required ? requiredLabel : optionalLabel}
            </span>
          </dt>
          <dd className="mt-1 max-w-[62ch] text-[14px] leading-[1.6] text-(--schemes-ink-soft)">
            {param.description}
            {param.example ? (
              <>
                {" "}
                <span className="text-(--schemes-muted)">
                  {exampleLabel} <InlineCode>{param.example}</InlineCode>
                </span>
              </>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}
