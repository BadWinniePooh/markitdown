import DOMPurify from "dompurify";
import { marked } from "marked";

export interface ConvertResult {
  markdown: string;
  title: string | null;
  filename: string;
  elapsed_ms: number;
}

/** Render untrusted markdown to sanitized HTML. */
export function renderMarkdown(md: string): string {
  return DOMPurify.sanitize(marked.parse(md, { async: false }) as string);
}

/** "report.final.docx" -> "report.final.md" */
export function mdFilename(original: string): string {
  const base = original.replace(/\.[^./\\]+$/, "");
  return `${base || "converted"}.md`;
}

export async function convertFile(file: File, signal?: AbortSignal): Promise<ConvertResult> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch("/api/convert", { method: "POST", body, signal });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export function downloadText(text: string, filename: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
