// Construit le plugin Stream Deck « Profil IA ».
//
//   npm run build   → génère manifest, layouts, interface et bin/ dans com.foufou-exe.profil-ia.sdPlugin/
//   npm run pack    → build + archive installable dans ../dist/com.foufou-exe.profil-ia.streamDeckPlugin
//
// Les images (imgs/) sont générées à part par tools/render-plugin-assets.py.
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const esbuild = require('esbuild');
const pkg = require('./package.json');

const UUID = 'com.foufou-exe.profil-ia';
const P = path.join(__dirname, `${UUID}.sdPlugin`);
const DIST = path.join(__dirname, '..', 'dist');
const VERSION = `${pkg.version}.0`;

const write = (file, data) => {
  const full = path.join(P, file);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, typeof data === 'string' ? data : JSON.stringify(data, null, 2) + '\n');
};

// ---------- molettes ----------
const DIALS = [
  { id: 'defiler', name: 'Défiler', label: 'Défiler (barre XL)', tip: "Fait défiler la page, la barre montre l'élan", value: 'Normal ×1', valueColor: '#C9C1FF', fill: '#8B7CF6', range: [0, 100],
    trig: { Rotate: 'Défiler haut / bas', Push: 'Vitesse ×1 / ×3', Touch: 'Vitesse ×1 / ×3' } },
  { id: 'zoom', name: 'Zoom', label: 'Zoom (barre XL)', tip: 'Ctrl + molette, niveau affiché de 50 à 200 %', value: '100 %', valueColor: '#A9D4FB', fill: '#4EA8F5', range: [50, 200],
    trig: { Rotate: 'Zoom avant / arrière', Push: 'Retour à 100 % (Ctrl+0)', Touch: 'Retour à 100 % (Ctrl+0)' } },
  { id: 'volume', name: 'Volume', label: 'Volume (barre XL)', tip: 'Volume réel de Windows avec grande barre', value: '…', valueColor: '#A6EBC3', fill: '#43D17F', range: [0, 100],
    trig: { Rotate: 'Régler le volume', Push: 'Couper / rétablir', Touch: 'Couper / rétablir' } },
  { id: 'dictee', name: 'Dictée', label: 'Dictée (barre XL)', tip: 'Lance la saisie vocale Windows (Win+H)', value: 'Appuyer', valueColor: '#F6B89C', fill: '#F0804E', range: [0, 100],
    trig: { Rotate: '—', Push: 'Démarrer / arrêter la dictée', Touch: 'Démarrer / arrêter la dictée' } },
];

for (const d of DIALS) {
  write(`layouts/${d.id}.json`, {
    $schema: 'https://schemas.elgato.com/streamdeck/plugins/layout.json',
    id: `${UUID}.layout.${d.id}`,
    items: [
      { key: 'bg', type: 'pixmap', rect: [0, 0, 200, 100], value: `imgs/layouts/bg-${d.id}.png`, zOrder: 0 },
      { key: 'title', type: 'text', rect: [66, 9, 128, 24], value: d.name, font: { size: 19, weight: 700 }, color: '#F3F4F6', alignment: 'left', 'text-overflow': 'ellipsis', zOrder: 1 },
      { key: 'value', type: 'text', rect: [66, 34, 128, 20], value: d.value, font: { size: 15, weight: 600 }, color: d.valueColor, alignment: 'left', 'text-overflow': 'ellipsis', zOrder: 1 },
      { key: 'bar', type: 'bar', rect: [14, 64, 172, 18], value: d.range[0], subtype: 0, border_w: 0, bar_bg_c: '#2A2C35', bar_fill_c: d.fill, range: { min: d.range[0], max: d.range[1] }, zOrder: 1 },
    ],
  });
}

