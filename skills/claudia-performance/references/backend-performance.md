# Backend Performance

## Database Query Optimization

### EXPLAIN ANALYZE Is Your Best Friend

Never guess why a query is slow. Run `EXPLAIN ANALYZE` (Postgres) or `EXPLAIN` with `FORMAT=JSON` (MySQL) and read the output.

**What to look for:**
- **Seq Scan** on a large table: You're missing an index
- **Nested Loop** with high row counts: Likely an N+1 or a missing JOIN index
- **Sort** with high cost: Consider an index that matches your ORDER BY
- **Hash Join** with massive hash table: Your join condition might not be indexed

```sql
-- Postgres: always use ANALYZE to get actual execution times
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...

-- Look at "actual time" not "estimated cost"
-- Buffers tells you how much I/O happened
```

### Index Strategy

**Rules of thumb:**
- Index columns used in WHERE, JOIN ON, and ORDER BY
- Composite indexes: put equality columns first, then range columns
- Don't index everything -- each index slows writes and uses disk
- Partial indexes for common filters: `CREATE INDEX ... WHERE status = 'active'`
- Covering indexes to avoid table lookups: `INCLUDE (column)` in Postgres

```sql
-- Good composite index for: WHERE user_id = ? AND created_at > ? ORDER BY created_at
CREATE INDEX idx_user_created ON orders (user_id, created_at);

-- Partial index: only index the rows you actually query
CREATE INDEX idx_active_users ON users (email) WHERE deleted_at IS NULL;
```

### N+1 Queries: Detection and Fixes

The N+1 problem: You fetch N items, then run 1 query per item to get related data. 100 users = 101 queries instead of 2.

**Detection:**
- Enable query logging and count queries per request
- Use tools: `django-debug-toolbar`, `bullet` gem (Rails), `pg-monitor` (Node)
- APM tools (Datadog, New Relic) flag N+1 automatically

**Fixes:**

1. **Eager loading** (ORM-level):
   ```python
   # Django: select_related (FK/OneToOne), prefetch_related (M2M/reverse FK)
   User.objects.select_related('profile').prefetch_related('orders')

   # SQLAlchemy: joinedload, subqueryload
   session.query(User).options(joinedload(User.orders))
   ```
   ```javascript
   // Prisma: include
   prisma.user.findMany({ include: { orders: true } })

   // Sequelize: include with eager loading
   User.findAll({ include: [Order] })
   ```

2. **DataLoader** (GraphQL / batch pattern):
   ```javascript
   // Groups individual loads into batch queries per tick
   const userLoader = new DataLoader(ids => User.findByIds(ids));
   // 100 calls to userLoader.load(id) = 1 SQL query
   ```

3. **JOINs** (raw SQL when the ORM fights you):
   ```sql
   -- Instead of N+1, one query with JOIN
   SELECT u.*, o.* FROM users u
   LEFT JOIN orders o ON o.user_id = u.id
   WHERE u.active = true;
   ```

## Connection Pooling

Opening a database connection takes 20-50ms (TCP handshake + auth + TLS). Without pooling, every request pays that cost.

**Why pool:**
- Amortize connection setup cost across requests
- Limit max connections (Postgres defaults to 100; a busy app can exhaust this)
- Handle connection failures gracefully

**How:**
- **Node.js**: Most drivers pool by default (`pg` pool, Prisma connection pool). Configure `max` based on: `max = (cores * 2) + effective_spindle_count` (start with 10-20).
- **Python**: SQLAlchemy `pool_size` + `max_overflow`. Django `CONN_MAX_AGE`.
- **External pooler**: PgBouncer for Postgres. Sits between app and DB. Handles thousands of app connections with a small pool to Postgres. Use `transaction` mode for most apps.

**Pool sizing:**
- More connections is not better. Postgres performance degrades past ~100 active connections.
- Formula: start with `(2 * CPU cores) + number of disks`. Benchmark from there.
- If you have 10 app instances each with pool size 20, that's 200 connections. Use PgBouncer.

## Caching Patterns

### Cache-Aside (Lazy Loading)

The most common pattern. App checks cache first, falls back to DB, populates cache.

```python
def get_user(user_id):
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    user = db.query(User).get(user_id)
    redis.setex(f"user:{user_id}", 300, json.dumps(user))  # 5min TTL
    return user
```

**Pros:** Only caches what's actually read. Simple.
**Cons:** Cache miss = slower (DB query + cache write). Stale data until TTL expires.

### Write-Through

Write to cache and DB at the same time. Cache is always fresh.

```python
def update_user(user_id, data):
    db.query(User).filter_by(id=user_id).update(data)
    db.commit()
    redis.setex(f"user:{user_id}", 300, json.dumps(data))  # update cache too
```

**Pros:** Cache always current. No stale reads.
**Cons:** Every write is slower (two writes). Caches data that may never be read.

### Write-Behind (Write-Back)

Write to cache immediately, flush to DB asynchronously. High write throughput.

**Pros:** Writes are fast (cache only). Good for write-heavy workloads.
**Cons:** Data loss risk if cache fails before flush. Complex. Use only when you understand the trade-off.

### Cache Invalidation Strategies

- **TTL**: Set expiration. Simple, eventually consistent. Good default.
- **Explicit invalidation**: Delete cache key on write. More correct, more code.
- **Versioned keys**: `user:42:v3`. Bump version on write. Old keys expire naturally.
- **Pub/Sub invalidation**: Publish invalidation events. Good for multi-instance apps.

### Redis Patterns

