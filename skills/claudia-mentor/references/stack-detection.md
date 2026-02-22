# Stack Detection Guide

When Claudia needs to give context-aware advice, it should read the user's project files to understand what they're actually using. This makes advice specific instead of generic.

## Files to Check

### Package Ecosystem
- **`package.json`** -- Node.js/frontend: dependencies, devDependencies, scripts, engines
- **`requirements.txt`** / **`pyproject.toml`** / **`Pipfile`** -- Python
- **`go.mod`** -- Go
- **`Cargo.toml`** -- Rust
- **`Gemfile`** -- Ruby
- **`pom.xml`** / **`build.gradle`** -- Java

### Framework Detection (from package.json dependencies)
| Dependency | Framework |
|-----------|-----------|
| `next` | Next.js (check for `app/` vs `pages/` directory) |
| `nuxt` | Nuxt |
| `@sveltejs/kit` | SvelteKit |
| `astro` | Astro |
| `remix` / `@remix-run/*` | Remix |
| `express` | Express.js |
| `fastify` | Fastify |
| `hono` | Hono |
| `django` (Python) | Django |
| `flask` (Python) | Flask |
| `fastapi` (Python) | FastAPI |

### Database Detection
- **`prisma/schema.prisma`** -- Prisma ORM (check `datasource` for DB type)
- **`drizzle.config.ts`** -- Drizzle ORM
- **`knexfile.js`** -- Knex.js
- **`docker-compose.yml`** -- Look for `postgres`, `mysql`, `mongo`, `redis` services
- **`.env`** / **`.env.example`** -- Look for `DATABASE_URL`, `REDIS_URL`, etc.

### Infrastructure Detection
- **`Dockerfile`** -- Containerized
- **`docker-compose.yml`** -- Multi-service setup
- **`fly.toml`** -- Fly.io
- **`vercel.json`** -- Vercel
- **`netlify.toml`** -- Netlify
- **`railway.json`** -- Railway
- **`serverless.yml`** -- Serverless Framework
- **`terraform/`** / **`*.tf`** -- Terraform
- **`pulumi/`** -- Pulumi
- **`.github/workflows/`** -- GitHub Actions CI

### Config Detection
- **`tsconfig.json`** -- TypeScript (check `strict`, `target`, `module`)
- **`tailwind.config.*`** -- Tailwind CSS
- **`.eslintrc.*`** -- ESLint config
- **`vite.config.*`** -- Vite
- **`webpack.config.*`** -- Webpack
- **`jest.config.*`** / **`vitest.config.*`** -- Test framework
- **`playwright.config.*`** -- Playwright E2E

## How to Use This

When a domain skill is activated, the mentor should:

1. **Read `package.json`** (or equivalent) in the current project root
2. **Scan for config files** using Glob patterns
3. **Adjust advice** based on what's actually there

### Example: Database Question

Without stack detection: "You could use PostgreSQL, MySQL, or MongoDB..."

With stack detection (after reading `package.json` and `docker-compose.yml`):
"You're already running Postgres in Docker and using Prisma. For this use case, add a Prisma model with a JSONB field -- no need for a separate document store."

### Example: Testing Question

Without: "Popular options include Jest, Vitest, and Mocha..."

With (after reading `vitest.config.ts` and `package.json`):
"You're using Vitest already. For this integration test, use Vitest's `beforeAll` to spin up the test DB, and the `vi.mock` for the external API call."

## Integration with Skills

Each domain skill's SKILL.md should include a note like:

> Before answering, check the project context. Read `package.json` and scan for relevant config files using Glob. Tailor your recommendation to the user's actual stack.

This turns generic "here are your options" advice into specific "here's what to do in your project" guidance.
