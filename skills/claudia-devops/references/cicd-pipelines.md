# CI/CD Pipelines

## GitHub Actions

The most common CI for open-source and small-to-mid teams. Good enough for most projects, and you're already on GitHub.

### Key Patterns

**Matrix builds** -- test across multiple versions/OS in parallel:
```yaml
strategy:
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, macos-latest]
```

**Dependency caching** -- don't reinstall every time:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

**Artifacts** -- pass build output between jobs:
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/
```

**Reusable workflows** -- DRY your CI across repos:
```yaml
jobs:
  test:
    uses: your-org/.github/.github/workflows/test.yml@main
    with:
      node-version: 20
```

**Concurrency** -- cancel redundant runs:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Common Gotchas
- `actions/checkout` only fetches one commit by default. Need history? Set `fetch-depth: 0`
- Secrets aren't available in PRs from forks (security feature, not a bug)
- `GITHUB_TOKEN` permissions are read-only by default in forks
- Workflow files must be on the default branch to be triggered by new branches

## Other CI Systems

| System | Best For | Notes |
|--------|----------|-------|
| GitLab CI | Teams on GitLab | Tight integration, good built-in registry |
| CircleCI | Fast parallel builds | Excellent caching, orbs for reusable config |
| Buildkite | Self-hosted runners | Run CI on your own infra, scales well |
| Jenkins | Legacy / enterprise | Avoid for new projects if you can |
| Dagger | Portable pipelines | Write CI in Go/Python/TS, runs anywhere |

## Pipeline Design Principles

### Fast Feedback First

Put the fastest checks first. Don't wait 10 minutes for tests to find a lint error.

```
Order by speed:
1. Lint + format check (seconds)
2. Type check (seconds to low minutes)
3. Unit tests (low minutes)
4. Build (minutes)
5. Integration tests (minutes)
6. E2E tests (slow, run these last or in parallel)
```

### Parallelism

- Split tests across multiple runners (CircleCI has this built in, GH Actions needs manual splitting)
- Run lint, type-check, and tests in parallel jobs (they don't depend on each other)
- Use matrix builds for cross-platform testing

### Caching Dependencies

Cache aggressively -- dependency installation is the biggest time sink:
- **Node**: Cache `node_modules` or `~/.npm`, key on lockfile hash
- **Python**: Cache `~/.cache/pip` or virtualenv directory
- **Go**: Cache `~/go/pkg/mod`
- **Docker**: Cache layers with `--cache-from` or GitHub Actions cache backend

### Test Splitting

For large test suites:
- Split by timing data (CircleCI does this automatically)
- Split by directory or test file
- Run flaky tests in a separate job that doesn't block deploy

## Docker in CI

### Layer Caching

Docker builds are slow without caching. Use BuildKit cache mounts:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
```

### Multi-Stage Builds

Keep production images small:
```dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:20-slim AS production
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

### GitHub Container Registry (ghcr.io)

Free for public repos, included with GitHub plans for private. Push images directly from Actions:
```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
- uses: docker/build-push-action@v5
  with:
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Buildx for Multi-Platform

Build for ARM and x86 in one step:
```yaml
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
```

## Secrets in CI

- **Never echo secrets** in logs, even for debugging. CI logs are often visible to more people than you think.
- **Use platform secrets**: GitHub Actions secrets, GitLab CI variables (masked + protected), CircleCI contexts.
- **Rotate regularly**: Set a calendar reminder. 90 days for most secrets.
- **Scope narrowly**: Use environment-level secrets over repo-level when possible.
- **Audit access**: Review who has access to CI secrets quarterly.

## Environment Promotion

The golden rule: **same artifact through all environments.**

```
Build once → push to registry → deploy to dev → promote to staging → promote to prod

NOT: build for dev, build again for staging, build again for prod
```

- Use environment variables for environment-specific config, not different builds
- Tag images with git SHA, not `latest` (you need to know exactly what's running)
- Keep staging as close to production as possible (same infra, same config shape)

## Database Migrations in CI

Migrations are the scariest part of deploys. Handle them carefully:

- **Run migrations before app deploy** -- the new code expects the new schema
- **Test rollback**: Every migration should have a working `down` migration
- **Separate migration from app deploy**: Run migrations as a CI job, not on app startup
- **Backward-compatible migrations**: New code should work with both old and new schema during the rollback window
- **Large table migrations**: Use `pt-online-schema-change` (MySQL) or `pg_repack` (Postgres) to avoid locks

## Monorepo CI

### Affected-Only Builds

Don't rebuild everything when one package changes:

| Tool | Approach |
|------|----------|
| Nx | Dependency graph, only builds/tests affected projects |
| Turborepo | Similar to Nx, simpler config, Vercel-backed |
| Path filters | GH Actions `paths` trigger, simple but less precise |
| Changesets | Focused on versioning/publishing, pairs with Nx/Turbo |

### Path Filters in GitHub Actions

Simple approach for smaller monorepos:
```yaml
on:
  push:
    paths:
      - 'packages/api/**'
      - 'packages/shared/**'
```

### Nx/Turborepo Approach

More precise -- understands dependency graph:
```bash
# Only test projects affected by changes since main
npx nx affected --target=test --base=origin/main
npx turbo run test --filter=...[origin/main]
```

Cache task results remotely so CI doesn't redo work that a teammate already did.
