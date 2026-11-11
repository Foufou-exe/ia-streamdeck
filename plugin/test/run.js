// Test de bout en bout : lance bin/plugin.js face à un faux Stream Deck (WebSocket) et un faux helper.
// Usage : npm run build && npm test
const assert = require('assert');
const path = require('path');
const { spawn } = require('child_process');
const { WebSocketServer } = require('ws');

const PORT = 28190;
const ROOT = path.join(__dirname, '..');
const A = (id) => `com.foufou-exe.profil-ia.${id}`;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const wss = new WebSocketServer({ port: PORT });
const received = [];
const prompts = [];

wss.on('connection', (sock) => {
  sock.on('message', async (raw) => {
    const msg = JSON.parse(raw);
    if (msg.event === 'registerPlugin') { run(sock).catch(fail); return; }
    received.push(msg);
  });
});

function fail(e) { console.error('ÉCHEC :', e.message); process.exit(1); }

async function run(sock) {
  const send = (o) => sock.send(JSON.stringify(o));
  const appear = (id, ctx, controller, settings = {}) => send({ event: 'willAppear', action: A(id), context: ctx, payload: { controller, settings } });

  appear('volume', 'vol', 'Encoder');
  appear('defiler', 'scroll', 'Encoder');
  appear('prompt', 'key', 'Keypad', { preset: 'resume' });
  await wait(400);

  send({ event: 'dialRotate', action: A('volume'), context: 'vol', payload: { ticks: 5 } });
  send({ event: 'dialRotate', action: A('defiler'), context: 'scroll', payload: { ticks: 2 } });
  send({ event: 'keyDown', action: A('prompt'), context: 'key', payload: { settings: { preset: 'resume' } } });
  await wait(100);
  send({ event: 'keyUp', action: A('prompt'), context: 'key', payload: { settings: { preset: 'resume' } } });
  await wait(300);
  send({ event: 'keyDown', action: A('prompt'), context: 'key', payload: { settings: { preset: 'resume' } } });
  await wait(600);
  send({ event: 'keyUp', action: A('prompt'), context: 'key', payload: { settings: { preset: 'resume' } } });
  await wait(500);

  const fb = (ctx) => received.filter((m) => m.context === ctx && m.event === 'setFeedback').map((m) => m.payload);
  assert.ok(fb('vol').some((p) => p.bar && p.bar.value === 50), 'le volume doit passer à 50 (40 + 5 crans × 2)');
  assert.ok(fb('scroll').some((p) => p.bar && p.bar.value > 0), 'la barre Défiler doit s\'élancer');
  assert.deepStrictEqual(prompts.map((p) => p.target), ['app', 'chatgpt'], 'appui court → Claude, appui long → ChatGPT');
  assert.strictEqual(prompts[0].send, true, 'Résumé envoie automatiquement');
  assert.strictEqual(received.filter((m) => m.event === 'showOk').length, 2, 'deux confirmations attendues');

  console.log('OK : molettes, appui court/long et confirmations');
  sock.close(); wss.close();
  setTimeout(() => process.exit(0), 300);
}

const child = spawn(process.execPath, [path.join(ROOT, 'com.foufou-exe.profil-ia.sdPlugin/bin/plugin.js'), '-port', String(PORT), '-pluginUUID', 'TEST', '-registerEvent', 'registerPlugin', '-info', '{}'], {
  env: { ...process.env, PROFIL_IA_HELPER: JSON.stringify([process.execPath, path.join(__dirname, 'fake-helper.js')]) },
  stdio: ['ignore', 'inherit', 'inherit'],
});
// le plugin journalise la sortie d'erreur du helper : on y lit les prompts envoyés
const fs = require('fs');
const LOG = path.join(ROOT, 'com.foufou-exe.profil-ia.sdPlugin/logs/profil-ia.log');
try { fs.unlinkSync(LOG); } catch (e) { /* absent */ }
setInterval(() => {
  try {
    const lines = fs.readFileSync(LOG, 'utf8').split('\n').filter((l) => l.includes('PROMPT '));
    prompts.length = 0;
    lines.forEach((l) => prompts.push(JSON.parse(l.slice(l.indexOf('PROMPT ') + 7))));
  } catch (e) { /* pas encore de journal */ }
}, 50);
setTimeout(() => fail(new Error('délai dépassé')), 10000);
process.on('exit', () => { try { child.kill(); } catch (e) { /* déjà arrêté */ } });
