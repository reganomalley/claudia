---
description: >
  DevOps and CI/CD knowledge domain for Claudia. Use this skill when the user asks about deployment
  strategies, CI/CD pipelines, monitoring, logging, alerting, incident response, infrastructure as
  code, or developer experience. Triggers on phrases like "deploy", "CI/CD", "GitHub Actions",
  "monitoring", "logging", "alerting", "uptime", "rollback", "blue-green", "canary", "Terraform",
  "infrastructure as code", "Docker in CI", or "pipeline".
---

# Claudia DevOps Domain

## Overview

DevOps is about shipping with confidence and sleeping through the night. Automate the boring stuff, monitor the important stuff. If your deploy process has a wiki page with 15 manual steps, something has gone wrong.

## Decision Trees

### Deployment Strategy: Where Are You?

```
What are you deploying?
├── Static site (HTML, SPA, docs)
│   └── Netlify / Vercel / Cloudflare Pages -- just push to main
├── Simple app (one service, one database)
│   └── PaaS: Railway / Render / Fly.io -- git push deploys, managed infra
├── Multi-service (2-5 services talking to each other)
│   └── Container orchestration: Docker Compose → ECS / Cloud Run
├── Enterprise (many teams, compliance, multi-region)
│   └── Kubernetes + GitOps (ArgoCD / Flux)
└── Not sure
    └── Start with PaaS. Move down only when you hit real limits.
```

### CI/CD Pipeline Template

```
Every pipeline follows this shape:

  lint → test → build → deploy staging → smoke test → deploy prod

Specifics:
├── Lint + type-check (fastest, catches dumb mistakes first)
├── Unit tests (fast, high coverage)
├── Build artifact (Docker image, static bundle, binary)
├── Deploy to staging (automatic on merge to main)
├── Smoke tests against staging (health check, critical paths)
├── Deploy to production (automatic or manual gate)
└── Post-deploy verification (synthetic monitoring, error rate check)
```

### Deployment Patterns

| Pattern | How It Works | Use When | Risk |
|---------|-------------|----------|------|
| Rolling | Replace instances one at a time | Default for most apps | Brief mixed versions |
| Blue-Green | Run two identical envs, swap traffic | Zero-downtime required | 2x infrastructure cost |
| Canary | Route small % of traffic to new version | High-traffic, risk-averse | Complex routing setup |
| Feature Flags | Deploy code dark, enable for users | Decouple deploy from release | Flag debt accumulates |
| Recreate | Kill old, start new | Dev/staging, downtime OK | Downtime during deploy |

**Default recommendation:** Rolling deploy with health checks. Add blue-green when downtime costs money. Add canary when a bad deploy costs a lot of money.

### Monitoring Hierarchy

```
Start at the top, add layers as you need them:

Level 0: Uptime checks (is it responding?)
   └── Free: UptimeRobot, Betterstack
Level 1: Error tracking (what's breaking?)
   └── Sentry, Bugsnag
Level 2: APM (what's slow?)
   └── Datadog, New Relic, Grafana Cloud
Level 3: Logs (what happened?)
   └── Structured logging → ELK, Loki, Datadog Logs
Level 4: Metrics + dashboards (trends over time)
   └── Prometheus + Grafana, Datadog
Level 5: Distributed tracing (where's the bottleneck across services?)
   └── Jaeger, Tempo, Datadog APM
```

Most teams should have Levels 0-2 from day one. Add 3-5 as complexity grows.

## Quick Comparisons

| Need | Start Here | Level Up When |
|------|-----------|---------------|
| Static deploy | Netlify / Vercel | Need edge functions or custom infra |
| App deploy | Railway / Render | Need custom networking or >$100/mo savings |
| Containers | Docker Compose + Cloud Run | Multi-service orchestration → ECS or k8s |
| CI/CD | GitHub Actions | Need self-hosted runners or complex pipelines |
| Monitoring | Sentry + UptimeRobot | Need APM or distributed tracing → Datadog |
| Logging | Console + structured JSON | Need search/alerting → Loki or ELK |
| Secrets in CI | Platform secrets (GH Actions) | Need rotation/audit → Vault or Doppler |
| IaC | Terraform | Already on AWS → consider CDK; Pulumi for TS fans |

## Deep References

For detailed guidance on specific topics, load:
- `references/cicd-pipelines.md` -- Pipeline design, GitHub Actions, Docker in CI, monorepo strategies
- `references/monitoring-incidents.md` -- Monitoring stacks, alerting, incident response, SLOs

## Response Format

When advising on DevOps:
1. **What stage are you at?** (match recommendation to actual complexity)
2. **Concrete tool/pattern** (not abstract principles)
3. **The pipeline sketch** (what runs when, in what order)
4. **What to monitor** (you're not done until you know it's working)
