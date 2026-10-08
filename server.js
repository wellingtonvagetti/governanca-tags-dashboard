'use strict';
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const zlib = require('node:zlib');
const { promisify } = require('node:util');
const gunzip = promisify(zlib.gunzip);
const gzip = promisify(zlib.gzip);

const MAX_BODY = 30 * 1024 * 1024;
let dashboardCache;

async function readDashboard() {
  if (dashboardCache) return dashboardCache;
  try { dashboardCache = await fs.readFile(path.join(__dirname, 'index.html')); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    const packed = await fs.readFile(path.join(__dirname, 'dashboard.html.gz.b64'), 'utf8');
    dashboardCache = await gunzip(Buffer.from(packed.replace(/\s+/g, ''), 'base64'));
  }
  return dashboardCache;
}

function dataDirectory(explicit) {
  if (explicit) return explicit;
  if (process.env.DASHBOARD_DATA_DIR) return process.env.DASHBOARD_DATA_DIR;
  return process.env.WEBSITE_SITE_NAME ? '/home/data/governanca-tags-dashboard' : path.join(__dirname, '.data');
}

function embeddedSnapshot(html) {
  const match = html.toString().match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/);
  if (!match) throw new Error('Dados incorporados não encontrados');
  return JSON.parse(match[1]);
}

function safeJson(value) { return JSON.stringify(value).replace(/</g, '\\u003c'); }
function injectSnapshot(html, snapshot) {
  return Buffer.from(html.toString().replace(
    /(<script id="data" type="application\/json">)[\s\S]*?(<\/script>)/,
    `$1${safeJson(snapshot)}$2`
  ));
}

function summarize(snapshot) {
  const r = snapshot.R || {}, dict = snapshot.dict || {};
  const indexes = Array.from({ length: (r.s || []).length }, (_, i) => i);
  const scopes = {
    governance: indexes.filter(i => r.sc[i] === 1), complete: indexes,
    outside: indexes.filter(i => r.sc[i] !== 1)
  };
  const value = (tag, i) => {
    const x = r[tag]?.[i];
    return x == null || x < 0 ? null : dict[tag]?.[x] ?? null;
  };
  const one = ids => {
    const total = ids.length;
    const tag = name => {
      const filled = ids.filter(i => value(name, i) !== null).length;
      const classified = ['CLIENTE', 'PRODUTO'].includes(name)
        ? ids.filter(i => value(name, i) !== null && value(name, i) !== 'INDEFINIDO').length : filled;
      return { filled, classified, total };
    };
    return {
      resources: total, subscriptions: new Set(ids.map(i => r.s[i])).size,
      resourceGroups: new Set(ids.map(i => r.g[i])).size,
      tags: { CLIENTE: tag('CLIENTE'), PRODUTO: tag('PRODUTO') }
    };
  };
  return Object.fromEntries(Object.entries(scopes).map(([name, ids]) => [name, one(ids)]));
}

function userName(req) {
  const direct = req.headers['x-ms-client-principal-name'];
  if (direct) return String(direct).slice(0, 200);
  try {
    const raw = req.headers['x-ms-client-principal'];
    if (!raw) return 'usuário autenticado';
    const principal = JSON.parse(Buffer.from(raw, 'base64').toString('utf8'));
    return String(principal.userDetails || principal.userId || 'usuário autenticado').slice(0, 200);
  } catch { return 'usuário autenticado'; }
}

async function readBody(req) {
  const chunks = []; let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) throw Object.assign(new Error('Arquivo excede o limite de 30 MB'), { status: 413 });
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw Object.assign(new Error('Conteúdo JSON inválido'), { status: 400 }); }
}

