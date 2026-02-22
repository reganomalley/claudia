#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

// ANSI helpers
const fg = (n) => `\x1b[38;5;${n}m`;
const bg = (n) => `\x1b[48;5;${n}m`;
const r = "\x1b[0m";       // reset
const w = "\x1b[37m";      // white
const d = "\x1b[2m";       // dim
const bold = "\x1b[1m";    // bold
const g = "\x1b[32m";      // green
const hide = "\x1b[?25l";  // hide cursor
const show = "\x1b[?25h";  // show cursor

// Palette — 256 color codes
const _ = -1;      // transparent (no draw)
const HR = 236;    // hair (dark gray, visible on black terminals)
const HH = 238;    // hair highlight
const RD = 196;    // red face
const RR = 160;    // darker red (shadow/contour)
const WH = 15;     // white (eyes)
const PU = 0;      // pupil (black)
const CH = 203;    // coral (hands/accent)
const MO = 52;     // mouth (dark red)
const SP = 203;    // sparkle color (coral)

// Half-block rendering: ▀ has fg=top, bg=bottom
function cell(top, bot) {
  if (top === _ && bot === _) return ' ';
  if (top === _ && bot !== _) return `${fg(bot)}▄${r}`;
  if (top !== _ && bot === _) return `${fg(top)}▀${r}`;
  if (top === bot) return `${fg(top)}█${r}`;
  return `${fg(top)}${bg(bot)}▀${r}`;
}

// Pixel grid — 10 wide x 12 tall (6 output lines)
const pixels = [
  //0   1   2   3   4   5   6   7   8   9
  [ _,  _,  _,  HR, HH, HR, HR, _,  _,  _],   // row 0: hair tips
  [ _,  _,  HR, HR, HR, HR, HR, HR, _,  _],   // row 1: hair
  [ _,  HR, HR, HR, HR, HR, HR, HR, HR, _],   // row 2: hair full
  [ _,  HR, HR, RD, RD, RD, RD, HR, HR, _],   // row 3: hair + forehead
  [ _,  HR, RD, WH, PU, RD, WH, PU, HR, _],   // row 4: eyes top
  [ _,  HR, RD, WH, PU, RD, WH, PU, HR, _],   // row 5: eyes bottom
  [ _,  _,  RD, RD, RD, RD, RD, RD, _,  _],   // row 6: cheeks
  [ _,  _,  RD, RD, MO, MO, RD, RD, _,  _],   // row 7: mouth
  [ _,  _,  _,  RR, RD, RD, RR, _,  _,  _],   // row 8: chin
  [ _,  _,  CH, _,  _,  _,  _,  CH, _,  _],   // row 9: hands
  [ _,  _,  _,  _,  _,  _,  _,  _,  _,  _],   // row 10
  [ _,  _,  _,  _,  _,  _,  _,  _,  _,  _],   // row 11
];

// Render pixel grid into half-block rows
const mascotLines = [];
for (let y = 0; y < pixels.length; y += 2) {
  let line = '';
  for (let x = 0; x < pixels[0].length; x++) {
    const top = pixels[y][x];
    const bot = (y + 1 < pixels.length) ? pixels[y + 1][x] : _;
    line += cell(top, bot);
  }
  mascotLines.push(line);
}

// Add sparkle above her head
const sparkle = `      ${fg(SP)}*${r}`;

const version = require('../package.json').version;
const pluginDir = path.resolve(__dirname, '..');

// ── Auto-setup: add alias to shell config ──────────────────────

function getShellConfig() {
  const shell = process.env.SHELL || '';
  if (shell.includes('zsh')) return path.join(os.homedir(), '.zshrc');
  if (shell.includes('bash')) {
    const profile = path.join(os.homedir(), '.bash_profile');
    if (fs.existsSync(profile)) return profile;
    return path.join(os.homedir(), '.bashrc');
  }
  return null;
}

const ALIAS_MARKER = '# claudia-mentor';
const ALIAS_LINE = `alias claude='claude --plugin-dir "${pluginDir}"' ${ALIAS_MARKER}`;

let aliasStatus = 'skipped';

try {
  const configFile = getShellConfig();
  if (configFile) {
    const contents = fs.existsSync(configFile) ? fs.readFileSync(configFile, 'utf8') : '';

    if (contents.includes(ALIAS_MARKER)) {
      const updated = contents.replace(
        /alias claude='claude --plugin-dir ".*?"' # claudia-mentor/,
        ALIAS_LINE
      );
      if (updated !== contents) {
        fs.writeFileSync(configFile, updated);
        aliasStatus = 'updated';
      } else {
        aliasStatus = 'exists';
      }
    } else {
      fs.appendFileSync(configFile, `\n${ALIAS_LINE}\n`);
      aliasStatus = 'added';
    }
  }
} catch (e) {
  aliasStatus = 'failed';
}

// ── Build output ────────────────────────────────────────────────

const setupMsg = aliasStatus === 'added'
  ? `  ${g}+${r} ${w}Auto-configured.${r} ${d}Restart your terminal, then just type${r} ${w}claude${r}`
  : aliasStatus === 'updated'
  ? `  ${g}+${r} ${d}Alias updated.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : aliasStatus === 'exists'
  ? `  ${g}+${r} ${d}Already configured.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : `  ${d}Run:${r} ${w}claude --plugin-dir "${pluginDir}"${r}`;

const textLines = [
  ``,
  `  ${w}${bold}Claudia${r} ${d}v${version}${r}`,
  `  ${d}She catches what you miss.${r}`,
  ``,
  setupMsg,
  ``,
  `  ${d}She checks your code automatically.${r}`,
  `  ${d}She joins conversations about tech decisions.${r}`,
  `  ${d}She teaches you as you build.${r}`,
  ``,
  `  ${d}Docs:${r}   ${w}https://getclaudia.dev${r}`,
  `  ${d}Source:${r} ${w}https://github.com/reganomalley/claudia${r}`,
  ``,
  `  ${d}Every Claude needs a Claudia.${r}`,
  ``,
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function animate() {
  process.stdout.write(hide + '\n');

  // Sparkle
  process.stdout.write(sparkle + '\n');
  await sleep(80);

  // Mascot
  for (let i = 0; i < mascotLines.length; i++) {
    process.stdout.write('    ' + mascotLines[i] + '\n');
    await sleep(60);
  }

  await sleep(120);

  // Text
  for (let i = 0; i < textLines.length; i++) {
    process.stdout.write(textLines[i] + '\n');
    await sleep(30);
  }

  process.stdout.write(show);
}

animate().catch(() => {
  process.stdout.write(show);
  process.stdout.write(sparkle + '\n');
  mascotLines.forEach(row => process.stdout.write('    ' + row + '\n'));
  console.log(textLines.join('\n'));
});

process.on('exit', () => process.stdout.write(show));
process.on('SIGINT', () => { process.stdout.write(show); process.exit(); });
