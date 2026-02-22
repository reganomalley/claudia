# Claudia Session — Feb 22, 2026

## What got done

### 1. Proactive hooks (the big one)
Added 4 new hooks that make Claudia active beyond file edits. All advisory, never block, session-deduped, gated by proactivity level. Claudia now uses 5 hook event types (was 1), 11 hooks total (was 7).

| Hook | Event | What it does |
|------|-------|-------------|
| `claudia-teach.py` | Stop | Scans Claude's responses for 35+ tech keywords. Offers `/claudia:explain` for beginners. Also catches error patterns. |
| `claudia-compact-tip.py` | PreCompact | Teaches Esc+Esc shortcut on auto-compact. Encourages on manual. Beginner-only. |
| `claudia-session-tips.py` | SessionStart | Injects greeting box on every startup. Random beginner tip from pool of 10. Explains compaction. Light welcome on resume. |
| `claudia-prompt-coach.py` | UserPromptSubmit | Detects vague prompts ("fix it", "help", all-caps). Nudges Claude to ask clarifying questions. High proactivity only, max 3/session. |

All tested locally — keyword detection, dedup, proactivity gating, max-per-session limits, slash command skipping, frustration detection.

### 2. Greeting reliability
SessionStart hook now injects the full greeting box via `additionalContext` with an "IMPORTANT" instruction to display it exactly. Fires on every fresh startup for all users, regardless of proactivity. Previously the greeting only appeared when the model decided to invoke the skill.

### 3. Domain: askclaudia.dev
- Added `askclaudia.dev` as domain alias on Netlify via API
- Swept all `getclaudia.dev` references across 6 files (CLAUDE.md, postinstall.js, start.astro, astro.config, SITEMAP.md, BRAND.md)
- `getclaudia.dev` DNS is dead (no records on GoDaddy). Kept as alias on Netlify but does nothing.

### 4. Netlify build fix
- Root `netlify.toml` added with `base = "website"` so Netlify builds from the right subdirectory
- **Auto-deploy is still broken** — GitHub webhook is disconnected. All deploys this session were manual.
- Manual deploy command: `cd ~/personal/claudia/website && npm run build && netlify deploy --prod --dir=dist`

### 5. Website updates
- **Step 04 greeting**: Replaced ASCII box with pixel art mascot (colored half-blocks matching real terminal postinstall output)
- **Step 05 "Make it yours"**: Was dead-end font/terminal links with no instructions. Now says "ask Claudia" with `/claudia:ask` example
- Three manual deploys pushed to Netlify throughout session

### 6. /claudia:resume command
New command that reads session notes and summarizes where you left off. Auto-detects `claudia-session-*.md` files or accepts a path argument.

### 7. .zshrc fix
`source ~/tunnel/scripts/aliases.sh` was erroring because file doesn't exist. Changed to `[ -f ... ] && source ...` so it silently skips.

## Commits
1. `6e6d185` — Proactive hooks + Netlify build fix
2. `d7bac2f` — Rebrand to askclaudia.dev + greeting overhaul
3. `cf95df8` — Inject greeting via SessionStart hook for reliable display
4. (next) — Add /claudia:resume command

## Still TODO

### Must do next session
- [ ] **Reconnect Netlify to GitHub**: app.netlify.com/projects/getclaudia > Site configuration > Build & deploy > re-authorize GitHub. This restores auto-deploy on push.
- [ ] **Verify askclaudia.dev HTTPS**: SSL cert should be provisioned by now. Check `https://askclaudia.dev` loads.
- [ ] **Test Claudia greeting live**: Quit session, open new terminal, run `claude`. Greeting box should appear on first response.

### Should do
- [ ] Update website homepage to say "11 hooks" instead of "7"
- [ ] Update og:description meta tags across all pages
- [ ] The `/start` page may return homepage on Netlify due to SPA redirect priority — investigate
- [ ] Publish new npm version (currently 0.4.0, hooks changed significantly)

### Nice to have
- [ ] Tune prompt coach patterns with real usage data
- [ ] Add more keywords to teach hook as users encounter them
- [ ] Animate pixel art mascot in website terminal mockup on scroll

## How to resume
```
/claudia:resume
```
Or start Claude with the plugin and it'll greet you automatically.

## How to test hooks
```bash
echo '{"proactivity": "high"}' > ~/.claude/claudia.json
echo '{"experience": "beginner"}' > ~/.claude/claudia-context.json

echo '{"session_id":"t","last_assistant_message":"Deploy on Vercel"}' | python3 hooks/scripts/claudia-teach.py
echo '{"session_id":"t","trigger":"auto"}' | python3 hooks/scripts/claudia-compact-tip.py
echo '{"session_id":"t","source":"startup"}' | python3 hooks/scripts/claudia-session-tips.py
echo '{"session_id":"t","prompt":"fix it"}' | python3 hooks/scripts/claudia-prompt-coach.py
```

## How to deploy manually
```bash
cd ~/personal/claudia/website && npm run build && netlify deploy --prod --dir=dist
```
