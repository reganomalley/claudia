#!/usr/bin/env node

const v = "\x1b[31m";  // vermillion-ish (red)
const w = "\x1b[37m";  // white
const d = "\x1b[2m";   // dim
const b = "\x1b[1m";   // bold
const r = "\x1b[0m";   // reset

console.log(`
${v}     _____ ${r}
${v}    / ____|${r}
${v}   | |     ${w}${b}laudia${r}${d} v${require('../package.json').version}${r}
${v}   | |     ${r}
${v}   | |____ ${d}The senior dev you don't have.${r}
${v}    \\_____|${r}

${d}  She's ready. Open any project with Claude Code${r}
${d}  and she'll take it from here.${r}

${d}  Three ways she shows up:${r}
${w}  1.${r} ${d}Automatic checks on every file write${r}
${w}  2.${r} ${d}Jumps into conversation when you make tech decisions${r}
${w}  3.${r} ${d}Ask directly:${r} ${v}/claudia${r} ${d}+ your question${r}

${d}  Docs:${r}      ${w}https://getclaudia.dev${r}
${d}  Source:${r}    ${w}https://github.com/reganomalley/claudia${r}

${d}  Every Claude needs a Claudia.${r}
`);
