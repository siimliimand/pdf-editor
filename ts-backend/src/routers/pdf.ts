import { Hono } from 'hono';

export const pdfRouter = new Hono();

pdfRouter.post('/upload', async (c) => {
  return c.json({ message: 'PDF upload endpoint — not yet implemented' }, 501);
});
