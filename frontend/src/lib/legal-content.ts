import { readFileSync } from "fs";
import { join } from "path";

interface LegalDocument {
  effectiveDate?: string;
  content: string;
}

export function getLegalDocument(
  document: "privacy" | "terms",
): LegalDocument {
  const filePath = join(
    process.cwd(),
    "src",
    "content",
    "legal",
    `${document}.md`,
  );
  const fileContent = readFileSync(filePath, "utf-8");

  const frontmatterMatch = fileContent.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  let effectiveDate: string | undefined;
  let content = fileContent;

  if (frontmatterMatch) {
    const frontmatter = frontmatterMatch[1];
    const effectiveDateMatch = frontmatter.match(
      /effectiveDate:\s*["'](.+?)["']/,
    );
    if (effectiveDateMatch) {
      effectiveDate = effectiveDateMatch[1];
    }
    content = fileContent.slice(frontmatterMatch[0].length);
  }

  return {
    effectiveDate,
    content: content.trim(),
  };
}
