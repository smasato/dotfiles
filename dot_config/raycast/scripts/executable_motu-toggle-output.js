#!/usr/bin/env node
// Required parameters:
// @raycast.schemaVersion 1
// @raycast.title MOTU Toggle Output
// @raycast.mode compact
// @raycast.argument1 { "type": "dropdown", "placeholder": "Select Output", "data": [{"title": "Speaker", "value": "a"}, {"title": "Headphone", "value": "b"}] }
// Optional parameters:
// @raycast.icon 🔉
// Documentation:
// @raycast.description Toggle main output mute via WebSocket
// @raycast.author smasato
// @raycast.authorURL https://raycast.com/smasato

'use strict';

const arg = (process.argv[2] || '').toLowerCase();
if (arg !== 'a' && arg !== 'b') {
  console.error('usage: a|b');
  process.exit(1);
}

// a: Speaker
// b: Headphone
const payloads = arg === 'a'
  ? [
    new Uint8Array([19,153,0,0,0,1,0]),
    new Uint8Array([19,152,0,0,0,1,1])
  ]
  : [
    new Uint8Array([19,152,0,0,0,1,0]),
    new Uint8Array([19,153,0,0,0,1,1])
  ];

const ws = new WebSocket('ws://127.0.0.1:1281/UL5LFF1F3C');
ws.binaryType = 'arraybuffer';

ws.addEventListener('open', () => {
  payloads.forEach(payload => {
    ws.send(payload);
  });
  ws.close();
});
ws.addEventListener('error', e => { console.error(e.message); process.exit(2); });
