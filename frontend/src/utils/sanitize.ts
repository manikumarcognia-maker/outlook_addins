const HTML_TAG_RE = /<[^>]*>/g;

export function stripHtml(input: string): string {
  return input.replace(HTML_TAG_RE, " ");
}

export function sanitizeText(input: string): string {
  return stripHtml(input)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function truncateText(input: string, maxLength = 8000): string {
  if (input.length <= maxLength) return input;
  return `${input.slice(0, maxLength)}…`;
}

export function extractDomain(email: string): string {
  const at = email.lastIndexOf("@");
  return at >= 0 ? email.slice(at + 1).toLowerCase() : "";
}
