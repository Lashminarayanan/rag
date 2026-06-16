import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import healthRouter from './routes/health.js';
import researchRouter from './routes/research.js';
import { errorHandler } from './middleware/errorHandler.js';

export function buildApp() {
  const app = express();
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(cors());
  app.use(express.json({ limit: '2mb' }));

  app.get('/', (_req, res) => {
    res.json({ ok: true, message: 'Offline Financial RAG enterprise backend running' });
  });

  app.use('/api/v1/health', healthRouter);
  app.use('/api/v1/research', researchRouter);

  app.use(errorHandler);
  return app;
}
