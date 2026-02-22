---
name: claudia-infrastructure
description: >
  Infrastructure knowledge domain for Claudia. Use this skill when the user asks about cloud providers,
  AWS vs GCP vs Azure, containerization, Kubernetes, serverless, hosting, deployment infrastructure,
  CDNs, load balancers, DNS, or cloud architecture decisions. Triggers on phrases like "which cloud",
  "should I use AWS", "Kubernetes vs", "serverless", "deploy to", "hosting", "containers", "ECS vs EKS",
  "Lambda vs", "cloud costs", "self-host", or "infrastructure for".
version: 0.1.0
---

# Claudia Infrastructure Domain

## Overview

This skill helps you pick where and how to run your software. Most projects are over-infrastructured -- your goal is the simplest setup that meets your actual requirements, not the one that looks best on a resume.

## Where Should This Run?

```
What are you deploying?
├── Static site (HTML, SPA, docs)
│   └── Vercel, Netlify, Cloudflare Pages (free tier is enough for most)
├── Web app (server-rendered, full-stack)
│   ├── Simple / solo dev → Railway, Render, Fly.io
│   ├── Scaling / team → ECS Fargate, Cloud Run, App Engine
│   └── Enterprise / complex → Kubernetes (EKS, GKE)
├── API service (REST, GraphQL, gRPC)
│   ├── Sporadic traffic → Lambda, Cloud Functions, Cloudflare Workers
│   ├── Steady traffic → Container on Fly.io, Cloud Run, ECS
│   └── High throughput → Dedicated instances behind ALB
├── Data pipeline (ETL, batch processing)
│   ├── Simple / scheduled → Lambda + EventBridge, Cloud Functions + Scheduler
│   ├── Complex / multi-step → Step Functions, Cloud Workflows, Airflow
│   └── Big data → EMR, Dataproc, Spark on Kubernetes
└── ML inference
    ├── Low traffic → Lambda (small models), Cloud Run + GPU
    ├── Real-time → SageMaker endpoints, Vertex AI, dedicated GPU instances
    └── Batch → SageMaker Batch Transform, Vertex AI Batch Prediction
```

## The Cloud Provider Question

There is no universally "best" cloud. There's the best cloud for your situation.

- **AWS**: Most services, most mature, largest community. If you have no strong reason to pick something else, AWS is the safe default. But the console is a maze and IAM will make you cry.
- **GCP**: Best developer experience for data and ML workloads. BigQuery is unmatched. GKE is the best managed Kubernetes. But smaller service catalog and less enterprise presence.
- **Azure**: The answer when your company already runs on Microsoft -- Active Directory, .NET, Office 365. Enterprise integration is its moat. Developer experience is improving but still trails.
- **Self-host**: When you need full control, cost predictability, or data sovereignty. Hetzner, OVH, bare metal. Be honest about your ops capacity -- this means you're the on-call team.

**The real advice:** Pick one cloud and go deep. Multi-cloud sounds smart but usually means double the operational complexity for marginal benefit. The exception is using a CDN (Cloudflare) in front of any cloud.

## Quick Comparisons

| Need | First Choice | When to Upgrade |
|------|-------------|----------------|
| Static site | Vercel / Netlify | You probably don't |
| Side project / MVP | Railway / Render | When you need custom networking or >$50/mo |
| Production web app | Cloud Run / ECS Fargate | When you need complex service mesh → Kubernetes |
| REST API | Cloud Run / Fly.io | High throughput + low latency → dedicated instances |
| Background jobs | Lambda / Cloud Functions | Long-running (>15min) → ECS tasks or dedicated workers |
| Full-stack monolith | Fly.io / Railway | Scaling beyond single region → Cloud Run or ECS |
| Microservices (5+) | Kubernetes (EKS/GKE) | This is already the heavy option |

## Container Orchestration

```
How many services are you running?
├── 1 service
│   └── docker run on a VM, or just use Railway/Render
├── 2-4 services
│   └── docker-compose (dev), ECS Fargate / Cloud Run / Fly.io (prod)
├── 5-10 services
│   └── Consider Kubernetes (EKS, GKE) or stick with ECS if on AWS
└── 10+ services with complex networking
    └── Kubernetes is justified. Invest in platform engineering.
```

**The Kubernetes rule:** Don't use Kubernetes unless you have 5+ services AND a team that can operate it. A bad Kubernetes setup is worse than no orchestration at all. ECS, Cloud Run, and Fly.io handle the 2-4 service range without the operational tax.

## Serverless

```
Is serverless right for this?
├── Event-driven (webhooks, S3 triggers, queue consumers) → YES
├── Sporadic traffic (minutes/hours between requests) → YES
├── Quick APIs (<15 min execution, stateless) → YES
├── Cron jobs (scheduled, short-lived) → YES
├── Long-running processes (>15 min) → NO, use containers
├── Consistent high throughput → NO, always-on is cheaper
├── Complex state management → NO, use a persistent service
└── Cold-start sensitive (sub-100ms required) → MAYBE, edge functions or provisioned concurrency
```

## Deep References

For detailed guidance on specific topics, load:
- `references/cloud-providers.md` -- Deep comparison of AWS, GCP, Azure, self-hosting
- `references/containers-orchestration.md` -- Docker, Kubernetes, and alternatives
- `references/serverless-edge.md` -- Serverless platforms, edge computing, cost models

## Response Format

When advising on infrastructure:
1. **Recommendation** (specific service or platform)
2. **Why it fits** (match to their scale, team, and requirements)
3. **Cost implications** (ballpark monthly cost and what drives it up)
4. **Migration path** (how to move when you outgrow this choice)
