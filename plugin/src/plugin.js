/* Profil IA — Molettes dynamiques (Stream Deck+)
 * Protocole WebSocket Stream Deck brut + helper PowerShell pour Windows.
 */
'use strict';
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const LOG = path.join(ROOT, 'logs', 'profil-ia.log');

function log(...a) {
  try {
    fs.mkdirSync(path.dirname(LOG), { recursive: true });
    fs.appendFileSync(LOG, new Date().toISOString() + ' ' + a.join(' ') + '\n');
  } catch (e) { /* ignore */ }
}
try { if (fs.statSync(LOG).size > 512 * 1024) fs.unlinkSync(LOG); } catch (e) { /* ignore */ }

// ---------- arguments ----------
const argv = {};
for (let i = 2; i < process.argv.length; i += 2) argv[process.argv[i].replace(/^-+/, '')] = process.argv[i + 1];
const PORT = argv.port, UUID = argv.pluginUUID, REGISTER = argv.registerEvent;

// ---------- images (data URL) ----------
const imgCache = {};
function img(name) {
  if (!imgCache[name]) {
    const buf = fs.readFileSync(path.join(ROOT, 'imgs', 'layouts', name + '.png'));
    imgCache[name] = 'data:image/png;base64,' + buf.toString('base64');
  }
  return imgCache[name];
}