```
# Rate limiting (sliding window)
MULTI
ZADD rate:{user_id} {timestamp} {request_id}
ZREMRANGEBYSCORE rate:{user_id} 0 {timestamp - window}
ZCARD rate:{user_id}
EXEC

# Distributed lock
SET lock:{resource} {owner} NX EX 30  # acquire
DEL lock:{resource}                    # release (check owner first)

# Leaderboard
ZADD leaderboard {score} {user_id}
ZREVRANGE leaderboard 0 9 WITHSCORES  # top 10
```

## Async Processing

Anything that takes >100ms and the user doesn't need the result immediately should go in a queue.

**What to move off the request path:**
- Sending emails / notifications
- Image/video processing
- PDF generation
- Data exports
- Webhook deliveries
- Analytics writes
- Search index updates

**Queue options:**
- **BullMQ** (Node.js + Redis): Simple, battle-tested. Good for most Node apps.
- **Celery** (Python + Redis/RabbitMQ): The standard for Python. Use with Redis broker for simplicity.
- **SQS** (AWS): Managed, scales infinitely, no infrastructure to run. Use with Lambda for serverless.
- **RabbitMQ**: When you need routing, priorities, or complex messaging patterns.

**Pattern:**
```javascript
// Instead of this (blocks the request for 2s):
app.post('/signup', async (req, res) => {
  const user = await createUser(req.body);
  await sendWelcomeEmail(user);      // 500ms
  await generateAvatar(user);         // 1s
  await syncToCRM(user);             // 500ms
  res.json(user);
});

// Do this (responds in 50ms):
app.post('/signup', async (req, res) => {
  const user = await createUser(req.body);
  await queue.add('welcome-email', { userId: user.id });
  await queue.add('generate-avatar', { userId: user.id });
  await queue.add('sync-crm', { userId: user.id });
  res.json(user);
});
```

## Memory Profiling

### Node.js

```bash
# Take a heap snapshot while running
node --inspect your-app.js
# Open Chrome DevTools → chrome://inspect → take heap snapshot

# Programmatic heap dump
npm install heapdump
kill -USR2 <pid>  # writes heapdump to disk

# Track allocations over time
node --inspect --expose-gc your-app.js
# DevTools → Memory → Allocation timeline
```

**Common Node.js memory leaks:**
- Event listeners not removed (especially on long-lived objects)
- Closures holding references to large objects
- Unbounded arrays/maps used as caches (use LRU instead)
- Global variables accumulating data
- Streams not properly destroyed on error

### Python

```python
# tracemalloc -- built-in, good for finding where memory is allocated
import tracemalloc
tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)

# memory_profiler -- line-by-line memory usage
# pip install memory-profiler
@profile
def my_function():
    big_list = [i for i in range(1_000_000)]  # shows memory jump here
```

## CPU Profiling

### Node.js

```bash
# clinic.js -- the best all-in-one diagnostic tool
npx clinic doctor -- node your-app.js
npx clinic flame -- node your-app.js   # flamegraph
npx clinic bubbleprof -- node your-app.js  # async delays

# 0x -- lightweight flamegraphs
npx 0x your-app.js
```

### Python

```bash
# cProfile -- built-in, good for finding hot functions
python -m cProfile -s cumulative your-script.py

# py-spy -- sampling profiler, attach to running process, no code changes
pip install py-spy
py-spy top --pid <pid>           # live top-like view
py-spy record -o profile.svg --pid <pid>  # flamegraph
```

## Common Node.js Performance Issues

- **Event loop blocking**: CPU-heavy work (JSON.parse on huge payloads, crypto, image processing) blocks all requests. Fix: use worker threads or move to a queue.
- **Large JSON serialization**: `JSON.stringify` on huge objects is synchronous and slow. Fix: stream responses, paginate, or use `fast-json-stringify` with a schema.
- **Synchronous file I/O**: `fs.readFileSync` in request handlers blocks the event loop. Fix: always use `fs.promises` or `fs.createReadStream`.
- **Unbounded concurrency**: `Promise.all` on 10,000 items hitting an API. Fix: use `p-limit` or `p-map` with concurrency control.
- **Not using streams**: Reading entire files/responses into memory. Fix: pipe streams (`request.pipe(transform).pipe(response)`).

## Common Python Performance Issues

- **GIL**: CPU-bound Python code only uses one core. Fix: `multiprocessing`, or use C extensions (numpy, etc.).
- **Sync in async**: Calling blocking code in an async handler blocks the entire event loop. Fix: `asyncio.to_thread()` or `run_in_executor()`.
- **ORM N+1**: Django and SQLAlchemy make N+1 easy to write. Fix: `select_related`, `prefetch_related`, eager loading.
- **Not using generators**: Loading a million rows into a list when you process them one at a time. Fix: generators, `yield`, `iter_rows()`.
- **String concatenation in loops**: Building strings with `+=` in a loop. Fix: use `''.join(list)` or `io.StringIO`.

## Horizontal vs Vertical Scaling

**Vertical (bigger machine):**
- Simpler. No distributed systems headaches.
- Works until it doesn't (there's a ceiling).
- Good for: databases (usually), small-medium apps, anything with shared state.
- Try this first. A bigger machine is cheaper than engineering time.

**Horizontal (more machines):**
- Requires stateless app design (sessions in Redis, not memory).
- Needs load balancer, health checks, deployment coordination.
- Good for: stateless APIs, worker pools, read replicas.
- Required when: single machine can't handle the load, or you need redundancy.

**Decision:** If you can solve it by upgrading your server, do that. Horizontal scaling adds operational complexity that most teams underestimate. Scale horizontally when vertical hits its ceiling or when you need high availability across failure domains.
