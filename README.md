# Claudia: Proactive Mentor Plugin for Claude Code

[![Tests](https://github.com/reganomalley/claudia/actions/workflows/test.yml/badge.svg)](https://github.com/reganomalley/claudia/actions/workflows/test.yml)

A Claude Code plugin that acts as your technology mentor, security advisor, and prompt coach. Claudia fills the gaps between writing code and making good technology decisions.

**10 knowledge domains. 14 hooks. 11 commands. 205+ tests. Beginner-friendly.**

## What Claudia Does

- **Technology advising** -- Helps you choose databases, frameworks, APIs, infrastructure, and architecture patterns with clear trade-offs
- **Security guidance** -- Catches hardcoded secrets before they ship, advises on auth patterns and secrets management
- **Anti-pattern detection** -- Warns about common mistakes across code, Docker, dependencies, accessibility, and git hygiene
- **Prompt coaching** -- Detects vague prompts and suggests improvements to get better results from Claude
- **Context-aware** -- Reads your package.json, configs, and stack to give specific advice, not generic recommendations
- **Project health audits** -- `/claudia:health` scans your project for security, testing, dependency, and architecture issues
- **Beginner mode** -- Simplified greeting, stuck detection, run suggestions, milestone celebrations, progressive command reveal

## Install

```bash
npm install -g claudia-mentor
```

That's it. One command. The installer automatically configures your shell so every `claude` session loads Claudia. Restart your terminal and type `claude` -- she's there.

To verify, type `/claudia:ask are you there?` inside Claude Code.

## Usage

### Slash Commands

Type `/claudia:` and tab to see all options.

```
/claudia:ask what database should I use for time-series data?
/claudia:explain                  # Explain code, a technology, or a concept
/claudia:explain src/auth.ts      # Explain a specific file
/claudia:review                   # Review recent changes for bugs
/claudia:review feature-branch    # Review a specific branch
/claudia:why                      # Explain why your project uses this stack
/claudia:why prisma               # Explain a specific technology choice
/claudia:health                   # Run a full project health audit
/claudia:wtf                      # Break down an error: What / Why / Fix
/claudia:where                    # Guided tour of your project structure
/claudia:resume                   # Pick up where you left off
/claudia:shortcuts                # Keyboard shortcut reference
/claudia:setup                    # First-time onboarding
/claudia:start                    # Create a new project from scratch
```

### Automatic (Model-Invoked)

Claudia automatically activates when you:
- Make technology decisions ("should I use MongoDB or Postgres?")
- Discuss architecture ("how should I structure this microservice?")
- Choose between frameworks ("React or Svelte for this project?")
- Write suboptimal prompts ("make it better")
- Introduce security anti-patterns

### Hooks (Always Active)

**7 file-check hooks** (run on every file write):

| Hook | Type | What it catches |
|------|------|-----------------|
| Secret detection | blocks | AWS keys, API tokens, passwords, private keys, connection strings |
| Bad practices | warns | `eval()`, empty catch, `console.log` in prod, SQL concat, `chmod 777` |
| Dependency audit | warns | Deprecated, compromised, or trivial packages |
| Dockerfile lint | warns | Running as root, large images, secrets in ENV, missing multi-stage |
| Git hygiene | blocks | .env writes, merge conflict markers. Warns on large binaries |
| Accessibility | warns | Missing alt text, unlabeled inputs, icon-only buttons, div click handlers |
| License compliance | warns | GPL/AGPL dependencies in permissive-licensed projects |

**7 proactive hooks** (watch your conversation):

| Hook | Event | What it does |
|------|-------|--------------|
| Teach | Stop | Explains tech keywords, reveals commands contextually |
| Compact tip | PreCompact | Tips on context compaction |
| Session tips | SessionStart | Rotating tips, beginner-simplified greeting |
| Prompt coach | UserPromptSubmit | Stuck detection, vague prompt coaching |
| Run suggest | Stop | Tells beginners how to run created files |
| Next steps | Stop | Suggests 2-3 contextual next actions |
| Milestones | Stop | Celebrates achievements (persistent across sessions) |

## Beginner Mode

Set `"experience": "beginner"` in `~/.claude/claudia-context.json` (or run `/claudia:setup`) and Claudia adapts:

- **Simplified greeting** -- No command list on startup. Just "Claudia is here. Just build. I'm watching."
- **Stuck detection** -- Type "I'm stuck" or "help" and she asks one clarifying question, then suggests one small next step
- **Run suggestions** -- After a file is created, she tells you how to run it
- **Next-step suggestions** -- When Claude finishes a task, she suggests what to try next
- **Milestones** -- Celebrates first file, first bug fix, first commit. Persists across sessions
- **Progressive command reveal** -- Commands appear when relevant, not all at once

## Knowledge Domains

### Databases (`claudia-databases`)
- SQL vs NoSQL decision framework
- Vector databases for RAG/embeddings (pgvector, Pinecone, Qdrant)
- Time-series and graph database selection
- "Just use Postgres" rule (and when to break it)

### Security (`claudia-security`)
- Authentication patterns (session, JWT, OAuth, passkeys)
- Secrets management lifecycle
- TEEs and sandboxing
- Common security mistakes with fixes

### Infrastructure (`claudia-infrastructure`)
- AWS vs GCP vs Azure vs self-host
- Container orchestration (Docker, ECS, Cloud Run, k8s)
- Serverless decision framework
- Edge computing and cost estimation

### Frontend (`claudia-frontend`)
- Framework selection (React, Vue, Svelte, Solid, Angular)
- SSR vs SPA vs SSG vs islands architecture
- State management (when to use what)
- CSS approaches, bundlers, Core Web Vitals

### API Design (`claudia-api`)
- REST vs GraphQL vs gRPC vs tRPC
- API versioning, pagination, error handling
- Webhook design, rate limiting
- Real-time patterns (WebSockets, SSE, polling)

### Testing (`claudia-testing`)
- Test pyramid and what to test at each level
- Framework comparison (Jest, Vitest, Playwright)
- Mocking patterns (and when NOT to mock)
- Testing strategy by app type

### Performance (`claudia-performance`)
- "Measure before you optimize" framework
- Backend: N+1 queries, caching, connection pooling
- Frontend: Core Web Vitals, bundle optimization, image/font loading
- Profiling tools for Node.js and Python

### DevOps (`claudia-devops`)
- CI/CD pipeline design (GitHub Actions patterns)
- Deployment strategies (rolling, blue-green, canary)
- Monitoring hierarchy and the four golden signals
- Incident response and SLI/SLO framework

### Data Modeling (`claudia-data`)
- Schema design patterns (multi-tenancy, soft deletes, hierarchical data)
- Migration safety (zero-downtime patterns)
- Indexing strategy (B-tree, GIN, partial, composite)
- Normalization, denormalization, and anti-patterns

### Prompt Coaching (built into mentor)
- Detects vague or underspecified prompts
- Suggests improvements across 5 quality dimensions
- Offers rewritten versions

## Configuration

Override Claudia's personality and proactivity level:

### Global (`~/.claude/claudia.json`)

```json
{
  "proactivity": "high",
  "personality": {
    "tone": "casual"
  }
}
```

### Per-project (`.claudia.json` in project root)

```json
{
  "proactivity": "low",
  "hooks": {
    "check_practices": {
      "enabled": false
    }
  }
}
```

### Proactivity Levels

| Level | Behavior |
|-------|----------|
| `low` | Only responds when you use `/claudia` |
| `moderate` | Proactive on security issues and major anti-patterns (default) |
| `high` | Flags any suboptimal pattern or technology decision |

## Contributing

Claudia is designed for community contributions. The easiest ways to contribute:

### Add Reference Files
Drop a new `.md` file in any `references/` directory. Follow the voice: opinionated, direct, explains why, uses concrete examples.

### Add Anti-Patterns
Add entries to any hook script in `hooks/scripts/`.

### New Knowledge Domains

Use the scaffolding tool:

```bash
./scripts/create-domain.sh architecture
```

This creates the directory structure and template files. Fill in the SKILL.md, add reference files, and update the mentor's routing table.

### Security Rules for Hook Contributions

Hooks run locally with the same permissions as Claude Code. Malicious hooks could read files, exfiltrate data, or modify code silently.

- **All hook/script PRs require maintainer review** -- markdown-only reference PRs are lower risk
- **No network calls in hooks** -- no fetching URLs, no phoning home, local filesystem only
- **No obfuscated code** -- every line must be readable and understandable
- Hook PRs get a dedicated security review with line-by-line diff and sandboxed testing

### Writing Guidelines
- Be opinionated -- "it depends" without follow-up is not helpful
- Use decision trees and comparison tables
- Explain the "why" behind every recommendation
- Include "when NOT to use this" alongside recommendations
- Keep SKILL.md under ~2000 words, put depth in references

## License

MIT
