# Claudia Website Sitemap

## Architecture

**Stack:** Static site. Astro or Next.js static export. Tailwind CSS. Deployed on Netlify.

**Domain:** getclaudia.dev

**Repo:** Same repo (`reganomalley/claudia`), `website/` directory. Or separate `claudia-website` repo if you want to keep plugin and site deployments independent.

---

## Pages

### 1. Home `/`

The conversion + showcase page. Single long-scroll page with clear sections.

#### Hero Section
- **Headline:** "The mentor in your terminal" (or chosen tagline)
- **Subhead:** "Claudia is a Claude Code plugin that catches security mistakes, advises on technology decisions, and coaches you to write better prompts. 10 knowledge domains. 7 automated hooks."
- **CTA:** `npm install -g claudia-mentor` (copy-to-clipboard) + "View on GitHub" secondary button
- **Visual:** Mascot illustration + animated terminal showing Claudia catching a hardcoded secret

#### How It Works (3 cards)
```
[Hooks icon]           [Skills icon]         [Commands icon]
Always watching        Ask anything          On-demand audits
7 hooks catch          10 knowledge          /claudia for questions
secrets, anti-         domains advise        /claudia-health for
patterns, bad deps     on tech decisions     full project scans
before they ship       with trade-offs       with scored reports
```

#### Live Demo Section
Animated terminal (TypeIt.js or similar) showing three scenarios:
1. **Secret blocked:** User writes an AWS key, Claudia blocks it with explanation
2. **Tech advice:** User asks "should I use MongoDB?", Claudia gives opinionated answer with trade-offs
3. **Health audit:** User runs `/claudia-health`, gets scored report

Each scenario: 10-15 seconds, auto-cycles with manual tabs.

#### Domain Showcase
Grid of 10 domain cards. Each card:
- Icon (simple, from illustration set)
- Domain name (e.g., "Databases")
- 2-line description
- One example question
- Click expands to show the decision tree or comparison table from that SKILL.md

#### Hook Showcase
Table or card grid of all 7 hooks:
```
Hook              | Type     | Catches
Secret detection  | Blocks   | AWS keys, API tokens, passwords, private keys
Git hygiene       | Blocks   | .env writes, merge conflict markers
Code practices    | Advisory | eval(), empty catch, console.log, SQL concat
Dependencies      | Advisory | Deprecated, compromised, trivial packages
Dockerfile lint   | Advisory | Root user, :latest, missing multi-stage
Accessibility     | Advisory | Missing alt text, unlabeled inputs
License           | Advisory | Copyleft deps in permissive projects
```

#### Social Proof / Metrics (once available)
- GitHub stars
- npm downloads
- "Used by X developers" (once you have telemetry or can estimate)
- Quotes from early users (collect these manually at first)

#### Install Section (repeated CTA at bottom)
```
# Install
npm install -g claudia-mentor

# Or clone directly
git clone https://github.com/reganomalley/claudia.git ~/.claude/plugins/claudia

# Enable in Claude Code
claude plugin add ~/.claude/plugins/claudia
```

#### Footer
- GitHub link
- npm link
- License (MIT)
- "Built by Regan O'Malley" with link to regan.life
- "Contribute a domain" link to contributing docs

---

### 2. Docs `/docs`

Living documentation pulled from the actual SKILL.md and reference files in the repo.

#### Structure:
```
/docs
  /getting-started          # Install, first run, configuration
  /domains
    /databases              # Rendered from claudia-databases SKILL.md
    /security               # Rendered from claudia-security SKILL.md
    /infrastructure
    /frontend
    /api
    /testing
    /performance
    /devops
    /data
    /mentor                 # Core brain, prompt coaching
  /hooks
    /secret-detection
    /code-practices
    /dependencies
    /dockerfile
    /git-hygiene
    /accessibility
    /license
  /configuration            # Proactivity levels, overrides, per-project config
  /contributing             # How to add domains, hooks, reference files
```

**Key design decision:** Docs should be auto-generated from the actual markdown files in the repo whenever possible. Use a build step that copies SKILL.md and reference files into the docs site. This way the docs never drift from the source.

