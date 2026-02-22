# Schema Patterns

## Normalization

Normalization removes redundancy and protects data integrity. For most applications, 3NF is the right target. Going beyond 3NF adds complexity without meaningful benefit.

### 1NF (First Normal Form)

- Every column holds a single value (no arrays, no comma-separated lists)
- Every row is unique (has a primary key)

**Before (violates 1NF):**
```
| user_id | name  | phone_numbers        |
|---------|-------|----------------------|
| 1       | Alice | 555-0100, 555-0101   |
```

**After (1NF):**
```
| user_id | name  |       | user_id | phone_number |
|---------|-------|       |---------|--------------|
| 1       | Alice |       | 1       | 555-0100     |
                          | 1       | 555-0101     |
```

### 2NF (Second Normal Form)

- Must be in 1NF
- Every non-key column depends on the entire primary key (no partial dependencies)

**Before (violates 2NF, composite key `order_id + product_id`):**
```
| order_id | product_id | product_name | quantity |
```
`product_name` depends only on `product_id`, not the full key.

**After (2NF):** Split into `orders_products (order_id, product_id, quantity)` and `products (product_id, product_name)`.

### 3NF (Third Normal Form)

- Must be in 2NF
- No transitive dependencies (non-key columns don't depend on other non-key columns)

**Before (violates 3NF):**
```
| employee_id | department_id | department_name |
```
`department_name` depends on `department_id`, not on `employee_id`.

**After (3NF):** Split into `employees (employee_id, department_id)` and `departments (department_id, department_name)`.

### When to Stop

3NF is almost always enough. BCNF, 4NF, 5NF exist but the scenarios where they matter are rare and the schemas they produce are harder to work with. If someone tells you to go beyond 3NF, ask them to show you the actual anomaly they're preventing.

## Denormalization

Denormalization trades write complexity for read performance. Only do it when you have measured evidence that normalization is your bottleneck.

### Computed Columns

Store a derived value alongside the source data. Good for values that are expensive to compute and read frequently.

```sql
-- Instead of calculating on every read:
ALTER TABLE orders ADD COLUMN total_amount DECIMAL(10,2);
-- Update via trigger or application code on insert/update of order_items
```

### Materialized Views

Pre-computed query results that you refresh on a schedule. Good for dashboards and reports.

```sql
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT date_trunc('month', created_at) AS month, SUM(total_amount) AS revenue
FROM orders GROUP BY 1;

-- Refresh periodically (not on every write)
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_revenue;
```

### Read Replicas

Send read queries to replicas, writes to primary. Good when read volume dwarfs write volume. Introduces replication lag -- your code must tolerate slightly stale reads.

## Common Schema Patterns

### Users + Profiles (1:1 Split)

Separate frequently-accessed auth data from rarely-accessed profile data.

```sql
-- Hot table: queried on every request
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Cold table: queried on profile views
CREATE TABLE profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    display_name TEXT,
    bio TEXT,
    avatar_url TEXT,
    settings JSONB DEFAULT '{}'
);
```

**Why split:** Different access patterns. `users` is read on every authenticated request. `profiles` is read only when someone views a profile. Keeps the hot table small and fast.

### Tags / Categories (Many-to-Many)

Always use a junction table. Never comma-separated strings.

```sql
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Index both directions
CREATE INDEX idx_post_tags_tag ON post_tags(tag_id);
```

### Hierarchical Data

```
Which approach for tree-structured data?
├── Adjacency list (parent_id)
│   ├── Simple to implement
│   ├── Easy inserts and moves
│   ├── Recursive CTEs for tree queries (Postgres handles this well)
│   └── Best for: most cases, shallow trees, frequent writes
├── Materialized path ("/1/4/7/")
│   ├── Fast subtree queries (WHERE path LIKE '/1/4/%')
│   ├── Moves require updating all descendants
│   └── Best for: read-heavy, display breadcrumbs, infrequent moves
├── Nested set (lft/rgt numbers)
│   ├── Fast subtree and ancestor queries
│   ├── Inserts/moves are expensive (renumber everything)
│   └── Best for: read-heavy, rarely modified trees (e.g., category taxonomies)
└── Closure table (ancestor_id, descendant_id, depth)
    ├── Fast queries in all directions
    ├── Easy inserts (just add closure rows)
    ├── Uses more space (O(n^2) worst case)
    └── Best for: complex queries, moderate write frequency
```

**Default recommendation:** Start with adjacency list + recursive CTEs. Move to materialized path or closure table only if you measure query performance problems on deep trees.

### Multi-Tenancy

```
How isolated do tenants need to be?
├── Shared DB + tenant_id column (most common)
│   ├── Add tenant_id to every table
│   ├── Use Row Level Security (RLS) in Postgres
│   ├── Include tenant_id in every query and every index
│   ├── Simplest to operate, lowest cost
│   └── Risk: query without tenant_id filter = data leak
├── Separate schemas (one schema per tenant)
│   ├── Better isolation, same database
│   ├── Migrations run per-schema (slower as tenants grow)
│   └── Good for: moderate tenant count (<1000) with isolation needs
└── Separate databases (one DB per tenant)
    ├── Strongest isolation
    ├── Most expensive to operate
    ├── Connection management gets complex
    └── Good for: enterprise customers who require it contractually
```

### Soft Deletes

```sql
ALTER TABLE posts ADD COLUMN deleted_at TIMESTAMPTZ;

-- Partial index: only index non-deleted rows (what most queries want)
CREATE INDEX idx_posts_active ON posts(created_at) WHERE deleted_at IS NULL;
```

**Watch out for:**
- Every query now needs `WHERE deleted_at IS NULL` -- easy to forget
- Unique constraints must account for soft-deleted rows
- Foreign keys to soft-deleted rows create orphans
- Consider a view: `CREATE VIEW active_posts AS SELECT * FROM posts WHERE deleted_at IS NULL`

### Audit Trails

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    actor_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Implementation options:**
- **Application-level:** More control, can capture business context (why the change was made). Requires discipline to log everywhere.
- **Database triggers:** Never misses a change, but can't capture application context (who requested it via API). Can slow writes.
- **Change Data Capture (CDC):** Stream changes from the WAL (Debezium). Best for event-driven architectures.

**Recommendation:** Application-level for most apps. Triggers if you don't trust application code to be consistent. CDC if you need to feed changes to other systems.

### Polymorphic Associations

When different types of records need to share a relationship (e.g., comments on posts, images, and videos).

**Single Table Inheritance (STI):**
```sql
-- One table, type column, nullable columns for type-specific data
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('post', 'image', 'video')),
    title TEXT,
    body TEXT,         -- posts only
    url TEXT,          -- images and videos
    duration INTEGER   -- videos only
);
```
Good for: few types, similar fields. Bad for: many types, lots of nulls.

**Class Table Inheritance (CTI):**
```sql
-- Base table + type-specific tables
CREATE TABLE content (id SERIAL PRIMARY KEY, type TEXT NOT NULL, title TEXT);
CREATE TABLE posts (id INTEGER PRIMARY KEY REFERENCES content(id), body TEXT);
CREATE TABLE videos (id INTEGER PRIMARY KEY REFERENCES content(id), url TEXT, duration INTEGER);
```
Good for: many type-specific fields, clean schema. Bad for: queries across types require JOINs.

**Delegated Types (Rails-style):**
```sql
-- Commentable pattern
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    commentable_type TEXT NOT NULL,
    commentable_id INTEGER NOT NULL,
    body TEXT NOT NULL
);
CREATE INDEX idx_comments_target ON comments(commentable_type, commentable_id);
```
Good for: quick to implement. Bad for: no foreign key enforcement (the DB can't validate the target exists).

### Temporal Data (SCD Type 2)

Track how records change over time with validity periods.

```sql
CREATE TABLE product_prices (
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(10,2) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to TIMESTAMPTZ, -- NULL = current
    PRIMARY KEY (product_id, valid_from)
);

-- Current price
SELECT price FROM product_prices
WHERE product_id = 1 AND valid_to IS NULL;

-- Price at a specific date
SELECT price FROM product_prices
WHERE product_id = 1 AND valid_from <= '2025-06-01' AND (valid_to IS NULL OR valid_to > '2025-06-01');
```

## Anti-Patterns

### EAV Tables (Entity-Attribute-Value)

```sql
-- DON'T do this
CREATE TABLE attributes (
    entity_id INTEGER,
    attribute_name TEXT,
    attribute_value TEXT  -- everything is a string, typing is gone
);
```

**Why it's bad:** No type safety, impossible to enforce constraints, queries become nightmares of self-joins, indexes are useless, and every ORM will hate you.

**What to do instead:** Use JSONB columns for semi-structured data. You get indexing (GIN), type checking (JSON schema or application-level), and queries that don't make you want to quit.

### God Tables (>30 columns)

A single table with 40+ columns is a sign that you're storing multiple concerns together. Split by access pattern or domain concept. If `users` has columns for auth, profile, billing, preferences, and notification settings, those are at least 3-4 separate tables.

### Nullable Foreign Keys

```sql
-- Suspicious
CREATE TABLE posts (
    author_id INTEGER REFERENCES users(id),  -- can be NULL?
    editor_id INTEGER REFERENCES users(id),  -- can be NULL?
    reviewer_id INTEGER REFERENCES users(id) -- can be NULL?
);
```

A nullable FK often means you're modeling an optional relationship that should be a separate table, or you have a polymorphic relationship that needs a different pattern.
