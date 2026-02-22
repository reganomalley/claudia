# Claudia - Proactive Mentor Plugin

## What This Is
Claude Code plugin: technology mentor, security advisor, prompt coach. 10 knowledge domains, 7 hooks, 5 commands. MIT licensed. npm: `claudia-mentor`. Web: getclaudia.dev.

## Architecture
- **Skills** (model-invocable): `claudia-mentor` (core brain/router), `claudia-databases`, `claudia-security`, `claudia-infrastructure`, `claudia-frontend`, `claudia-api`, `claudia-testing`, `claudia-performance`, `claudia-devops`, `claudia-data`
- **Hooks** (PreToolUse): `check-secrets.sh` (blocks), `check-practices.py`, `check-deps.py`, `check-dockerfile.py`, `check-git-hygiene.py` (blocks .env + conflicts), `check-accessibility.py`, `check-license.py`
- **Commands**: `ask` (ask anything), `explain` (explain code), `review` (catch bugs), `why` (explain stack), `health` (project audit)
- **Config**: `defaults.json` for personality/proactivity, user override via `~/.claude/claudia.json`
- **Context persistence**: `~/.claude/claudia-context.json` stores stack detection + tech decisions across sessions

## Key Files
- `skills/claudia-mentor/SKILL.md` -- personality, routing, greeting, learning mode, context persistence
- `hooks/hooks.json` -- hook registration (7 hooks)
- `commands/ask.md` -- main question entry point
- `commands/explain.md` -- code explanation for vibecoders
- `commands/review.md` -- "almost right" bug catcher
- `commands/why.md` -- stack decision explainer
- `commands/health.md` -- health audit command
- `config/defaults.json` -- default personality + proactivity level

## Plugin Registration
- Commands are namespaced: `/claudia:ask`, `/claudia:explain`, `/claudia:review`, `/claudia:why`, `/claudia:health`
- SKILL.md frontmatter must NOT have `name:` field (causes namespace-stripping bug)
- Load via: `claude --plugin-dir ~/personal/claudia` or `claude --plugin-dir $(npm root -g)/claudia-mentor`

## Conventions
- Hook scripts receive JSON on stdin (session_id, tool_name, tool_input)
- Exit 2 = block, exit 0 = allow. Use stderr for block messages, stdout JSON for advisory.
- Session-aware dedup via state files in `~/.claude/`
- Use `${CLAUDE_PLUGIN_ROOT}` for all internal paths
- Each domain: SKILL.md (~2000 words max) + references/ for deep content
- Voice: opinionated, direct, explains why, uses decision trees and tables
- Proactivity "high" = learning mode (teaches concepts, names patterns, quizzes gently)