async function atomicWrite(file, content) {
  const temp = `${file}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(temp, content); await fs.rename(temp, file);
}

async function listStored(dir, baseline) {
  await fs.mkdir(dir, { recursive: true });
  const files = (await fs.readdir(dir)).filter(x => x.endsWith('.meta.json'));
  const stored = (await Promise.all(files.map(async file => {
    try { return JSON.parse(await fs.readFile(path.join(dir, file), 'utf8')); } catch { return null; }
  }))).filter(Boolean).sort((a, b) => String(b.savedAt).localeCompare(String(a.savedAt)));
  const base = {
    id: 'baseline', date: baseline.meta?.date || null, savedAt: null, savedBy: 'Deploy inicial',
    fullFile: baseline.meta?.fullFile || '', scopeFile: baseline.meta?.scopeFile || '',
    baseline: true, summary: summarize(baseline)
  };
  return [...stored, base];
}

async function latestSnapshot(dir, baseline) {
  try {
    const id = (await fs.readFile(path.join(dir, 'latest.txt'), 'utf8')).trim();
    if (!/^[a-zA-Z0-9._-]+$/.test(id)) throw new Error('Identificador inválido');
    return JSON.parse((await gunzip(await fs.readFile(path.join(dir, `${id}.json.gz`)))).toString('utf8'));
  } catch (error) {
    if (error.code !== 'ENOENT' && error.message !== 'Identificador inválido') console.error('Falha ao ler fotografia:', error.message);
    return baseline;
  }
}

async function saveSnapshot(dir, snapshot, req) {
  if (!snapshot?.meta || !snapshot?.R || !Array.isArray(snapshot.R.id) || !snapshot.meta.date)
    throw Object.assign(new Error('Fotografia inválida ou sem Data de Coleta'), { status: 400 });
  if (!/^\d{4}-\d{2}-\d{2}$/.test(snapshot.meta.date))
    throw Object.assign(new Error('Data de Coleta inválida'), { status: 400 });
  await fs.mkdir(dir, { recursive: true });
  const savedAt = new Date().toISOString();
  const id = `${snapshot.meta.date}--${savedAt.replace(/[:.]/g, '-')}`;
  const metadata = {
    id, date: snapshot.meta.date, savedAt, savedBy: userName(req),
    fullFile: snapshot.meta.fullFile || '', scopeFile: snapshot.meta.scopeFile || '',
    baseline: false, summary: summarize(snapshot)
  };
  await atomicWrite(path.join(dir, `${id}.json.gz`), await gzip(Buffer.from(JSON.stringify(snapshot)), { level: 9 }));
  await atomicWrite(path.join(dir, `${id}.meta.json`), JSON.stringify(metadata, null, 2));
  await atomicWrite(path.join(dir, 'latest.txt'), id);
  return metadata;
}

function json(res, status, payload, head = false) {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': body.length });
  res.end(head ? undefined : body);
}

function createServer(options = {}) {
  const dir = dataDirectory(options.dataDir);
  return http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff'); res.setHeader('Cache-Control', 'no-store');
    let pathname;
    try { pathname = new URL(req.url, 'http://localhost').pathname; }
    catch { res.writeHead(400); return res.end('Endereço inválido'); }
    try {
      const dashboard = await readDashboard(), baseline = embeddedSnapshot(dashboard);
      if (pathname === '/health' && ['GET', 'HEAD'].includes(req.method))
        return json(res, 200, { status: 'ok', persistence: dir }, req.method === 'HEAD');
      if (pathname === '/api/snapshots' && req.method === 'GET')
        return json(res, 200, { snapshots: await listStored(dir, baseline) });
      if (pathname === '/api/snapshots' && req.method === 'POST')
        return json(res, 201, { ok: true, snapshot: await saveSnapshot(dir, (await readBody(req)).snapshot, req) });
      if (!['GET', 'HEAD'].includes(req.method)) {
        res.writeHead(405, { Allow: 'GET, HEAD, POST' }); return res.end('Método não permitido');
      }
      if (!['/', '/index.html'].includes(pathname)) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        return res.end(req.method === 'HEAD' ? undefined : 'Não encontrado');
      }
      const content = injectSnapshot(dashboard, await latestSnapshot(dir, baseline));
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': content.length });
      res.end(req.method === 'HEAD' ? undefined : content);
    } catch (error) {
      console.error(error);
      if (pathname.startsWith('/api/')) return json(res, error.status || 500, { ok: false, error: error.message || 'Erro interno' });
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' }); res.end('Dashboard indisponível');
    }
  });
}

if (require.main === module) {
  const port = process.env.PORT || 8080;
  createServer().listen(port, '0.0.0.0', () => console.log('Dashboard iniciado com histórico persistente.'));
}
module.exports = { createServer, readDashboard, summarize, injectSnapshot };
