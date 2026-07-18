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
