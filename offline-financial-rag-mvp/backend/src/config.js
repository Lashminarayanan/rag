import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';

dotenv.config({ path: path.resolve(process.cwd(), '../.env') });
if (!process.env.POSTGRES_HOST) {
  dotenv.config();
}

function resolvePythonPath() {
  const explicit = process.env.PYTHON_QUERY_WORKER;
  if (explicit && fs.existsSync(explicit)) return explicit;
  return process.platform === 'win32' ? 'python' : 'python3';
}

export const config = {
  port: Number(process.env.BACKEND_PORT || 8080),
  python: resolvePythonPath(),
  queryWorker: process.env.RAG_PYTHON_ENTRY || '../rag/app/query_worker.py'
};
