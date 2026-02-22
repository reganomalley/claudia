#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

// Colors
const v = "\x1b[31m";       // vermillion
const p = "\x1b[38;5;203m"; // lighter vermillion/coral
const d2 = "\x1b[38;5;52m"; // dark red
const w = "\x1b[37m";       // white
const d = "\x1b[2m";        // dim
const b = "\x1b[1m";        // bold
const g = "\x1b[32m";       // green
const r = "\x1b[0m";        // reset
const hide = "\x1b[?25l";   // hide cursor
const show = "\x1b[?25h";   // show cursor

const version = require('../package.json').version;
const pluginDir = path.resolve(__dirname, '..');

// ── Auto-setup: add alias to shell config ──────────────────────

function getShellConfig() {
  const shell = process.env.SHELL || '';
  if (shell.includes('zsh')) return path.join(os.homedir(), '.zshrc');
  if (shell.includes('bash')) {
    // macOS uses .bash_profile, Linux uses .bashrc
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
      // Already installed -- update the path in case it moved
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
      // First install -- append alias
      fs.appendFileSync(configFile, `\n${ALIAS_LINE}\n`);
      aliasStatus = 'added';
    }
  }
} catch (e) {
  aliasStatus = 'failed';
}

// ── iTerm2 inline image support ─────────────────────────────────

function isITerm2() {
  return !!(process.env.TERM_PROGRAM === 'iTerm.app' ||
            process.env.LC_TERMINAL === 'iTerm2' ||
            process.env.ITERM_SESSION_ID);
}

function renderInlineImage(imagePath, opts = {}) {
  try {
    const data = fs.readFileSync(imagePath);
    const base64 = data.toString('base64');
    const width = opts.width || '20';
    const height = opts.height || 'auto';
    // iTerm2 inline image protocol: OSC 1337 ; File=[args] : base64 ST
    return `\x1b]1337;File=inline=1;width=${width};height=${height};preserveAspectRatio=1:${base64}\x07`;
  } catch (e) {
    return null;
  }
}

// ── Build output ────────────────────────────────────────────────

const mascotPath = path.join(__dirname, '..', 'assets', 'claudia-terminal.jpg');
const canInline = isITerm2() && fs.existsSync(mascotPath);

const asciiIcon = [
  `      ${p}*${r}`,
  `      ${v}|${r}`,
  `  ${v}@@@@@@${r}`,
  `  ${v}@@${r}${d2}@@${r}${v}@@${r}`,
  `  ${v}@@${r}`,
  `  ${v}@@${r}${d2}@@${r}${v}@@${r}`,
  `  ${v}@@@@@@${r}`,
];

const setupMsg = aliasStatus === 'added'
  ? `  ${g}+${r} ${w}Auto-configured.${r} ${d}Restart your terminal, then just type${r} ${w}claude${r}`
  : aliasStatus === 'updated'
  ? `  ${g}+${r} ${d}Alias updated.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : aliasStatus === 'exists'
  ? `  ${g}+${r} ${d}Already configured.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : `  ${d}Run:${r} ${w}claude --plugin-dir "${pluginDir}"${r}`;

const textLines = [
  ``,
  `  ${w}${b}Claudia${r} ${d}v${version}${r}`,
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

  if (canInline) {
    // Render the mascot image inline (iTerm2)
    const img = renderInlineImage(mascotPath, { width: '18', height: 'auto' });
    if (img) {
      process.stdout.write(img + '\n');
      await sleep(200);
    }
  } else {
    // ASCII fallback
    for (let i = 0; i < asciiIcon.length; i++) {
      process.stdout.write(asciiIcon[i] + '\n');
      await sleep(50);
    }
    await sleep(150);
  }

  for (let i = 0; i < textLines.length; i++) {
    process.stdout.write(textLines[i] + '\n');
    await sleep(30);
  }

  process.stdout.write(show);
}

animate().catch(() => {
  process.stdout.write(show);
  if (canInline) {
    const img = renderInlineImage(mascotPath, { width: '18', height: 'auto' });
    if (img) process.stdout.write(img + '\n');
  }
  console.log(textLines.join('\n'));
});

process.on('exit', () => process.stdout.write(show));
process.on('SIGINT', () => { process.stdout.write(show); process.exit(); });
