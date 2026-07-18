import { Hono } from 'hono';
import { convertPdfToHtml } from '../services/pdf-service';

export const pdfRouter = new Hono();

const PDF_MIME = 'application/pdf';
const MIN_ZOOM = 50;
const MAX_ZOOM = 500;
const DEFAULT_ZOOM = 100;

pdfRouter.post('/upload', async (c) => {
  const body = await c.req.parseBody();
  const file = body['file'];

  if (!file || !(file instanceof File)) {
    return c.json({ error: 'No file provided' }, 400);
  }

  if (file.type !== PDF_MIME) {
    return c.json({ error: 'File must be a PDF' }, 400);
  }

  let zoomLevel = DEFAULT_ZOOM;
  const zoomRaw = body['zoom'];
  if (zoomRaw != null) {
    const parsed = parseFloat(String(zoomRaw));
    if (!Number.isNaN(parsed)) {
      zoomLevel = parsed;
    }
  }
  if (zoomLevel < MIN_ZOOM || zoomLevel > MAX_ZOOM) {
    zoomLevel = DEFAULT_ZOOM;
  }

  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    const result = await convertPdfToHtml(bytes, { zoomLevel });
    return c.json({ html: result.html });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Conversion failed';
    return c.json({ error: message }, 500);
  }
});