#### Docs sidebar:
- Collapsible sections for Domains and Hooks
- Search (Algolia DocSearch or Pagefind for static)
- "Edit this page on GitHub" link on every page

---

### 3. Community/Contributing `/contribute`

A page designed to lower the barrier to contributing.

#### Sections:

**"The easiest open source contribution you'll ever make"**
- Contributing a reference file = writing one markdown document
- No code review, no tests, no build step
- Just knowledge in a specific format

**Contribution Types (ranked by effort):**
```
1. Add a reference file    (~30 min)  Drop a .md in references/
2. Add anti-pattern rules  (~1 hour)  Add entries to hook scripts
3. Improve a domain        (~2 hours) Expand SKILL.md or add references
4. Create a new domain     (~4 hours) Use create-domain.sh scaffold
5. Build a new hook        (~4 hours) Write a PreToolUse script
```

**Domain scaffolding:**
```bash
./scripts/create-domain.sh architecture
# Creates template SKILL.md + references/ directory
```

**Writing guidelines:**
- Be opinionated -- "it depends" without follow-up is not helpful
- Use decision trees and comparison tables
- Explain the "why" behind every recommendation
- Include "when NOT to use this"
- Keep SKILL.md under ~2000 words, depth goes in references

**Hall of contributors** -- auto-generated from git history, showing avatars of everyone who's contributed a domain or reference file.

---

### 4. Blog `/blog` (Phase 2)

For launch content and ongoing thought leadership:

**Launch posts:**
- "Why your AI coding assistant needs a mentor" (thesis post)
- "How Claudia catches secrets before they ship" (technical deep-dive)
- "The opinionated guide to database selection" (content marketing from claudia-databases)

**Ongoing:**
- New domain announcements
- "Claudia caught this" -- real examples of anti-patterns caught
- Guest posts from domain contributors

---

## Component Library

Reusable components needed for the site:

| Component | Usage |
|-----------|-------|
| `TerminalDemo` | Animated terminal showing Claudia in action |
| `DomainCard` | Grid card for each knowledge domain |
| `HookTable` | Table showing all hooks with type and catches |
| `InstallBlock` | Copy-to-clipboard install command |
| `CodeBlock` | Syntax-highlighted code with brand colors |
| `DecisionTree` | Rendered from markdown decision trees in SKILL.md |
| `ComparisonTable` | Styled tables from domain reference files |
| `ContributorGrid` | GitHub avatar grid from contributors |

---

## SEO Strategy

**Target keywords:**
- "claude code plugin"
- "claude code mentor"
- "AI coding assistant security"
- "best claude code plugins"
- "code review automation"
- "developer mentor tool"

**Each domain page** targets its own keywords:
- claudia-databases: "which database should I use", "SQL vs NoSQL decision"
- claudia-security: "JWT vs session authentication", "secrets management best practices"
- etc.

The knowledge in the SKILL.md files doubles as SEO content when rendered as docs pages.

---

## Launch Sequence

1. **Pre-launch:** GitHub repo public, README polished, plugin installable
2. **Website v1:** Home page + docs (auto-generated from repo)
3. **Announce:** Hacker News "Show HN", Reddit r/ClaudeAI, Twitter/X
4. **Week 1:** Monitor GitHub issues, respond to feedback, collect testimonials
5. **Week 2:** Blog post #1 (thesis), contribute page goes live
6. **Ongoing:** New domains = new blog posts = new SEO pages = more contributors

---

## Design Notes

- Dark mode default (devs expect it), with light mode toggle
- Terminal demos should feel real -- use actual Claudia output, not mockups
- Vermillion accent pops against dark backgrounds -- use it for CTAs and highlights
- The mascot illustration anchors the hero but doesn't overwhelm -- she's a guide, not a mascot brand
- Mobile: hero collapses to icon + headline + install button. Terminal demos become static screenshots on mobile.
- Page load target: <1s LCP. No heavy frameworks. Static site, aggressive caching, optimized images.
