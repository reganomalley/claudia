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

${d}  Commands:${r}
${w}  /claudia-mentor:claudia${r}          ${d}ask anything${r}
${w}  /claudia-mentor:claudia-explain${r}  ${d}explain the code${r}
${w}  /claudia-mentor:claudia-review${r}   ${d}catch bugs${r}
${w}  /claudia-mentor:claudia-why${r}      ${d}why this stack${r}
${w}  /claudia-mentor:claudia-health${r}   ${d}project audit${r}

${d}  Plus 7 automatic hooks and 10 knowledge domains.${r}
${d}  She remembers your stack across sessions.${r}

${d}  Docs:${r}      ${w}https://getclaudia.dev${r}
${d}  Source:${r}    ${w}https://github.com/reganomalley/claudia${r}

${d}  Every Claude needs a Claudia.${r}
`);
