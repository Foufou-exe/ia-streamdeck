// Remplace bin/helper.ps1 pendant les tests (Linux/macOS/CI) : journalise les commandes et simule le volume.
const rl = require('readline').createInterface({ input: process.stdin });
let vol = 40, muted = 0;
const say = (s) => process.stdout.write(s + '\n');
say('ready');
rl.on('line', (line) => {
  const p = line.trim().split(' ');
  process.stderr.write('CMD ' + p[0] + '\n');
  switch (p[0]) {
    case 'get': say(`vol ${vol} ${muted}`); break;
    case 'set': vol = +p[1]; say(`vol ${vol} ${muted}`); break;
    case 'mute': muted = 1 - muted; say(`vol ${vol} ${muted}`); break;
    case 'unmute': muted = 0; say(`vol ${vol} ${muted}`); break;
    case 'prompt': {
      const cfg = JSON.parse(Buffer.from(p[2], 'base64').toString('utf8'));
      process.stderr.write('PROMPT ' + JSON.stringify(cfg) + '\n');
      setTimeout(() => say(`prompt ${p[1]} ok`), 50);
      break;
    }
    case 'quit': process.exit(0);
  }
});
