# Migrations and Indexing

## Migration Safety

Migrations in production are not the same as migrations in development. A statement that takes 2ms on your laptop can lock a table for 20 minutes on a database with 50 million rows.

### Column Operations

**Adding a column:**
- Nullable column with no default: instant in Postgres (no table rewrite)
- Column with a default: instant in Postgres 11+ (stores default in catalog, not on disk). Older versions or MySQL < 8.0.12 rewrite the entire table.
- NOT NULL without default: requires backfilling first

**Safe process for adding a NOT NULL column:**
1. Add column as nullable: `ALTER TABLE users ADD COLUMN status TEXT;`
2. Backfill in batches: `UPDATE users SET status = 'active' WHERE status IS NULL AND id BETWEEN ? AND ?`
3. Add NOT NULL constraint: `ALTER TABLE users ALTER COLUMN status SET NOT NULL;`
4. Add default for future rows: `ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active';`

**Renaming a column (multi-step, never do it in one shot):**
1. Add new column
2. Backfill new column from old column
3. Update application code to write to both columns
4. Deploy. Verify.
5. Update application code to read from new column only
6. Deploy. Verify.
7. Stop writing to old column
8. Drop old column

This feels tedious. It is. But it prevents downtime.

**Dropping a column:**
1. Remove all references from application code
2. Deploy. Verify nothing reads or writes the column.
3. Drop the column: `ALTER TABLE users DROP COLUMN old_field;`

Never drop first. Dead code is better than broken production.

### Index Operations

**Adding an index:**
```sql
-- Postgres: use CONCURRENTLY to avoid locking the table
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- MySQL 5.6+: online DDL (default for most index operations)
ALTER TABLE users ADD INDEX idx_email (email), ALGORITHM=INPLACE, LOCK=NONE;
```

**Dropping an index:**
```sql
-- Postgres: also supports CONCURRENTLY
DROP INDEX CONCURRENTLY idx_old_index;
```

Always add indexes concurrently in production. A regular `CREATE INDEX` takes a write lock on the table for the entire duration.

### Large Data Migrations

For backfilling or transforming large amounts of data:

- **Batch it:** Process 1,000-10,000 rows at a time with a small sleep between batches
- **Track progress:** Log which batch you're on so you can resume if interrupted
- **Run off-peak:** Schedule for low-traffic hours
- **Monitor:** Watch replication lag, lock waits, and query latency during the migration
- **Use transactions per batch, not one giant transaction:** One transaction for 50M rows will blow up your WAL and replication

```python
# Example: batched backfill pattern
batch_size = 5000
last_id = 0

while True:
    rows = db.execute("""
        UPDATE users SET status = 'active'
        WHERE status IS NULL AND id > %s AND id <= %s
        RETURNING id
    """, [last_id, last_id + batch_size])

    if not rows:
        break

    last_id += batch_size
    time.sleep(0.1)  # let replicas catch up
```

### Migration Tools

Pick one and stick with it. Mixing migration tools in the same project leads to drift and confusion.

| Tool | Language/Framework | Notes |
|------|-------------------|-------|
| Prisma Migrate | Node.js / TypeScript | Schema-first, generates SQL. Good DX, opinionated. |
| Knex | Node.js | Query builder with migration support. Manual SQL, flexible. |
| Alembic | Python / SQLAlchemy | Auto-generates diffs from models. Powerful, mature. |
| Flyway | Java / JVM (any via SQL) | SQL-based, versioned files. Enterprise-friendly. |
| golang-migrate | Go | SQL files, simple, no ORM dependency. |
| Django migrations | Python / Django | Auto-generated from models. Built-in, works well. |
| Rails migrations | Ruby / Rails | DSL for schema changes. Convention-heavy, productive. |

**Key principles regardless of tool:**
- Migrations are immutable once deployed -- never edit a migration that has run in production
- Every migration should be idempotent when possible (use `IF NOT EXISTS`, `IF EXISTS`)
- Test migrations against production-sized data before deploying

## Indexing Strategy

### Index Types

**B-tree (default):**
- Handles `=`, `<`, `>`, `<=`, `>=`, `BETWEEN`, `IN`, `IS NULL`, `LIKE 'prefix%'`
- Default for `CREATE INDEX`. Use for almost everything.
- Does NOT help with `LIKE '%substring%'` (use GIN trigram for that)

**GIN (Generalized Inverted Index):**
- Best for: JSONB containment (`@>`), array containment (`@>`), full-text search (`@@`)
- Slower to build and update than B-tree, but much faster for these specific operations
```sql
CREATE INDEX idx_users_settings ON users USING GIN (settings);
-- Now fast: SELECT * FROM users WHERE settings @> '{"theme": "dark"}';
```

