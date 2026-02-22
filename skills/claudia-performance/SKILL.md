---
description: >
  Performance knowledge domain for Claudia. Use this skill when the user asks about optimization,
  profiling, caching, bundle size, load times, database query performance, memory leaks, N+1 queries,
  or scaling bottlenecks. Triggers on phrases like "slow", "optimize", "performance", "caching",
  "bundle size", "lazy load", "N+1", "memory leak", "profiling", "bottleneck", "latency",
  "throughput", or "Core Web Vitals".
---

# Claudia Performance Domain

## Overview

Don't optimize until you've measured. The bottleneck is never where you think it is. Most performance work is wasted because developers optimize the wrong thing based on intuition instead of data. Measure first, fix the actual problem, measure again to confirm.

## Before You Optimize

Run through this checklist every time, no exceptions:

1. **Is it actually slow?** Define "slow." If you can't point to a number that's too high, you don't have a performance problem -- you have a feeling.
2. **Have you measured?** Profiler output, not vibes. Browser DevTools, EXPLAIN ANALYZE, `time` command, APM traces. Something concrete.
3. **What's the target?** "Faster" is not a target. "p95 response time under 200ms" is a target. "LCP under 2.5s" is a target.
4. **Will users notice?** Going from 50ms to 10ms is impressive engineering and invisible to users. Going from 3s to 1s changes behavior.

## Performance Layers

Work top-down. Fixing a slow query doesn't help if you're sending 4MB of uncompressed JavaScript.

```
Where is it slow?
├── Network
│   ├── Large payloads → Compression (Brotli > gzip), CDN, image optimization
│   ├── Too many requests → HTTP/2, bundling, preconnect, prefetch
│   ├── No caching → Cache-Control headers, CDN, service worker
│   └── High latency → Edge deployment, CDN, regional replicas
├── Backend
│   ├── Slow queries → EXPLAIN ANALYZE, indexes, N+1 fixes
│   ├── No caching → Redis, application-level cache, materialized views
│   ├── Blocking operations → Async processing, queues, background jobs
│   └── CPU-bound work → Algorithm optimization, caching computed results, horizontal scaling
└── Frontend
    ├── Large bundle → Code splitting, tree shaking, dynamic imports
    ├── Slow rendering → Virtualization, CSS containment, reduce layout thrashing
    ├── Heavy images → WebP/AVIF, responsive images, lazy loading
    └── Layout shifts → Explicit dimensions, font-display swap, placeholder skeletons
```

## Common Bottlenecks

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| API responses >500ms | Unindexed query or N+1 | EXPLAIN ANALYZE, add index, eager load |
| Page load >3s | Large JS bundle or unoptimized images | Code split, compress, lazy load images |
| UI jank / dropped frames | Layout thrashing or main thread blocking | Batch DOM reads/writes, use requestAnimationFrame |
| Memory grows over time | Event listener leaks, unbounded caches | Heap snapshot, WeakRef, cache eviction |
| Works locally, slow in prod | Missing indexes, no CDN, cold caches | Mirror prod data locally, add CDN, warm caches |
| Slow under load | Connection pool exhaustion, no caching | Pool sizing, add Redis, horizontal scale |
| First load slow, navigations fine | No code splitting, large initial bundle | Route-based splitting, prefetch critical routes |
| Database CPU pegged | Missing indexes, full table scans | EXPLAIN ANALYZE, composite indexes, query rewrite |

## Caching Hierarchy

Caching is the most powerful performance tool you have. Use the right layer:

```
Request comes in
├── Browser cache (Cache-Control headers)
│   └── Free, instant. Set proper max-age, use immutable for hashed assets.
├── CDN cache (Cloudflare, CloudFront, Vercel Edge)
│   └── Edges close to users. Cache static assets aggressively, API responses carefully.
├── Application cache (Redis, Memcached)
│   └── Your computed results, session data, API responses from upstream.
├── Query cache (ORM-level, prepared statements)
│   └── Avoid re-parsing. Most ORMs handle this. Don't over-cache here.
└── Materialized views (database-level)
    └── Precomputed aggregations. Refresh on schedule or trigger.
```

**Cache invalidation** is the hard part. Three strategies:
- **TTL-based**: Simple, eventually consistent. Good for most things.
- **Event-based**: Invalidate on write. More complex, more correct.
- **Versioned keys**: Include version in cache key, bump on change. Never stale, but cold misses.

## Quick Wins

Try these before deep optimization. They fix 80% of performance issues:

1. **Add a CDN** -- Cloudflare free tier is fine. Instant win for static assets.
2. **Enable compression** -- Brotli if your server supports it, gzip otherwise.
3. **Add database indexes** -- Run EXPLAIN on your slowest queries. Add indexes for WHERE and JOIN columns.
4. **Lazy load images** -- `loading="lazy"` on img tags below the fold.
5. **Code split routes** -- Dynamic `import()` for routes users don't hit on first load.
6. **Cache API responses** -- Even 60 seconds of Redis caching dramatically reduces database load.
7. **Use connection pooling** -- If you're opening a new DB connection per request, stop.
8. **Set Cache-Control headers** -- Hashed static assets get `max-age=31536000, immutable`.

## Deep References

For detailed guidance on specific topics, load:
- `references/backend-performance.md` -- Database queries, caching patterns, async processing, profiling
- `references/frontend-performance.md` -- Core Web Vitals, bundle optimization, rendering, React-specific

## Response Format

When advising on performance:
1. **What's slow** (identify the specific bottleneck with evidence)
2. **Why it's slow** (root cause, not symptoms)
3. **How to fix it** (concrete steps, not "optimize your queries")
4. **How to verify it worked** (what to measure, what the target is)
