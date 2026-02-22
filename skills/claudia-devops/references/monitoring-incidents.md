# Monitoring and Incident Response

## Monitoring Stacks

| Stack | Best For | Notes |
|-------|----------|-------|
| Datadog | Premium all-in-one | Expensive but covers metrics, logs, traces, APM, synthetics. Good if budget allows. |
| Grafana + Prometheus | Open-source, self-hosted | Free, powerful, industry standard. Steeper setup curve. |
| New Relic | APM-focused | Good free tier, strong application performance monitoring |
| Sentry | Error tracking | Best-in-class error tracking with context. Free tier is generous. |
| Betterstack / UptimeRobot | Uptime monitoring | Simple, cheap, start here |
| Grafana Cloud | Managed open-source | Grafana + Prometheus + Loki without running the infra |

### Starting Stack (free or cheap)

For a new project, start with:
1. **UptimeRobot or Betterstack** -- is it up? (free tier)
2. **Sentry** -- what's erroring? (free tier)
3. **Structured logging to stdout** -- what happened? (free, your platform captures it)

Add Datadog or Grafana Cloud when you have multiple services or need dashboards.

## What to Monitor

### The Four Golden Signals

Google's SRE book nailed it. Monitor these four things and you'll catch most problems:

1. **Latency** -- how long requests take. Track p50 (median), p95, and p99 separately. The p99 is where the pain hides.
2. **Traffic** -- requests per second. Know your baseline so you notice anomalies.
3. **Errors** -- error rate as a percentage. 0.1% might be fine; 5% is a problem. Track by type (4xx vs 5xx).
4. **Saturation** -- how full your resources are. CPU, memory, disk, database connections, queue depth.

### What to Track at Each Layer

**Application:**
- Request count, latency, error rate (by endpoint)
- Business metrics (signups, purchases, API calls)
- Queue depth and processing time
- Cache hit rate

**Infrastructure:**
- CPU, memory, disk usage (alert at 80%, not 95%)
- Network I/O, connection counts
- Container restarts, OOM kills

**Database:**
- Query latency (slow query log)
- Connection pool usage
- Replication lag
- Lock contention

**External dependencies:**
- Third-party API latency and error rate
- DNS resolution time
- CDN hit rate

## Alerting

### Principles

**Alert on symptoms, not causes.** Alert on "error rate > 1%" not "CPU > 80%." High CPU that doesn't affect users isn't an alert -- it's a dashboard metric.

**Avoid alert fatigue.** Every alert should require human action. If you're ignoring alerts, you have too many. Delete or downgrade them.

**Three levels:**
- **Page** (wake someone up): User-facing impact right now. Error rate spike, complete outage, data loss risk.
- **Ticket** (fix this week): Degraded performance, disk filling up, certificate expiring soon.
- **Log** (check when convenient): Elevated latency, retry rate increase, minor anomaly.

### Alert Tools

| Tool | Best For |
|------|----------|
| PagerDuty | On-call scheduling, escalation policies, industry standard |
| Opsgenie | Similar to PagerDuty, Atlassian ecosystem |
| Betterstack | Simple on-call + status page |
| Slack alerts | Non-urgent notifications (never for pages) |

### Good Alert Checklist

Every alert should answer:
- What is broken? (clear, specific description)
- How bad is it? (error rate, affected users)
- What should I do? (link to runbook or dashboard)

## Logging

### Structured Logging

Always log in structured format (JSON). Never parse free-text log messages.