**GiST (Generalized Search Tree):**
- Best for: geometric data (PostGIS), range types, nearest-neighbor queries
- More flexible than B-tree for complex data types
```sql
CREATE INDEX idx_locations_point ON locations USING GIST (coordinates);
```

**BRIN (Block Range Index):**
- Best for: naturally ordered data (time-series, sequential IDs, append-only tables)
- Tiny index size (stores min/max per block range, not per row)
- Much less effective if data is not physically ordered on disk
```sql
CREATE INDEX idx_events_created ON events USING BRIN (created_at);
```

### Composite Indexes

Column order matters. The index `(a, b, c)` can be used for queries on:
- `a` alone
- `a AND b`
- `a AND b AND c`

It cannot be used for queries on `b` alone or `c` alone (leftmost prefix rule).

**Rule of thumb:** Equality conditions first, then range conditions.

```sql
-- Query: WHERE status = 'active' AND created_at > '2025-01-01'
-- Good: equality column first
CREATE INDEX idx_posts_status_created ON posts(status, created_at);

-- Bad: range column first (can't efficiently filter by status after range scan)
CREATE INDEX idx_posts_created_status ON posts(created_at, status);
```

### Partial Indexes

Index only the rows that matter. Dramatically smaller and faster when most queries filter by the same condition.

```sql
-- If 95% of queries only want active users:
CREATE INDEX idx_users_active_email ON users(email) WHERE active = true;

-- If you soft-delete and almost always query non-deleted:
CREATE INDEX idx_posts_not_deleted ON posts(created_at) WHERE deleted_at IS NULL;
```

### Expression Indexes

Index a computed value when you always query by the computed form.

```sql
-- Case-insensitive email lookup:
CREATE INDEX idx_users_email_lower ON users(lower(email));
-- Query must match: WHERE lower(email) = 'alice@example.com'

-- Extract from JSONB:
CREATE INDEX idx_users_plan ON users((settings->>'plan'));
```

### When NOT to Index

- **Small tables (<10,000 rows):** Seq scan is faster than index lookup. The optimizer knows this.
- **Write-heavy, rarely read:** Every index slows down INSERT/UPDATE/DELETE. If the table is a write buffer that gets batch-processed, skip indexes.
- **Low-cardinality columns (usually):** A boolean `active` column with 50/50 distribution won't benefit from a B-tree index. But a partial index on the rare value (`WHERE active = false`) might.
- **Columns you never filter, sort, or join on:** Indexes that don't serve queries are dead weight.

## Reading EXPLAIN ANALYZE

When a query is slow, `EXPLAIN ANALYZE` tells you why. Here's what to look for:

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42 AND status = 'pending';
```

**Key patterns:**

| What You See | What It Means | Likely Fix |
|-------------|---------------|-----------|
| Seq Scan | Full table scan, no index used | Add an index on the filter columns |
| Nested Loop with inner Seq Scan | N+1 pattern: scanning a table once per outer row | Add index on the join/filter column of the inner table |
| Sort (external merge) | Sorting on disk, not enough work_mem | Add index matching ORDER BY, or increase work_mem |
| Hash Join (large) | Joining large tables by hashing | Usually fine, but check if filtering earlier would reduce the set |
| Bitmap Heap Scan | Index found many rows, rechecking in heap | Normal for queries matching many rows. Consider if the query is too broad. |
| actual rows=100000 vs rows=100 (estimate) | Bad statistics, optimizer making poor choices | Run ANALYZE on the table, check if stats target needs increasing |

**The most important number:** `actual time` on the outermost node. That's your total query execution time. Work inward to find which node is consuming the most time.

## Connection Management

### Connection Pooling

Every database connection uses memory (Postgres: ~10MB per connection). Without pooling, 100 app servers each opening 10 connections = 1,000 connections = 10GB just for connections.

**pgBouncer** (Postgres):
- Sits between your app and Postgres
- Transaction pooling mode: connection is returned to pool after each transaction
- Session pooling mode: connection held for the session (needed for prepared statements)
- Typical config: pool_size = 20-50 per pgBouncer, max_client_conn = much higher

**Application-level pooling:**
- Most ORMs and drivers have built-in pools (Prisma, SQLAlchemy, HikariCP)
- Set `max_connections` to match your DB's capacity / number of app instances
- Set `idle_timeout` to reclaim unused connections (30-60 seconds)

### Timeouts

```sql
-- Statement timeout: kill queries that run too long
SET statement_timeout = '30s';

-- Idle in transaction timeout: kill abandoned transactions
SET idle_in_transaction_session_timeout = '60s';
```

Set these at the connection pool level, not per query. A missing timeout is how one bad query takes down your entire database.
