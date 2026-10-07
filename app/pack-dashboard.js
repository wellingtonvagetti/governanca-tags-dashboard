'use strict';
const fs = require('node:fs');
const zlib = require('node:zlib');
const path = require('node:path');
const input = process.argv[2] || path.join(__dirname, 'index.html');
const output = path.join(__dirname, 'dashboard.html.gz.b64');
const html = fs.readFileSync(input);
fs.writeFileSync(output, zlib.gzipSync(html, { level: 9 }).toString('base64') + '\n');
console.log(`Dashboard compactado: ${html.length} bytes → ${fs.statSync(output).size} bytes`);
