# Serverless and Edge Computing

## Serverless Platforms

| Platform | Runtime | Max Duration | Cold Start | Best For |
|----------|---------|-------------|------------|----------|
| AWS Lambda | Node, Python, Go, Rust, Java, .NET, custom | 15 min | 100ms-5s | AWS ecosystem, event-driven |
| GCP Cloud Functions | Node, Python, Go, Java, .NET, Ruby | 9 min (v1) / 60 min (v2) | 100ms-3s | GCP ecosystem, Firebase |
| Cloudflare Workers | JS/TS, WASM | 30s (free) / 15 min (paid) | ~0ms (V8 isolates) | Edge, low-latency, global |
| Vercel Functions | Node, Go, Python, Ruby | 10s (hobby) / 300s (pro) | 250ms-1s | Next.js apps |
| Netlify Functions | Node, Go | 10s (sync) / 15 min (background) | 200ms-1s | Jamstack sites |
| Deno Deploy | JS/TS | Unlimited (within reason) | ~0ms | Edge, TypeScript-native |
| AWS Lambda@Edge | Node, Python | 5s (viewer) / 30s (origin) | 50ms-2s | CloudFront transforms |

## When Serverless Works

Serverless is the right choice when your workload matches these patterns:

**Event-driven processing:**
- S3 upload triggers image resize
- Database change triggers notification
- Webhook handler processes incoming data
- Queue consumer processes messages one at a time

**Sporadic traffic:**
- Internal tools used during business hours
- Webhook endpoints that fire occasionally
- Scheduled reports (daily/weekly/monthly)
- APIs with unpredictable, bursty traffic

**Quick, stateless operations:**
- REST API endpoints that query a database and return results
- Data transformations (CSV parsing, format conversion)
- Authentication/authorization checks
- Sending emails or notifications

## When Serverless Doesn't Work

**Long-running processes (>15 min):**
- Video transcoding, large file processing
- ML model training
- Complex data migrations
- Use containers (ECS tasks, Cloud Run jobs) instead

**Consistent high throughput:**
- If you're always running at 100+ concurrent invocations, an always-on container is cheaper
- The break-even point is roughly 30-40% utilization -- above that, reserved containers win on cost
- At scale, Lambda's per-invocation pricing adds up fast

