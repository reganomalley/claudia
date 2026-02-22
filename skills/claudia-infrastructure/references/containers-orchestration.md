# Containers and Orchestration

## When to Containerize

**Always containerize production services.** Containers give you reproducible builds, consistent environments, and deployment flexibility. The 30 minutes to write a Dockerfile saves you hours of "works on my machine" debugging.

**Skip containers for:**
- One-off scripts and CLI tools (just use the language runtime)
- Lambda/Cloud Functions (they have their own packaging)
- Static sites (just deploy the build output)
- Local development tools (use them if your team wants, but don't force it)

## Docker Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| `FROM ubuntu:latest` | 300MB+ image, unpinned version | Use `node:20-slim`, `python:3.12-slim`, or `alpine` variants |
| No `.dockerignore` | Copies `node_modules`, `.git`, secrets into image | Add `.dockerignore` mirroring `.gitignore` + add `.git`, `*.md` |
| Running as root | Container compromise = root access | Add `USER nonroot` after installing dependencies |
| Single-stage build | Build tools in production image (larger, more attack surface) | Multi-stage: build in one stage, copy artifacts to slim runtime stage |
| No health check | Orchestrator can't tell if your app is actually working | Add `HEALTHCHECK CMD curl -f http://localhost:3000/health` |
| `COPY . .` before `npm install` | Cache busts on every code change | Copy `package*.json` first, install, then copy source |
| Hardcoded env vars | Secrets baked into image layer | Use `ENV` for defaults, override at runtime with `-e` or env files |
| No `.dockerignore` for secrets | `.env` files end up in the image | Always add `.env*` to `.dockerignore` |

## Dockerfile Best Practices

Here's a production-ready Node.js example showing all the right patterns:

```dockerfile
# Build stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:20-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

Key points:
- **Multi-stage**: Build tools stay in the builder stage, production image is lean
- **Layer ordering**: `package*.json` copied before source so `npm ci` layer is cached
- **Non-root user**: Created and switched to before CMD
- **Health check**: Orchestrator knows if the app is alive
- **Slim base**: `node:20-slim` instead of `node:20` (150MB vs 350MB)

## The Orchestration Ladder

Don't jump to Kubernetes. Walk up the ladder based on actual need.

### Level 1: Single Container

**When:** One service, one server. Most MVPs and side projects.

```bash
docker run -d --restart=unless-stopped -p 3000:3000 --name myapp myapp:latest
```

Good enough for a surprising number of production workloads. Add Watchtower for auto-updates, Caddy or nginx for TLS.

### Level 2: Docker Compose

**When:** 2-3 services that work together locally and in simple production setups.

```yaml
services:
  app:
    build: .
    ports: ["3000:3000"]
    depends_on: [db, redis]
    restart: unless-stopped
  db:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

Docker Compose is great for development. For production, it works on a single host but has no multi-host scaling, no rolling deploys, no self-healing. Fine for small apps, not for anything that needs uptime guarantees.

### Level 3: Managed Container Services

**When:** You need production-grade deployment without Kubernetes complexity. This is the sweet spot for most teams.

| Service | Cloud | Best For |
|---------|-------|----------|
| ECS + Fargate | AWS | AWS shops, no server management, pay-per-task |
| Cloud Run | GCP | Simplest DX, scale-to-zero, request-based pricing |
| Fly.io | Independent | Multi-region, great DX, good for full-stack apps |
| Railway | Independent | Fastest from zero to deployed, Git-push deploys |
| Render | Independent | Heroku replacement, simple and predictable |
| Azure Container Apps | Azure | Azure shops, Dapr integration |

**ECS + Fargate specifics:**
- No servers to manage. Define task (container config) and service (how many, where).
- Pricing: per vCPU-hour and GB-hour. A 0.5 vCPU / 1GB task runs ~$15/mo.
- Networking can be complex (VPC, security groups, ALB target groups). But once set up, it's solid.
- Use Copilot CLI to avoid the CloudFormation pain.

**Cloud Run specifics:**
- Deploy a container, get a URL. Genuinely that simple.
- Scale to zero (pay nothing when no traffic). Scale up to 1000 instances.
- Request-based pricing: $0.40/million requests + compute time. Cheapest option for sporadic traffic.
- Cold starts: typically 1-5 seconds. Use min-instances to avoid if needed.

**Fly.io specifics:**
- Multi-region by default. Deploy close to your users.
- Built-in Postgres (LiteFS for SQLite replication).
- `fly launch` from a Dockerfile = deployed in minutes.
- Pricing is VM-based, not request-based. More predictable for steady traffic.

### Level 4: Kubernetes

**When:** You actually need it. Which means:
- 5+ services with complex inter-service communication
- Need custom operators, CRDs, or service mesh
- Team has Kubernetes expertise (or budget to acquire it)
- Complex deployment patterns (canary, blue-green, traffic splitting)
- Running across multiple regions with sophisticated failover

**When you don't need it:**
- You have < 5 services (use Level 3)
- Your team is < 5 engineers (operational overhead will slow you down)
- You're a startup (ship features, not YAML)
- "We might need it someday" (you can migrate later, it's not that hard)

**If you DO use Kubernetes:**
- Use a managed service (EKS, GKE, AKS). Never self-host the control plane.
- GKE is the best managed Kubernetes. Autopilot mode removes node management entirely.
- EKS is the most common but has rougher edges. Use eksctl or Terraform, not the console.
- Invest in a platform team or use a platform tool (Backstage, Humanitec, Porter).
- Learn Helm basics, but consider Kustomize for simpler cases.
- Set resource requests and limits from day one. Unbounded pods will eat your cluster.

## Comparison Table: Managed Container Services

| Feature | ECS Fargate | Cloud Run | Fly.io | Railway | Render |
|---------|------------|-----------|--------|---------|--------|
| Scale to zero | No (min 1 task) | Yes | No (min 1 VM) | Yes | Yes (paid) |
| Cold start | N/A | 1-5 sec | N/A | ~5 sec | ~5 sec |
| Multi-region | Manual | Manual | Built-in | No | No |
| Custom domains | Via ALB | Built-in | Built-in | Built-in | Built-in |
| Git deploy | Via CI/CD | Yes | Yes | Yes | Yes |
| GPU | Yes | Yes (preview) | Yes | No | No |
| Pricing model | Per vCPU-hr | Per request + CPU | Per VM | Per usage | Per instance |
| Min monthly cost | ~$15 | ~$0 | ~$3 | ~$0 | ~$0 |
| Best for | AWS teams | GCP / simplicity | Multi-region | Prototypes | Heroku migrants |