```json
{
  "level": "error",
  "message": "Payment processing failed",
  "service": "billing",
  "request_id": "abc-123",
  "user_id": "usr_456",
  "error_code": "STRIPE_DECLINED",
  "duration_ms": 2340,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Correlation IDs

Pass a request ID through every service. When something fails, you can trace the entire request path across services. Generate at the edge (API gateway or first service), propagate in headers.

### Log Levels

| Level | Use For | Example |
|-------|---------|---------|
| ERROR | Something broke, needs attention | Payment failed, database connection lost |
| WARN | Something unexpected, might become a problem | Retry succeeded, approaching rate limit |
| INFO | Normal operations worth recording | Request completed, job finished, deploy started |
| DEBUG | Development detail, off in production | Query parameters, cache decisions |

### What NOT to Log

- **PII**: Names, emails, addresses, phone numbers (mask or hash them)
- **Secrets**: API keys, passwords, tokens (never, ever)
- **Full request/response bodies**: Too verbose, may contain PII. Log a summary.
- **Health check requests**: They'll drown out everything else

### Log Aggregation

| Tool | Type | Notes |
|------|------|-------|
| ELK (Elasticsearch + Logstash + Kibana) | Self-hosted | Powerful but heavy to operate |
| Loki + Grafana | Self-hosted or cloud | Lightweight, label-based, pairs with Prometheus |
| Datadog Logs | SaaS | Expensive at scale, great if already using Datadog |
| CloudWatch Logs | AWS-native | Fine for AWS, painful search UX |

## Incident Response

### The Playbook

```
1. DETECT   -- Alert fires or user reports issue
2. TRIAGE   -- How bad is it? Who's affected? What's the blast radius?
3. MITIGATE -- Rollback first, debug later. Restore service ASAP.
4. RESOLVE  -- Fix the root cause (after service is restored)
5. POSTMORTEM -- What happened, why, and how do we prevent it?
```

### Key Principles

**Rollback first, debug later.** The goal during an incident is to restore service, not to understand why it broke. Roll back the last deploy. If that doesn't fix it, roll back the one before that. Debug in staging afterward.

**Communicate early and often.** Update your status page. Tell support. Tell stakeholders. Silence during an outage is worse than "we're investigating."

**One incident commander.** Someone owns the incident. They coordinate, they communicate, they decide. Everyone else executes.

**Time-box investigation.** If you can't identify the cause in 15 minutes, escalate or rollback harder. Don't spend an hour debugging while users are down.

## SLIs, SLOs, and Error Budgets

### Definitions

- **SLI (Service Level Indicator)**: A measurement. "99.2% of requests completed in under 200ms."
- **SLO (Service Level Objective)**: A target. "We aim for 99.9% of requests under 200ms."
- **SLA (Service Level Agreement)**: A contract. "If we drop below 99.5%, we owe you credits." (Business decision, not engineering.)

### Picking SLOs

Choose 3-5 SLIs that actually reflect user experience:
- **Availability**: Percentage of successful requests (non-5xx)
- **Latency**: p99 response time for critical endpoints
- **Correctness**: Percentage of requests that return the right answer (for data-heavy services)
- **Freshness**: How old is the data? (for async/eventual consistency systems)

### The Nines

| SLO | Downtime/month | Downtime/year | Reality |
|-----|---------------|---------------|---------|
| 99% | 7.3 hours | 3.65 days | Hobby project |
| 99.9% | 43.8 minutes | 8.76 hours | Most SaaS products |
| 99.95% | 21.9 minutes | 4.38 hours | Serious business apps |
| 99.99% | 4.3 minutes | 52.6 minutes | Requires redundancy everywhere |
| 99.999% | 26 seconds | 5.26 minutes | You need a dedicated SRE team |

The difference between 99.9% and 99.99% is enormous in engineering effort and cost. Most teams should target 99.9% and be honest about it.

### Error Budgets

If your SLO is 99.9%, you have a 0.1% error budget per month. That's about 43 minutes of downtime.

- **Budget remaining**: Ship features, experiment, take risks
- **Budget spent**: Freeze deploys, focus on reliability, pay down tech debt

This turns reliability from a feeling ("things seem flaky") into a number you can make decisions with.

## Postmortems

### Blameless Postmortems

The goal is systemic improvement, not finding someone to blame. If a human made an error, the system should have prevented it or limited the blast radius.

### Template

Every postmortem should cover:

1. **Summary**: What happened, in one paragraph
2. **Impact**: Duration, affected users, revenue impact
3. **Timeline**: Minute-by-minute, what happened and when
4. **Root cause**: The actual underlying cause (not "John pushed bad code" but "no integration tests for the payment path")
5. **What went well**: Detection was fast, rollback worked, communication was clear
6. **What went poorly**: Took 30 minutes to identify the cause, no runbook existed
7. **Action items**: Specific, with owners and due dates. Not "be more careful" but "add integration test for payment flow (owner: Sarah, due: Jan 22)"

### Common Anti-Patterns

- **No action items**: A postmortem without action items is a story, not an improvement
- **Action items with no owners**: They won't get done
- **"Be more careful"**: This is not an action item. Systems should prevent mistakes.
- **Skipping postmortems for "small" incidents**: Small incidents reveal the same systemic issues as big ones