// ---------- helper (PowerShell) ----------
class Helper {
  constructor() { this.proc = null; this.ready = false; this.queue = []; this.listeners = []; this.buf = ''; this.lastFail = 0; this.pending = new Map(); this.seq = 0; }
  prompt(cfg, cb) {
    const id = String(++this.seq);
    this.pending.set(id, cb);
    setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); cb('timeout', ''); } }, 25000);
    this.send('prompt ' + id + ' ' + Buffer.from(JSON.stringify(cfg), 'utf8').toString('base64'));
  }
  start() {
    if (this.proc || Date.now() - this.lastFail < 3000) return;
    let cmd, args;
    if (process.env.PROFIL_IA_HELPER) {
      [cmd, ...args] = JSON.parse(process.env.PROFIL_IA_HELPER);
    } else {
      cmd = 'powershell.exe';
      args = ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', path.join(ROOT, 'bin', 'helper.ps1')];
    }
    log('helper start', cmd);
    try {
      this.proc = spawn(cmd, args, { windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (e) { log('helper spawn error', e.message); this.lastFail = Date.now(); this.proc = null; return; }
    this.ready = false;
    this.proc.stdout.setEncoding('utf8');
    this.proc.stdout.on('data', (d) => {
      this.buf += d;
      let i;
      while ((i = this.buf.indexOf('\n')) >= 0) {
        const line = this.buf.slice(0, i).trim();
        this.buf = this.buf.slice(i + 1);
        if (line) this.onLine(line);
      }
    });
    this.proc.stderr.on('data', (d) => log('helper stderr', String(d).trim()));
    this.proc.on('error', (e) => { log('helper error', e.message); });
    this.proc.on('exit', (code) => { log('helper exit', code); this.proc = null; this.ready = false; this.lastFail = Date.now(); });
  }
  onLine(line) {
    if (line === 'ready') {
      this.ready = true;
      const q = this.queue; this.queue = [];
      q.forEach((c) => this.write(c));
      return;
    }
    if (line.startsWith('err')) { log('helper', line); return; }
    const p = line.split(' ');
    if (p[0] === 'prompt') {
      const cb = this.pending.get(p[1]);
      if (cb) { this.pending.delete(p[1]); cb(p[2], p.slice(3).join(' ')); }
      return;
    }
    if (p[0] === 'vol') {
      const vol = parseInt(p[1], 10), muted = p[2] === '1';
      this.listeners.forEach((fn) => fn(vol, muted));
    }
  }
  write(cmd) { try { this.proc.stdin.write(cmd + '\n'); } catch (e) { log('helper write error', e.message); } }
  send(cmd) {
    this.start();
    if (!this.proc) return;
    if (!this.ready) {
      // keep only the latest "set" while waiting
      if (cmd.startsWith('set ')) this.queue = this.queue.filter((c) => !c.startsWith('set '));
      this.queue.push(cmd);
      return;
    }
    this.write(cmd);
  }
  onVolume(fn) { this.listeners.push(fn); }
  stop() { if (this.proc) { try { this.proc.stdin.write('quit\n'); } catch (e) { /* ignore */ } setTimeout(() => { try { this.proc && this.proc.kill(); } catch (e) { /* ignore */ } }, 300); } }
}
const helper = new Helper();

// ---------- Stream Deck socket ----------
let ws = null;
function sd(event, context, payload) {
  if (!ws || ws.readyState !== 1) return;
  const msg = { event, context };
  if (payload !== undefined) msg.payload = payload;
  ws.send(JSON.stringify(msg));
}
const feedback = (ctx, payload) => sd('setFeedback', ctx, payload);

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// ---------- actions ----------
class Base {
  constructor(ctx) { this.ctx = ctx; this.lastBg = null; this.timers = []; }
  bg(name) { if (this.lastBg !== name) { this.lastBg = name; return img(name); } return undefined; }
  push() {}
  rotate() {}
  dispose() { this.timers.forEach(clearInterval); }
  every(ms, fn) { const t = setInterval(fn, ms); this.timers.push(t); return t; }
  clear(t) { clearInterval(t); this.timers = this.timers.filter((x) => x !== t); }
}

class Defiler extends Base {
  constructor(ctx) { super(ctx); this.speed = 1; this.momentum = 0; this.dir = 'down'; this.decay = null; }
  appear() { this.render(true); }
  rotate(ticks) {
    helper.send('wheel ' + (-ticks * this.speed));
    this.dir = ticks > 0 ? 'down' : 'up';
    this.momentum = clamp(this.momentum + Math.abs(ticks) * 24, 0, 100);
    this.render();
    if (!this.decay) {
      this.decay = this.every(60, () => {
        this.momentum = clamp(this.momentum - 7, 0, 100);
        if (this.momentum === 0) { this.clear(this.decay); this.decay = null; }
        this.render();
      });
    }
  }
  push() { this.speed = this.speed === 1 ? 3 : 1; this.render(); }
  render(full) {
    const fast = this.speed === 3;
    let text;
    if (this.momentum > 0) text = (this.dir === 'down' ? '↓ Bas' : '↑ Haut') + (fast ? ' ×3' : '');
    else text = fast ? 'Rapide ×3' : 'Normal ×1';
    const p = { value: text, bar: { value: Math.round(this.momentum) } };
    const b = this.bg('bg-defiler'); if (b) p.bg = b;
    if (full) p.title = 'Défiler';
    feedback(this.ctx, p);
  }
}

class Zoom extends Base {
  constructor(ctx) { super(ctx); this.level = 100; }
  appear() { this.render(true); }
  rotate(ticks) {
    helper.send('zoom ' + ticks);
    this.level = clamp(this.level + ticks * 10, 30, 300);
    this.render();
  }
  push() { helper.send('zoomreset'); this.level = 100; this.render(); }
  render(full) {
    const p = { value: this.level + ' %', bar: { value: clamp(this.level, 50, 200) } };
    const b = this.bg('bg-zoom'); if (b) p.bg = b;
    if (full) p.title = 'Zoom';
    feedback(this.ctx, p);
  }
}

const volumeInstances = new Set();
const volState = { vol: null, muted: false, localAt: 0 };
let volPoll = null;
helper.onVolume((vol, muted) => {
  // ignore echoes while the dial is being turned
  if (Date.now() - volState.localAt < 450) return;
  if (vol === volState.vol && muted === volState.muted) return;
  volState.vol = vol; volState.muted = muted;
  volumeInstances.forEach((v) => v.render());
});

class Volume extends Base {
  appear() {
    volumeInstances.add(this);
    helper.send('get');
    if (!volPoll) volPoll = setInterval(() => { if (volumeInstances.size) helper.send('get'); }, 1500);
    this.render(true);
  }
  rotate(ticks) {
    if (volState.vol === null) { helper.send('get'); return; }
    volState.vol = clamp(volState.vol + ticks * 2, 0, 100);
    volState.localAt = Date.now();
    helper.send('set ' + volState.vol);
    if (ticks > 0 && volState.muted) { volState.muted = false; helper.send('unmute'); }
    volumeInstances.forEach((v) => v.render());
  }
  push() {
    volState.muted = !volState.muted;
    volState.localAt = Date.now();
    helper.send('mute');
    volumeInstances.forEach((v) => v.render());
  }
  render(full) {
    const { vol, muted } = volState;
    const p = {
      value: { value: vol === null ? '…' : (muted ? 'Muet' : vol + ' %'), color: muted ? '#9a9eaa' : '#a6ebc3' },
      bar: { value: vol === null ? 0 : vol, bar_fill_c: muted ? '#4a4d57' : '#43d17f' },
    };
    const b = this.bg(muted ? 'bg-volume-muet' : 'bg-volume'); if (b) p.bg = b;
    if (full) p.title = 'Volume';
    feedback(this.ctx, p);
  }
  dispose() { super.dispose(); volumeInstances.delete(this); if (!volumeInstances.size && volPoll) { clearInterval(volPoll); volPoll = null; } }
}

class Dictee extends Base {
  constructor(ctx) { super(ctx); this.active = false; this.since = 0; this.anim = null; }
  appear() { this.render(true); }
  push() {
    helper.send('dictee');
    this.active = !this.active;
    if (this.active) {
      this.since = Date.now();
      this.anim = this.every(90, () => {
        if (Date.now() - this.since > 5 * 60 * 1000) { this.stop(); return; }
        this.render();
      });
    } else this.stop(true);
    this.render();
  }
  stop(silent) {
    this.active = false;
    if (this.anim) { this.clear(this.anim); this.anim = null; }
    if (!silent) this.render();
  }
  render(full) {
    let p;
    if (this.active) {
      const t = (Date.now() - this.since) / 1000;
      const s = Math.floor(t), mm = Math.floor(s / 60), ss = String(s % 60).padStart(2, '0');
      const wave = Math.sin(t * 4.2);
      p = {
        value: { value: 'Écoute ' + mm + ':' + ss, color: '#ffc2ad' },
        bar: { value: Math.round(60 + 32 * wave), bar_fill_c: wave > 0 ? '#ff7a52' : '#d9603d' },
      };
      const b = this.bg('bg-dictee-actif'); if (b) p.bg = b;
    } else {
      p = { value: { value: 'Appuyer', color: '#f6b89c' }, bar: { value: 0, bar_fill_c: '#f0804e' } };
      const b = this.bg('bg-dictee'); if (b) p.bg = b;
    }
    if (full) p.title = 'Dictée';
    feedback(this.ctx, p);
  }
}

// ---------- touche « Prompt IA » ----------
const PRESETS = require('./presets.json');
function promptConfig(settings) {
  const s = settings || {};
  const pre = PRESETS[s.preset || 'explique'] || PRESETS.explique;
  return {
    prompt: (typeof s.prompt === 'string' && s.prompt.trim()) ? s.prompt.trim() : pre.prompt,
    source: s.source || 'selection',
    fallback: s.fallback || 'none',
    target: s.target || 'app',
    send: typeof s.send === 'boolean' ? s.send : pre.send,
    wait: Number.isFinite(+s.wait) && +s.wait > 0 ? Math.min(+s.wait, 8000) : 0,
    restore: s.restore !== false,
    longTarget: s.longTarget || 'chatgpt',
  };
}

const LONG_PRESS_MS = 450;

class Prompt {
  constructor(ctx, settings) { this.ctx = ctx; this.settings = settings || {}; this.busy = false; this.downAt = 0; }
  appear() {}
  rotate() {}
  dispose() {}
  down(settings) { if (settings) this.settings = settings; this.downAt = Date.now(); }
  up(settings) {
    if (settings) this.settings = settings;
    const held = this.downAt ? Date.now() - this.downAt : 0;
    this.downAt = 0;
    this.push(null, held >= LONG_PRESS_MS);
  }
  push(settings, long) {
    if (settings) this.settings = settings;
    if (this.busy) return;
    const cfg = promptConfig(this.settings);
    if (long) {
      if (cfg.longTarget === 'none') return;
      cfg.target = cfg.longTarget;
      cfg.wait = 0; // attente par défaut de la cible
    }
    delete cfg.longTarget;
    if (!cfg.wait) delete cfg.wait;
    this.busy = true;
    log('prompt', this.settings.preset || 'explique', cfg.source, cfg.target, 'send=' + cfg.send, long ? '(appui long)' : '');
    helper.prompt(cfg, (state, extra) => {
      this.busy = false;
      log('prompt result', state, extra);
      if (state === 'ok') sd('showOk', this.ctx);
      else sd('showAlert', this.ctx);
    });
  }
}

// doit correspondre aux UUID d'actions du manifest (build.js)
const PLUGIN_UUID = 'com.foufou-exe.profil-ia';
const KINDS = {
  [`${PLUGIN_UUID}.prompt`]: Prompt,
  [`${PLUGIN_UUID}.defiler`]: Defiler,
  [`${PLUGIN_UUID}.zoom`]: Zoom,
  [`${PLUGIN_UUID}.volume`]: Volume,
  [`${PLUGIN_UUID}.dictee`]: Dictee,
};
const instances = new Map();

function handle(msg) {
  const { event, action, context, payload } = msg;
  if (event === 'willAppear') {
    const K = KINDS[action];
    if (!K) return;
    const isKey = K === Prompt;
    if (payload && payload.controller && payload.controller !== (isKey ? 'Keypad' : 'Encoder')) return;
    const old = instances.get(context); if (old) old.dispose();
    const inst = new K(context, payload && payload.settings);
    instances.set(context, inst);
    inst.appear();
    return;
  }
  if (event === 'willDisappear') {
    const inst = instances.get(context);
    if (inst) { inst.dispose(); instances.delete(context); }
    return;
  }
  const inst = instances.get(context);
  if (!inst) return;
  if (event === 'dialRotate') inst.rotate(payload.ticks || 0, payload.pressed);
  else if (event === 'dialDown') inst.push();
  else if (event === 'touchTap') inst.push();
  else if (event === 'keyDown' && payload && payload.isInMultiAction) inst.push(payload.settings, false);
  else if (event === 'keyDown') inst.down(payload && payload.settings);
  else if (event === 'keyUp') inst.up(payload && payload.settings);
  else if (event === 'didReceiveSettings' && inst instanceof Prompt) inst.settings = (payload && payload.settings) || {};
}

function connect() {
  ws = new WebSocket('ws://127.0.0.1:' + PORT);
  ws.on('open', () => { log('connected'); ws.send(JSON.stringify({ event: REGISTER, uuid: UUID })); });
  ws.on('message', (data) => {
    let msg; try { msg = JSON.parse(String(data)); } catch (e) { return; }
    try { handle(msg); } catch (e) { log('handle error', e.stack || e.message); }
  });
  ws.on('close', () => { log('socket closed'); helper.stop(); setTimeout(() => process.exit(0), 400); });
  ws.on('error', (e) => log('socket error', e.message));
}

if (!PORT) { console.error('Lancé hors Stream Deck : arguments -port/-pluginUUID manquants.'); process.exit(1); }
log('start', process.version);
connect();
