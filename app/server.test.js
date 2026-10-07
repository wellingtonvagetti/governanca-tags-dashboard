'use strict';
const assert = require('node:assert/strict');
const { once } = require('node:events');
const { createServer } = require('./server');

(async () => {
  const server = createServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = 'http://127.0.0.1:' + server.address().port;
  try {
    const response = await fetch(base + '/');
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /text\/html/);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    const html = await response.text();
    assert(html.length > 5_000_000);
    assert(html.includes('id="csvFull"') && html.includes('id="csvScope"'));
    assert(html.includes('id="saveDashboard"'));
    assert.equal((await fetch(base + '/index.html')).status, 200);
    assert.equal((await fetch(base + '/', { method: 'HEAD' })).status, 200);
    assert.deepEqual(await (await fetch(base + '/health')).json(), { status: 'ok' });
    assert.equal((await fetch(base + '/server.js')).status, 404);
    assert.equal((await fetch(base + '/', { method: 'POST' })).status, 405);
    console.log('OK: dashboard, importação, health, HEAD, rotas e métodos HTTP.');
  } finally { await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); process.exitCode = 1; });
