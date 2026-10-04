import { useMemo, useRef, useState } from "react";
import { ConvertResult, convertFile, downloadText, mdFilename, renderMarkdown } from "./lib";

type Tab = "preview" | "raw";

export default function App() {
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [tab, setTab] = useState<Tab>("preview");
  const [copied, setCopied] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const abort = useRef<AbortController | null>(null);

  const html = useMemo(() => (result ? renderMarkdown(result.markdown) : ""), [result]);

  async function handle(file?: File) {
    if (!file) return;
    abort.current?.abort();
    abort.current = new AbortController();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await convertFile(file, abort.current.signal));
    } catch (e) {
      if ((e as Error).name !== "AbortError") setError((e as Error).message);
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  function clear() {
    abort.current?.abort();
    setResult(null);
    setError(null);
    setBusy(false);
  }

  async function copy() {
    if (!result) return;
    await navigator.clipboard.writeText(result.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <main>
      <header>
        <h1>MarkItDown</h1>
        <p>Convert documents to Markdown. Files are processed in memory and never stored.</p>
      </header>

      <div
        className={`drop ${dragging ? "over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files[0]); }}
        onClick={() => input.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
      >
        <input ref={input} type="file" hidden onChange={(e) => handle(e.target.files?.[0])} />
        {busy ? "Converting…" : "Drop a file here, or click to choose (PDF, Office, HTML, CSV, images, audio, …)"}
      </div>

      {error && <div className="error" role="alert">{error}</div>}

      {result && (
        <section>
          <div className="toolbar">
            <div className="tabs" role="tablist">
              <button role="tab" aria-selected={tab === "preview"} onClick={() => setTab("preview")}>Preview</button>
              <button role="tab" aria-selected={tab === "raw"} onClick={() => setTab("raw")}>Markdown</button>
            </div>
            <span className="meta">{result.filename} · {result.elapsed_ms} ms</span>
            <div className="actions">
              <button onClick={copy}>{copied ? "Copied" : "Copy"}</button>
              <button className="primary" onClick={() => downloadText(result.markdown, mdFilename(result.filename))}>
                Download .md
              </button>
              <button onClick={clear}>Clear</button>
            </div>
          </div>
          {result.markdown.trim() === "" ? (
            <p className="meta">The conversion produced no text.</p>
          ) : tab === "preview" ? (
            <article className="preview" dangerouslySetInnerHTML={{ __html: html }} />
          ) : (
            <pre className="raw">{result.markdown}</pre>
          )}
        </section>
      )}
    </main>
  );
}
