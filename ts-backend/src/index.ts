// Polyfill minimal browser globals for pdfjs-dist in Cloudflare Workers.
// pdfjs-dist v4 accesses window.location during static initialization of PDFWorker.
if (typeof globalThis.window === 'undefined') {
  (globalThis as any).window = {
    location: { href: 'http://localhost:8787/', origin: 'http://localhost:8787' },
    matchMedia: () => ({ matches: false }),
    addEventListener: () => {},
    removeEventListener: () => {},
  };
}

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { healthRouter } from './routers/health';
import { pdfRouter } from './routers/pdf';

type Bindings = {
  FONT_CACHE: R2Bucket;
  ENVIRONMENT: string;
};

const app = new Hono<{ Bindings: Bindings }>();

app.use('*', cors());

app.route('/', healthRouter);
app.route('/', pdfRouter);

export { app };

export default {
  fetch: app.fetch,
};
