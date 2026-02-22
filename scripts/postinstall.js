#!/usr/bin/env node

// Colors (matching Claude Code's block-character style)
const v = "\x1b[31m";     // vermillion
const p = "\x1b[38;5;203m"; // lighter vermillion/coral
const d2 = "\x1b[38;5;52m"; // dark red
const w = "\x1b[37m";     // white
const d = "\x1b[2m";      // dim
const b = "\x1b[1m";      // bold
const r = "\x1b[0m";      // reset
const hide = "\x1b[?25l"; // hide cursor
const show = "\x1b[?25h"; // show cursor

const version = require('../package.json').version;

// Claudia's icon - pixel art using block characters
// A small geometric "C" shape with a sparkle/star accent
const icon = [
  `      ${p}*${r}`,
  `      ${v}│${r}`,
  `  ${v}██████${r}`,
  `  ${v}██${r}${d2}██${r}${v}██${r}`,
  `  ${v}██${r}`,
  `  ${v}██${r}${d2}██${r}${v}██${r}`,
  `  ${v}██████${r}`,
];

const lines = [
  ...icon,
  ``,
  `  ${w}${b}Claudia${r} ${d}v${version}${r}`,
  `  ${d}The senior dev you don't have.${r}`,
  ``,
  `  ${d}Commands:${r}`,
  `  ${w}/claudia-mentor:claudia${r}          ${d}ask anything${r}`,
  `  ${w}/claudia-mentor:claudia-explain${r}  ${d}explain the code${r}`,
  `  ${w}/claudia-mentor:claudia-review${r}   ${d}catch bugs${r}`,
  `  ${w}/claudia-mentor:claudia-why${r}      ${d}why this stack${r}`,
  `  ${w}/claudia-mentor:claudia-health${r}   ${d}project audit${r}`,
  ``,
  `  ${d}7 hooks. 10 knowledge domains.${r}`,
  `  ${d}She remembers your stack across sessions.${r}`,
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

  // Draw icon with slightly slower timing
  for (let i = 0; i < icon.length; i++) {
    process.stdout.write(lines[i] + '\n');
    await sleep(50);
  }

  await sleep(150);

  // Rest cascades in faster
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
