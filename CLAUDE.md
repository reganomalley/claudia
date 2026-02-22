# Claudia - Proactive Mentor Plugin

## What This Is
Claude Code plugin: technology mentor, security advisor, prompt coach. 10 knowledge domains, 7 hooks. MIT licensed.

## Architecture
- **Skills** (model-invocable): `claudia-mentor` (core brain/router), `claudia-databases`, `claudia-security`, `claudia-infrastructure`, `claudia-frontend`, `claudia-api`, `claudia-testing`, `claudia-performance`, `claudia-devops`, `claudia-data`
- **Hooks** (PreToolUse): `check-secrets.sh` (blocks), `check-practices.py`, `check-deps.py`, `check-dockerfile.py`, `check-git-hygiene.py` (blocks .env + conflicts), `check-accessibility.py`, `check-license.py`
- **Commands**: `/claudia` (direct questions), `/claudia-health` (project audit)
- **Config**: `defaults.json` for personality/proactivity, user override via `~/.claude/claudia.json`

## Key Files
- `skills/claudia-mentor/SKILL.md` -- personality, routing, stack detection, prompt coaching
- `hooks/hooks.json` -- hook registration (7 hooks)
- `commands/claudia.md` -- slash command entry point
- `commands/claudia-health.md` -- health audit command
- `scripts/create-domain.sh` -- domain scaffolding for contributors
- `config/defaults.json` -- default personality + proactivity level

## Conventions
- Hook scripts receive JSON on stdin (session_id, tool_name, tool_input)
- Exit 2 = block, exit 0 = allow. Use stderr for block messages, stdout JSON for advisory.
- Session-aware dedup via state files in `~/.claude/`
- Use `${CLAUDE_PLUGIN_ROOT}` for all internal paths
- Each domain: SKILL.md (~2000 words max) + references/ for deep content
- Voice: opinionated, direct, explains why, uses decision trees and tables
