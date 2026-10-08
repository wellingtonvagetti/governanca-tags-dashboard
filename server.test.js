'use strict';
const assert = require('node:assert/strict');
const { once } = require('node:events');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { createServer } = require('./server');

(async () => {
  const dataDir = await fs.mkdtemp(path.join(os.tmpdir(), 'evertec-dashboard-'));
  const server = createServer({ dataDir });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const base = 'http://127.0.0.1:' + server.address().port;
  try {
    const response = await fetch(base + '/');
    assert.equal(response.status, 200); assert.match(response.headers.get('content-type'), /text\/html/);
    const html = await response.text(); assert(html.length > 5_000_000);
    assert(html.includes('id="csvFull"') && html.includes('id="csvScope"'));
    assert(html.indexOf('id="csvFull"') > html.indexOf('id="p-pbi"'));
    assert(html.includes('id="snapshotHistory"') && html.includes('id="snapshotEvolution"'));
    const initial = await (await fetch(base + '/api/snapshots')).json();
    assert.equal(initial.snapshots.length, 1); assert.equal(initial.snapshots[0].id, 'baseline');
    const embedded = JSON.parse(html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
    embedded.meta.date = '2026-10-08'; embedded.meta.fullFile = 'completo.csv'; embedded.meta.scopeFile = 'governanca.csv';
    const save = await fetch(base + '/api/snapshots', { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-ms-client-principal-name': 'teste@evertec' }, body: JSON.stringify({ snapshot: embedded }) });
    assert.equal(save.status, 201); const saved = await save.json(); assert(saved.ok); assert.equal(saved.snapshot.savedBy, 'teste@evertec');
    const history = await (await fetch(base + '/api/snapshots')).json(); assert.equal(history.snapshots.length, 2);
    const refreshed = await (await fetch(base + '/')).text();
    assert(refreshed.includes('"date":"2026-10-08"')); assert(refreshed.includes('"fullFile":"completo.csv"'));
    assert.deepEqual(await (await fetch(base + '/health')).json(), { status: 'ok', persistence: dataDir });
    assert.equal((await fetch(base + '/server.js')).status, 404);
    assert.equal((await fetch(base + '/', { method: 'POST' })).status, 405);
    console.log('OK: dashboard, persistência, histórico, injeção da última coleta e rotas HTTP.');
  } finally {
    await new Promise(resolve => server.close(resolve));
    await fs.rm(dataDir, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
