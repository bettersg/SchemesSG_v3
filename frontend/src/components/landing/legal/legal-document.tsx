import ReactMarkdown, {
  defaultUrlTransform,
  type Components,
} from "react-markdown";
import Link from "next/link";
import { Body, Headline, Title } from "@/components/ui/typography";
import { cn } from "@/lib/utils";
import { DocsSidebar } from "../developers/docs-sidebar";
import { ScrollToTop } from "../shared/scroll-to-top";

/**
 * Long-form legal document (privacy, terms) in the /developers reference shell:
 * a section sidebar beside bordered rows. The copy is markdown; each `##`
 * heading becomes one row and one sidebar entry.
 */

// The upper end of a readable line: no code panel shares this column.
const PROSE = "max-w-[75ch]";
const BODY = "text-[15px] leading-[1.65]";
const LINK =
  "font-medium text-(--schemes-blue-600) underline decoration-1 underline-offset-2 hover:decoration-2";

type Section = { id: string; heading: string; body: string };

// react-markdown's default sanitiser blanks tel: hrefs, which would drop the
// 995 and 1771 links in the terms.
const urlTransform = (url: string) =>
  url.startsWith("tel:") ? url : defaultUrlTransform(url);

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

/** Splits on `##` headings; anything before the first one is the preamble. */
export function splitSections(markdown: string): {
  preamble: string;
  sections: Section[];
} {
  const [preamble, ...parts] = markdown.split(/^## /m);
  return {
    preamble: preamble.trim(),
    sections: parts.map((part) => {
      const newline = part.indexOf("\n");
      const heading = (newline === -1 ? part : part.slice(0, newline)).trim();
      const body = newline === -1 ? "" : part.slice(newline + 1).trim();
      return { id: slugify(heading), heading, body };
    }),
  };
}

const components: Components = {
  h3: ({ children }) => (
    <Title
      as="h3"
      id={slugify(String(children))}
      className="mt-8 mb-2 scroll-mt-24 text-lg"
    >
      {children}
    </Title>
  ),
  p: ({ children }) => (
    <Body className={cn("mt-3 first:mt-0", BODY, PROSE)}>{children}</Body>
  ),
  ul: ({ children }) => (
    <ul
      className={cn(
        "mt-3 list-disc space-y-1.5 pl-5 text-(--schemes-ink-soft) marker:text-(--schemes-muted)",
        BODY,
        PROSE,
      )}
    >
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol
      className={cn(
        "mt-3 list-decimal space-y-1.5 pl-5 text-(--schemes-ink-soft) marker:text-(--schemes-muted)",
        BODY,
        PROSE,
      )}
    >
      {children}
    </ol>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-(--schemes-ink)">{children}</strong>
  ),
  a: ({ href = "", children }) => {
    if (href.startsWith("/") || href.startsWith("#")) {
      return (
        <Link href={href} className={LINK}>
          {children}
        </Link>
      );
    }
    const external = !href.startsWith("mailto:") && !href.startsWith("tel:");
    return (
      <a
        href={href}
        className={LINK}
        {...(external && { target: "_blank", rel: "noopener noreferrer" })}
      >
        {children}
      </a>
    );
  },
};

export default function LegalDocument({
  heading,
  effectiveDate,
  markdown,
}: {
  heading: string;
  effectiveDate?: string;
  markdown: string;
}) {
  const { preamble, sections } = splitSections(markdown);

  return (
    <div className="bg-(--schemes-bg)">
      <div className="mx-auto w-full max-w-7xl lg:grid lg:grid-cols-[16rem_minmax(0,1fr)] lg:px-6">
        <DocsSidebar
          heading="Contents"
          items={sections.map(({ id, heading }) => ({ id, label: heading }))}
        />

        <div className="min-w-0 px-4 sm:px-8 lg:pr-0 lg:pl-10">
          <div className="mx-auto w-full max-w-[75ch]">
            <header className="lg:pt-nav">
              <div className="pt-10 pb-8">
                <Headline as="h1" className="text-3xl sm:text-[2.25rem]">
                  {heading}
                </Headline>
                {effectiveDate && (
                  <Body className={cn("mt-3 text-(--schemes-muted)", BODY)}>
                    Effective date: {effectiveDate}
                  </Body>
                )}
                {preamble && (
                  <div className="mt-6">
                    <ReactMarkdown
                      components={components}
                      urlTransform={urlTransform}
                    >
                      {preamble}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </header>

            {sections.map((section) => (
              <section
                key={section.id}
                id={section.id}
                className="scroll-mt-24 border-t border-(--schemes-border) py-10"
              >
                <Headline as="h2" className="mb-3 text-xl sm:text-2xl">
                  {section.heading}
                </Headline>
                <ReactMarkdown
                  components={components}
                  urlTransform={urlTransform}
                >
                  {section.body}
                </ReactMarkdown>
              </section>
            ))}
          </div>
        </div>
      </div>
      <ScrollToTop />
    </div>
  );
}
