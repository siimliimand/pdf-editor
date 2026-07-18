/**
 * pdfjs-dist compatibility shim for Cloudflare Workers.
 *
 * Two problems to solve:
 *
 * 1. pdfjs-dist's isNodeJS detection: When isNodeJS is true, pdfjs-dist
 *    disables Web Worker creation and runs on the main thread via a "fake
 *    worker".  We patch process.toString() so the check passes in Workers.
 *
 * 2. Fake worker module loading: Even in fake-worker mode, pdfjs-dist does
 *    `import(workerSrc)` to load WorkerMessageHandler.  That dynamic import
 *    fails in Workers ("No such module").  Instead, we provide the handler
 *    via `globalThis.pdfjsWorker`, which pdfjs-dist checks first.
 *
 * This file MUST be imported BEFORE any pdfjs-dist import.
 */

import { WorkerMessageHandler } from "pdfjs-dist/build/pdf.worker.mjs";

(globalThis as any).pdfjsWorker = { WorkerMessageHandler };
