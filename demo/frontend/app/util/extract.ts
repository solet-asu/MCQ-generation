// app/lib/extract.ts
// Client-only text extraction for PDF / DOCX / TXT.
// Loads pdf.js directly from /public at runtime (no bundling), with a module worker.
// This avoids the "Object.defineProperty called on non-object" bundler issue.

let pdfjsModulePromise: Promise<any> | null = null;

function basePath() {
  // If you'll host under a subpath, set NEXT_PUBLIC_BASE_PATH="/home"
  const b = (process.env.NEXT_PUBLIC_BASE_PATH || "").replace(/\/$/, "");
  return b;
}
function pdfModuleUrl() {
  return `${basePath()}/pdf/pdf.mjs`;
}
function pdfWorkerUrl() {
  return `${basePath()}/pdf/pdf.worker.min.mjs`;
}

async function loadPdfjsFromPublic() {
  if (typeof window === "undefined")
    throw new Error("pdfjs can only run in the browser");
  if (!pdfjsModulePromise) {
    // Load the ESM file as-is from /public; tell the bundler to ignore it.
    // @ts-expect-error webpackIgnore is fine; Next will pass it through.
    pdfjsModulePromise = import(/* webpackIgnore: true */ pdfModuleUrl());
  }
  const mod = await pdfjsModulePromise;

  // Set up a module worker once
  try {
    if (mod?.GlobalWorkerOptions && !mod.GlobalWorkerOptions.workerPort) {
      mod.GlobalWorkerOptions.workerPort = new Worker(pdfWorkerUrl(), {
        type: "module",
      });
    }
  } catch (e) {
    // If worker creation fails, we'll fall back to disableWorker later.
    console.warn(
      "[pdfjs] module worker init failed; will try without worker:",
      e
    );
  }
  return mod;
}

export async function extractTextClient(file: File): Promise<string> {
  const name = file.name || "upload";
  const ext = (name.split(".").pop() || "").toLowerCase();

  if (ext === "txt") {
    return await file.text();
  }

  const arrayBuffer = await file.arrayBuffer();

  if (ext === "pdf") {
    const pdfjs = await loadPdfjsFromPublic();

    const tryRead = async (opts: any) => {
      const task = pdfjs.getDocument(opts);
      const pdf = await task.promise;
      let out = "";
      for (let p = 1; p <= pdf.numPages; p++) {
        const page = await pdf.getPage(p);
        const content = await page.getTextContent({
          normalizeWhitespace: true,
          disableCombineTextItems: false,
        });
        const pageText = content.items
          .map((it: any) => (typeof it?.str === "string" ? it.str : ""))
          .filter(Boolean)
          .join(" ");
        out += (pageText + "\n").trim() + "\n";
      }
      return out.trim();
    };

    // First try with the worker (if it initialized)
    try {
      return await tryRead({ data: arrayBuffer });
    } catch (e) {
      console.warn(
        "[pdfjs] worker read failed; retrying with disableWorker:",
        e
      );
      // Fallback: no worker
      return await tryRead({ data: arrayBuffer, disableWorker: true });
    }
  }

  if (ext === "docx") {
    // Browser build of mammoth (pure client-side)
    // @ts-expect-error using browser bundle path
    const mammoth = await import("mammoth/mammoth.browser");
    const result = await mammoth.extractRawText({ arrayBuffer });
    return (result?.value as string) || "";
  }

  throw new Error(
    `Unsupported file type: .${ext}. Supported: .pdf, .docx, .txt`
  );
}
