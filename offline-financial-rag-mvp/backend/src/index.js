import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import { config } from './config.js';
import { initSse, sendEvent } from './sse.js';


const app = express();
app.use(cors());
app.use(express.json({ limit: '2mb' }));


app.get('/api/health', (_req, res) => {
  console.log('[INFO] Health check received');
  res.json({ ok: true, service: 'offline-financial-rag-backend' });
});


app.post('/api/query/stream', (req, res) => {
  const query = req.body?.query?.trim();


  console.log('[INFO] /api/query/stream called');
  console.log('[INFO] Query:', query);


  if (!query) {
    console.log('[WARN] Query is missing');
    return res.status(400).json({ error: 'query is required' });
  }


  initSse(res);
  sendEvent(res, 'status', { stage: 'accepted', message: 'Query accepted by backend' });


  console.log('[INFO] Python executable:', config.python);
  console.log('[INFO] Query worker:', config.queryWorker);


  const worker = spawn(config.python, [config.queryWorker, '--query', query], {
    env: { ...process.env },
    cwd: process.cwd(),
    stdio: ['ignore', 'pipe', 'pipe']
  });


  let stdoutBuffer = '';


  const flushLine = (line) => {
    if (!line.trim()) return;


    console.log('[PYTHON STDOUT]', line);


    try {
      const msg = JSON.parse(line);
      const type = msg.type || 'message';
      sendEvent(res, type, msg);
    } catch (err) {
      sendEvent(res, 'log', { type: 'log', message: line });
    }
  };


  worker.stdout.on('data', (chunk) => {
    stdoutBuffer += chunk.toString();
    const parts = stdoutBuffer.split('\n');
    stdoutBuffer = parts.pop() || '';
    for (const part of parts) flushLine(part);
  });


  worker.stderr.on('data', (chunk) => {
    const msg = chunk.toString();
    console.error('[PYTHON STDERR]', msg);
    sendEvent(res, 'stderr', { type: 'stderr', message: msg });
  });


  worker.on('error', (err) => {
    console.error('[ERROR] Failed to start Python worker:', err);
    sendEvent(res, 'stderr', {
      type: 'stderr',
      message: `Failed to start Python worker: ${err.message}`
    });
    res.end();
  });


  worker.on('close', (code) => {
    if (stdoutBuffer.trim()) flushLine(stdoutBuffer);


    console.log('[INFO] Python worker exited with code:', code);
    sendEvent(res, 'done', { type: 'done', exitCode: code });
    res.end();
  });


  res.on('close', () => {
    console.log('[INFO] Client connection closed');
    if (!worker.killed) worker.kill('SIGTERM');
  });
});


app.listen(config.port, () => {
  console.log(`Backend listening on http://localhost:${config.port}`);
});