// ---------- manifest ----------
write('manifest.json', {
  $schema: 'https://schemas.elgato.com/streamdeck/plugins/manifest.json',
  UUID,
  Name: 'Profil IA',
  Version: VERSION,
  Author: 'Thibaut',
  Description: 'Touches « Prompt IA » configurables (Claude / ChatGPT) et molettes Stream Deck+ à grande barre dynamique.',
  URL: pkg.homepage,
  Icon: 'imgs/plugin/icon',
  Category: 'Profil IA',
  CategoryIcon: 'imgs/plugin/category',
  CodePath: 'bin/plugin.js',
  Nodejs: { Version: '20', Debug: 'disabled' },
  SDKVersion: 2,
  Software: { MinimumVersion: '6.5' },
  OS: [{ Platform: 'windows', MinimumVersion: '10' }],
  Actions: [{
    UUID: `${UUID}.prompt`,
    Name: 'Prompt IA',
    Tooltip: "Envoie la sélection à Claude ou ChatGPT avec un prompt prêt à l'emploi",
    Icon: 'imgs/actions/prompt',
    Controllers: ['Keypad'],
    PropertyInspectorPath: 'ui/prompt.html',
    States: [{ Image: 'imgs/actions/prompt-key', ShowTitle: false }],
    SupportedInMultiActions: true,
  }].concat(DIALS.map((d) => ({
    UUID: `${UUID}.${d.id}`,
    Name: d.label,
    Tooltip: d.tip,
    Icon: `imgs/actions/${d.id}`,
    Controllers: ['Encoder'],
    Encoder: { layout: `layouts/${d.id}.json`, Icon: `imgs/actions/${d.id}`, TriggerDescription: d.trig },
    States: [{ Image: `imgs/actions/${d.id}-key` }],
    SupportedInMultiActions: false,
    UserTitleEnabled: false,
  }))),
});

// ---------- inspecteur de propriétés ----------
const presets = JSON.parse(fs.readFileSync(path.join(__dirname, 'src/presets.json'), 'utf8'));
write('ui/prompt.html', fs.readFileSync(path.join(__dirname, 'src/prompt-pi.html'), 'utf8').replace('__PRESETS__', JSON.stringify(presets)));

// ---------- code ----------
esbuild.buildSync({
  entryPoints: [path.join(__dirname, 'src/plugin.js')],
  outfile: path.join(P, 'bin/plugin.js'),
  bundle: true, platform: 'node', target: 'node20', format: 'cjs',
  external: ['bufferutil', 'utf-8-validate'],
  charset: 'utf8', legalComments: 'none',
});
// helper.ps1 en UTF-8 avec BOM + CRLF pour Windows PowerShell 5.1
const ps = fs.readFileSync(path.join(__dirname, 'src/helper.ps1'), 'utf8').replace(/\r?\n/g, '\r\n');
write('bin/helper.ps1', '﻿' + ps);
console.log(`build ${UUID} ${VERSION}`);

// ---------- archive .streamDeckPlugin (zip, sans dépendance) ----------
if (process.argv.includes('--pack')) {
  const crcTable = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
  const crc32 = (buf) => { let c = -1; for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8); return (c ^ -1) >>> 0; };
  const files = [];
  const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).forEach((e) => {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== 'logs') walk(full); } else files.push(full);
  });
  walk(P);
  const DOS_DATE = ((2026 - 1980) << 9) | (1 << 5) | 1; // 1er janvier 2026, date fixe = archive reproductible
  const chunks = [], central = [];
  let offset = 0;
  for (const full of files) {
    const name = Buffer.from(path.relative(path.dirname(P), full).split(path.sep).join('/'), 'utf8');
    const data = fs.readFileSync(full);
    const comp = zlib.deflateRawSync(data, { level: 9 });
    const crc = crc32(data);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4); local.writeUInt16LE(0x0800, 6); local.writeUInt16LE(8, 8);
    local.writeUInt16LE(0, 10); local.writeUInt16LE(DOS_DATE, 12); local.writeUInt32LE(crc, 14); local.writeUInt32LE(comp.length, 18); local.writeUInt32LE(data.length, 22);
    local.writeUInt16LE(name.length, 26); local.writeUInt16LE(0, 28);
    const cen = Buffer.alloc(46);
    cen.writeUInt32LE(0x02014b50, 0); cen.writeUInt16LE(20, 4); cen.writeUInt16LE(20, 6); cen.writeUInt16LE(0x0800, 8); cen.writeUInt16LE(8, 10);
    cen.writeUInt16LE(0, 12); cen.writeUInt16LE(DOS_DATE, 14); cen.writeUInt32LE(crc, 16); cen.writeUInt32LE(comp.length, 20); cen.writeUInt32LE(data.length, 24);
    cen.writeUInt16LE(name.length, 28); cen.writeUInt32LE(offset, 42);
    chunks.push(local, name, comp);
    central.push(cen, name);
    offset += local.length + name.length + comp.length;
  }
  const cenBuf = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(files.length, 8); end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(cenBuf.length, 12); end.writeUInt32LE(offset, 16);
  fs.mkdirSync(DIST, { recursive: true });
  const out = path.join(DIST, `${UUID}.streamDeckPlugin`);
  fs.writeFileSync(out, Buffer.concat([...chunks, cenBuf, end]));
  console.log(`archive ${path.relative(path.join(__dirname, '..'), out)} (${files.length} fichiers)`);
}