**Complex state management:**
- Multi-step workflows with shared state (use Step Functions if you must stay serverless)
- WebSocket connections (Lambda doesn't maintain connections; use API Gateway WebSocket or a dedicated service)
- In-memory caching (every invocation is a fresh environment)

**Cold-start sensitive workloads:**
- Real-time gaming, live trading
- Anything requiring sub-100ms P99 latency
- User-facing requests where a 2-second delay is unacceptable

## Cold Start Mitigation

Cold starts are the #1 complaint about serverless. Here's what actually helps:

| Strategy | How | Impact |
|----------|-----|--------|
| Smaller bundles | Tree-shake, remove unused dependencies | 30-50% faster cold starts |
| Lighter runtimes | Python/Node over Java/.NET. Go/Rust for fastest. | Java: 3-5s → Go: <100ms |
| Provisioned concurrency | Keep N instances warm (AWS Lambda) | Eliminates cold starts, costs more |
| Min instances | Same concept on Cloud Run | Eliminates cold starts, costs more |
| Edge functions | Cloudflare Workers, Deno Deploy use V8 isolates, no cold start | ~0ms cold start, limited runtime |
| SnapStart | AWS Lambda for Java -- snapshots JVM state | 90% reduction for Java |
| Keep dependencies minimal | Don't import all of `aws-sdk`, import specific clients | Significant for Node.js |

**Reality check:** For most web APIs, a 1-2 second cold start on the first request after idle is fine. Users won't notice if your health check endpoint keeps the function warm. Only optimize cold starts if you've measured them as an actual problem.

## Edge Computing

Edge computing runs your code at CDN points-of-presence, close to users globally. Sounds great, but it has real constraints.

### When Edge Makes Sense

- **Latency-critical global audiences**: Serving users on 5+ continents who all need fast responses
- **Simple transforms**: Rewriting headers, A/B test routing, geolocation-based redirects
- **Static generation at the edge**: ISR (Incremental Static Regeneration) on Vercel/Cloudflare
- **Auth token validation**: Checking JWTs at the edge before hitting your origin
- **Personalization without origin round-trip**: Locale, currency, basic personalization

### When Edge Doesn't Make Sense

- **Database access**: Your database is in one region. An edge function in Tokyo hitting a database in Virginia adds latency, not removes it. Solutions (replicated reads, edge databases like Turso/Neon) are emerging but not mature.
- **Complex business logic**: V8 isolate environments (Workers, Deno Deploy) have limited APIs -- no filesystem, limited npm compatibility, memory limits.
- **Heavy computation**: Edge environments have tight CPU and memory limits (128MB on Workers free tier).
- **When your users are in one region**: If 95% of traffic is US-East, edge adds complexity for no benefit. Just deploy in us-east-1.

### Edge Platforms Compared

| Platform | Runtime | Database Access | NPM Compat | Pricing |
|----------|---------|----------------|------------|---------|
| Cloudflare Workers | V8 isolates | D1 (SQLite), KV, R2 | Limited (no Node APIs) | 100K req/day free |
| Vercel Edge Functions | V8 isolates | Via API routes | Limited | Part of Vercel plan |
| Deno Deploy | Deno runtime | Deno KV | Deno + some npm | 100K req/day free |
| Fastly Compute | WASM | KV Store | N/A (WASM) | $50/mo + usage |
| Lambda@Edge | Node/Python | Via AWS APIs | Full Node.js | Per request + duration |

## Cost Comparison: Serverless vs Always-On

The break-even depends on traffic pattern. Here are concrete numbers:

### Low Traffic (1K requests/day)

- **Lambda**: ~$0.20/mo (basically free tier)
- **Cloud Run (scale to zero)**: ~$0 (free tier covers this)
- **Always-on container (Railway)**: ~$5/mo
- **Winner**: Serverless, by a lot

### Moderate Traffic (100K requests/day)

- **Lambda**: ~$15-30/mo (depends on duration and memory)
- **Cloud Run**: ~$10-25/mo
- **Always-on container (0.5 vCPU)**: ~$15/mo
- **Winner**: About even. Choose based on DX preference, not cost.

### High Traffic (1M requests/day)

- **Lambda**: ~$150-400/mo
- **Cloud Run**: ~$100-250/mo
- **Always-on container (2 vCPU)**: ~$60-80/mo
- **Winner**: Always-on container. At sustained load, per-request pricing loses.

### Very High Traffic (10M requests/day)

- **Lambda**: ~$1,500-4,000/mo
- **Always-on containers (autoscaled)**: ~$200-500/mo
- **Winner**: Containers, and it's not close.

**Rule of thumb:** Serverless is cheaper below ~30-40% utilization. Above that, switch to always-on. Most production APIs with steady traffic cross this threshold.

## Vendor Lock-In Considerations

Serverless has the highest lock-in risk in cloud computing. Be deliberate about where you accept it.

**High lock-in (hard to migrate):**
- AWS Step Functions (workflow definition language is proprietary)
- DynamoDB Streams → Lambda triggers (tightly coupled AWS services)
- API Gateway + Lambda authorizers (whole auth flow is AWS-specific)
- CloudFormation / SAM templates (rewrite for any other platform)

**Medium lock-in (some migration work):**
- Lambda function code (portable logic, but handler signature and deployment are platform-specific)
- Cloud Run (standard containers, just deploy elsewhere)
- SQS/SNS triggers (swap for RabbitMQ/NATS, but rewire the plumbing)

**Low lock-in (easy to migrate):**
- Cloudflare Workers using standard Web APIs (runs anywhere with V8)
- Containers with standard HTTP interfaces (deploy on any container platform)
- Functions that just wrap a library (the library moves with you)

**The pragmatic take:** Some lock-in is fine. The cost of avoiding all lock-in (writing abstraction layers, using lowest-common-denominator features) is usually higher than the cost of a future migration that may never happen. Accept lock-in deliberately, not accidentally.
