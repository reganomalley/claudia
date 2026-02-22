# Claudia: Proactive Mentor Plugin for Claude Code

A Claude Code plugin that acts as your technology mentor, security advisor, and prompt coach. Claudia fills the gaps between writing code and making good technology decisions.

**10 knowledge domains. 7 automated hooks. Context-aware advice.**

## What Claudia Does

- **Technology advising** -- Helps you choose databases, frameworks, APIs, infrastructure, and architecture patterns with clear trade-offs
- **Security guidance** -- Catches hardcoded secrets before they ship, advises on auth patterns and secrets management
- **Anti-pattern detection** -- Warns about common mistakes across code, Docker, dependencies, accessibility, and git hygiene
- **Prompt coaching** -- Detects vague prompts and suggests improvements to get better results from Claude
- **Context-aware** -- Reads your package.json, configs, and stack to give specific advice, not generic recommendations
- **Project health audits** -- `/claudia-health` scans your project for security, testing, dependency, and architecture issues

## Install

```bash
npm install -g claudia-mentor
```

That's it. One command. The installer automatically configures your shell so every `claude` session loads Claudia. Restart your terminal and type `claude` -- she's there.

To verify, type `/claudia:ask are you there?` inside Claude Code.

## Usage

### Slash Commands

Commands are namespaced under `claudia-mentor:`. Type `/claudia-mentor:` and tab to see all options.

```
/claudia:ask what database should I use for time-series data?
/claudia:explain                 # Explain the code that was just written
/claudia:explain src/auth.ts      # Explain a specific file
/claudia:review                   # Review recent changes for bugs
/claudia:review feature-branch    # Review a specific branch
/claudia:why                      # Explain why your project uses this stack
/claudia:why prisma               # Explain a specific technology choice
/claudia:health                   # Run a full project health audit
```

### Automatic (Model-Invoked)

Claudia automatically activates when you:
- Make technology decisions ("should I use MongoDB or Postgres?")
- Discuss architecture ("how should I structure this microservice?")
- Choose between frameworks ("React or Svelte for this project?")
- Write suboptimal prompts ("make it better")
- Introduce security anti-patterns

### Hooks (Always Active)

**Secret detection** (blocks):
- AWS access keys, OpenAI/Stripe keys, GitHub tokens, GitLab PATs, Slack tokens
- Hardcoded passwords, secrets, and API keys
- Database connection strings with credentials
- Private keys

**Anti-pattern warnings** (advisory):
- `eval()` usage, `document.write()`, `innerHTML`
- `console.log` in production code
- Empty catch blocks
- HTTP URLs (non-HTTPS), disabled SSL verification
- SQL string concatenation
- `chmod 777`
- TODO/FIXME markers in new code

**Dependency audit** (advisory):
- Deprecated packages (moment, request, gulp)
- Compromised packages (colors, faker, event-stream)
- Trivial packages (is-odd, is-even, left-pad)

**Dockerfile lint** (advisory):
- Running as root, large base images, `:latest` tag
- Missing multi-stage builds, secrets in ENV
- npm install without --production

**Git hygiene** (blocks/advisory):
- Writing to .env files (blocks)
- Merge conflict markers in code (blocks)
- Large binary files (advisory)

**Accessibility** (advisory):
- Images without alt text
- Inputs without labels
- Icon-only buttons without aria-label
- Click handlers on non-interactive elements
- Positive tabIndex values

**License compliance** (advisory):
- Copyleft dependencies (GPL, AGPL, SSPL) in permissive-licensed projects

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

- **All hook/script PRs require maintainer review** — markdown-only reference PRs are lower risk
- **No network calls in hooks** — no fetching URLs, no phoning home, local filesystem only
- **No obfuscated code** — every line must be readable and understandable
- Hook PRs get a dedicated security review with line-by-line diff and sandboxed testing

### Writing Guidelines
- Be opinionated -- "it depends" without follow-up is not helpful
- Use decision trees and comparison tables
- Explain the "why" behind every recommendation
- Include "when NOT to use this" alongside recommendations
- Keep SKILL.md under ~2000 words, put depth in references

## License

MIT
