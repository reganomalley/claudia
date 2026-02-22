# SQL vs NoSQL: When Each Paradigm Wins

## SQL (Relational) Wins When

- **Data has clear relationships**: Users have orders, orders have items, items have categories
- **You need transactions**: Money, inventory, anything where partial updates are dangerous
- **You need complex queries**: JOINs, aggregations, window functions, subqueries
- **Schema is mostly stable**: You know your data shape and it won't change weekly
- **Data integrity matters**: Foreign keys, constraints, unique indexes enforce correctness
- **You need ad-hoc queries**: Business analysts will query this data in ways you can't predict

**Best choices:** PostgreSQL (general), MySQL (WordPress/legacy), SQLite (local/embedded)

### PostgreSQL Specifically

Postgres deserves special mention because it blurs the SQL/NoSQL line:
- `JSONB` columns give you document-store flexibility within a relational model
- `ARRAY` types for simple lists without a join table
- Full-text search with `tsvector` + `tsquery`
- Extensions: PostGIS (geo), pgvector (embeddings), TimescaleDB (time-series)
- Excellent at concurrent reads AND writes

## NoSQL Wins When

### Document Databases (MongoDB, CouchDB)

**Use when:**
- Schema varies significantly between records (e.g., product catalogs with different attributes)
- Data is naturally nested and read as a whole (e.g., user profiles with embedded preferences)
- Rapid iteration on schema during early development
- You need horizontal scaling with automatic sharding

**Don't use when:**
- You need transactions across multiple documents (MongoDB has them now but they're a bolt-on)
- You need JOINs (lookups exist but are slower than SQL JOINs)
- Your data is fundamentally relational

### Key-Value Stores (Redis, DynamoDB)

**Use when:**
- Access pattern is simple: get by key, set by key
- You need sub-millisecond latency (caching, sessions, rate limiting)
- High throughput reads/writes at predictable latency (DynamoDB)
- You can model your access patterns upfront (DynamoDB requires this)

**Don't use when:**
- You need to query by anything other than the key (or limited secondary indexes)
- You need complex filtering, sorting, or aggregation
- Your access patterns are unpredictable

### Wide-Column (Cassandra, ScyllaDB)

**Use when:**
- Write-heavy workloads at massive scale (>100K writes/sec)
- Multi-region deployment with eventual consistency acceptable
- Time-series-like data with known query patterns
- High availability is more important than consistency

**Don't use when:**
- You need strong consistency
- Your data model changes frequently
- You're not at massive scale (operational overhead isn't worth it)

## The Hybrid Approach

Most real systems use multiple databases:
- **Postgres** as the source of truth for business data
- **Redis** for caching and sessions
- **Elasticsearch** for search (synced from Postgres via CDC or scheduled jobs)
- **S3** for files and blobs (never store files in your database)

This is fine and normal. The key is having a clear "source of truth" and understanding the consistency implications of syncing between systems.
