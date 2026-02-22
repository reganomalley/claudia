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

// ── Animation ──────────────────────────────────────────────────

const icon = [
  `      ${p}*${r}`,
  `      ${v}│${r}`,
  `  ${v}██████${r}`,
  `  ${v}██${r}${d2}██${r}${v}██${r}`,
  `  ${v}██${r}`,
  `  ${v}██${r}${d2}██${r}${v}██${r}`,
  `  ${v}██████${r}`,
];

const setupMsg = aliasStatus === 'added'
  ? `  ${g}✓${r} ${w}Auto-configured.${r} ${d}Restart your terminal, then just type${r} ${w}claude${r}`
  : aliasStatus === 'updated'
  ? `  ${g}✓${r} ${d}Alias updated.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : aliasStatus === 'exists'
  ? `  ${g}✓${r} ${d}Already configured.${r} ${w}claude${r} ${d}always loads Claudia.${r}`
  : `  ${d}Run:${r} ${w}claude --plugin-dir "${pluginDir}"${r}`;

const lines = [
  ...icon,
  ``,
  `  ${w}${b}Claudia${r} ${d}v${version}${r}`,
  `  ${d}The senior dev you don't have.${r}`,
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

  for (let i = 0; i < icon.length; i++) {
    process.stdout.write(lines[i] + '\n');
    await sleep(50);
  }

  await sleep(150);

  for (let i = icon.length; i < lines.length; i++) {
    process.stdout.write(lines[i] + '\n');
    await sleep(30);
  }

  process.stdout.write(show);
}

animate().catch(() => {
  process.stdout.write(show);
  console.log(lines.join('\n'));
});

process.on('exit', () => process.stdout.write(show));
process.on('SIGINT', () => { process.stdout.write(show); process.exit(); });
