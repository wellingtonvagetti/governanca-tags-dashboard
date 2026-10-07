'use strict';
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const zlib = require('node:zlib');
const { promisify } = require('node:util');
const gunzip = promisify(zlib.gunzip);

async function readDashboard() {
  try { return await fs.readFile(path.join(__dirname, 'index.html')); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    const packed = await fs.readFile(path.join(__dirname, 'dashboard.html.gz.b64'), 'utf8');
    return gunzip(Buffer.from(packed.replace(/\s+/g, ''), 'base64'));
  }
}

function createServer() {
  return http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    if (!['GET', 'HEAD'].includes(req.method)) {
      res.writeHead(405, { Allow: 'GET, HEAD' });
      return res.end('Método não permitido');
    }
    let pathname;
    try { pathname = new URL(req.url, 'http://localhost').pathname; }
    catch { res.writeHead(400); return res.end('Endereço inválido'); }
    if (pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(req.method === 'HEAD' ? undefined : '{"status":"ok"}');
    }
    if (!['/', '/index.html'].includes(pathname)) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end(req.method === 'HEAD' ? undefined : 'Não encontrado');
    }
    try {
      const content = await readDashboard();
      res.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Length': content.length
      });
      res.end(req.method === 'HEAD' ? undefined : content);
    } catch {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Dashboard indisponível');
    }
  });
}

if (require.main === module) {
  const port = process.env.PORT || 8080;
  createServer().listen(port, '0.0.0.0', () => console.log('Dashboard iniciado.'));
}
module.exports = { createServer, readDashboard };
