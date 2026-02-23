# Changelog

## 0.6.0 — 2026-02-23

### Added
- `/claudia:shortcuts` command — keyboard shortcut reference for Claude Code, terminal, and Claudia
- `/claudia:setup` command — first-time onboarding (7 steps)
- `/claudia:start` command — project creation from scratch
- Shared config module (`claudia_config.py`) for all hooks — project resolution, user config, project-scoped context
- Shortcuts keyword detection in teach hook
- Vermillion ANSI color across all hook `systemMessage` output

### Changed
- Command count: 8 → 11
- Updated CLAUDE.md and README with accurate counts
- Website copy updated to reflect all 11 commands

## 0.5.7 — 2026-02-23

### Added
- Per-turn Stop hook lock — only one Claudia note fires per Claude response
- Re-inject project context after compaction and resume so Claude stays grounded

## 0.5.0 — 2026-02-22

### Added
- 7 proactive hooks (Stop, PreCompact, SessionStart, UserPromptSubmit)
  - `claudia-teach.py` — keyword teaching + progressive command reveal
  - `claudia-compact-tip.py` — Esc+Esc tip before compaction
  - `claudia-session-tips.py` — rotating tips + beginner-simplified greeting
  - `claudia-prompt-coach.py` — stuck detection + vague prompt coaching
  - `claudia-run-suggest.py` — how to run created files
  - `claudia-next-steps.py` — contextual next actions
  - `claudia-milestones.py` — persistent cross-session milestone celebrations
- `/claudia:resume` command — session pickup + multi-project dashboard
- Beginner mode with progressive feature reveal
- Stuck detection (moderate+ for beginners, high for everyone)
- `systemMessage` on all proactive hooks so Claudia is visible in the status line
- Reliable greeting via SessionStart hook
- Per-project context persistence (`~/.claude/claudia-projects/`)
- Proactivity gating (low/moderate/high)

### Changed
- Rebranded domain from getclaudia.dev to askclaudia.dev
- Website redesigned with proactive coaching section, all 8 commands listed
- Mascot: transparent PNG, pixel art in terminal postinstall

## 0.4.0 — 2026-02-21

### Changed
- Plugin name shortened to `claudia` (from longer form)
- Command names cleaned up for consistency

## 0.3.0 — 2026-02-21

### Added
- One-command install via `npm i -g claudia-mentor`
- Auto-configures shell alias on postinstall

## 0.2.1 — 2026-02-21

### Added
- Pixel art postinstall icon with animated ANSI rendering

## 0.2.0 — 2026-02-21

### Added
- `/claudia:why` command — explain stack decisions
- `/claudia:health` command — project health audit
- `/claudia:wtf` command — error explainer (What/Why/Fix)
- `/claudia:where` command — project structure tour
- Learning mode (high proactivity)
- Context persistence across sessions
- Session greeting in core skill

### Changed
- Docs rewritten with dead-simple install guide

## 0.1.0 — 2026-02-21

### Added
- Initial release
- 7 PreToolUse hooks: check-secrets, check-practices, check-deps, check-dockerfile, check-git-hygiene, check-accessibility, check-license
- 10 knowledge domains: databases, security, infrastructure, frontend, API, testing, performance, devops, data, mentor
- `/claudia:ask` and `/claudia:explain` commands
- `/claudia:review` command — "almost right" bug catcher
- Astro + Tailwind website
- MIT license
