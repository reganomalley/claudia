# Time-Series and Graph Databases

## Time-Series Databases

### When You Need One

You have data that:
- Is append-mostly (rarely update old records)
- Has a timestamp as the primary query dimension
- Needs aggregation over time windows (avg per hour, max per day)
- Arrives at high volume (metrics, IoT, financial ticks, logs)

### Options

| Database | Best For | Notes |
|----------|----------|-------|
| TimescaleDB | Postgres users, moderate scale | Postgres extension, full SQL, familiar tooling |
| InfluxDB | Metrics and monitoring | Purpose-built, Flux query language, good ecosystem |
| QuestDB | High-ingest performance | SQL interface, very fast writes, newer |
| ClickHouse | Analytics on time-series | Column-oriented, great for aggregations at scale |
| Prometheus | Infrastructure monitoring | Pull-based, pairs with Grafana, not a general DB |

### Decision Framework

```
What's the use case?
├── App metrics / monitoring
│   ├── Infrastructure → Prometheus + Grafana
│   └── Application metrics → InfluxDB or TimescaleDB
├── IoT sensor data
│   ├── <100K devices → TimescaleDB
│   └── >100K devices → QuestDB or InfluxDB
├── Financial data
│   ├── Tick data at high volume → QuestDB
│   └── Analytics/reporting → ClickHouse
└── Already using Postgres
    └── TimescaleDB (it's just an extension)
```

### TimescaleDB Quick Start

```sql
-- It's just Postgres with an extension
CREATE EXTENSION timescaledb;

-- Create a regular table
CREATE TABLE metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id TEXT,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION
);

-- Convert to hypertable (this is where the magic happens)
SELECT create_hypertable('metrics', 'time');

-- Query with time buckets
SELECT time_bucket('1 hour', time) AS hour,
       device_id,
       AVG(temperature) as avg_temp
FROM metrics
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY hour, device_id
ORDER BY hour DESC;
```

### Key Concepts

- **Retention policies**: Auto-delete old data (e.g., keep 90 days of raw, 2 years of hourly aggregates)
- **Continuous aggregates**: Pre-compute rollups for fast dashboards
- **Compression**: Time-series data compresses extremely well (10-20x typical)
- **Downsampling**: Store high-resolution recent data, lower-resolution historical

---

## Graph Databases

### When You Need One

Your queries primarily ask about **relationships between entities**:
- "Find all friends of friends who like jazz"
- "What's the shortest path between A and B?"
- "Which users are in the same community cluster?"
- "Show all dependencies of this package (transitive)"

### The Postgres-First Test

Before reaching for a graph database, try PostgreSQL:

```sql
-- Recursive CTE for graph traversal (up to ~3 hops)
WITH RECURSIVE friends AS (
  SELECT friend_id, 1 AS depth
  FROM friendships WHERE user_id = 'alice'
  UNION
  SELECT f.friend_id, fr.depth + 1
  FROM friendships f
  JOIN friends fr ON f.user_id = fr.friend_id
  WHERE fr.depth < 3
)
SELECT DISTINCT friend_id FROM friends;
```

**If this is fast enough, you don't need a graph database.**

### When Postgres Isn't Enough

- Traversals >3 hops deep
- Complex path-finding algorithms (shortest path, PageRank, community detection)
- Graph pattern matching (find all triangles, find cycles)
- >10M edges with deep traversals

### Options

| Database | Best For | Query Language |
|----------|----------|---------------|
| Neo4j | General graph, most mature | Cypher |
| Amazon Neptune | AWS-native, managed | Gremlin or SPARQL |
| ArangoDB | Multi-model (graph + document) | AQL |
| Dgraph | Distributed graph | GraphQL-like (DQL) |

### Neo4j Quick Example

```cypher
// Find friends of friends who like jazz, excluding direct friends
MATCH (me:Person {name: 'Alice'})-[:KNOWS]->(:Person)-[:KNOWS]->(fof:Person)
WHERE NOT (me)-[:KNOWS]->(fof)
  AND (fof)-[:LIKES]->(:Genre {name: 'Jazz'})
RETURN DISTINCT fof.name
```

### Common Mistake

**Don't use a graph database just because your data has relationships.** All relational databases handle relationships -- that's what "relational" means. Graph databases are for when the *query patterns* are graph-shaped (variable-depth traversals, path-finding, pattern matching).

| Data Pattern | Use |
|-------------|-----|
| Users have orders, orders have items | Relational (PostgreSQL) |
| Users follow users, find mutual connections | Could be either -- try SQL first |
| Find all paths between two nodes in a network | Graph (Neo4j) |
| Social network analysis, community detection | Graph (Neo4j) |
| Dependency trees with >3 levels | Graph (Neo4j) |
