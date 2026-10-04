// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { mdFilename, renderMarkdown } from "./lib";

describe("mdFilename", () => {
  it("swaps the extension", () => {
    expect(mdFilename("report.final.docx")).toBe("report.final.md");
    expect(mdFilename("noext")).toBe("noext.md");
  });
});

describe("renderMarkdown", () => {
  it("renders headings", () => {
    expect(renderMarkdown("# Hi")).toContain("<h1");
  });
  it("strips scripts and event handlers", () => {
    const html = renderMarkdown('<script>alert(1)</script><img src=x onerror="alert(1)">');
    expect(html).not.toContain("<script");
    expect(html).not.toContain("onerror");
  });
});
