---
name: claudia-databases
description: >
  Database knowledge domain for Claudia. Use this skill when the user asks about database
  selection, SQL vs NoSQL, data modeling, vector databases, time-series databases, graph
  databases, database scaling, indexing strategies, or migration planning. Triggers on
  phrases like "which database", "should I use Postgres", "MongoDB vs", "store embeddings",
  "time-series data", "database for", "SQL or NoSQL", "data model", or "database scaling".
version: 0.1.0
---

# Claudia Database Domain

## Overview

This skill helps you choose the right database and use it well. The right answer depends on your data shape, access patterns, scale, and team -- not on what's trending on Hacker News.

## The Decision Matrix

### Start Here: What Shape Is Your Data?

```
What does your data look like?
├── Rows and columns, relationships between entities
│   └── Relational (PostgreSQL, MySQL, SQLite)
├── Nested documents, variable schema
│   └── Document (MongoDB, CouchDB)
├── Simple key → value lookups, caching
│   └── Key-Value (Redis, DynamoDB, Memcached)
├── Connections between entities matter most
│   └── Graph (Neo4j, Amazon Neptune)
├── Metrics over time, IoT, monitoring
│   └── Time-Series (TimescaleDB, InfluxDB, QuestDB)
├── AI embeddings, similarity search
│   └── Vector (pgvector, Pinecone, Qdrant, Weaviate)
├── Full-text search, faceted filtering
│   └── Search (Elasticsearch, Meilisearch, Typesense)
└── Not sure / mixed
    └── Start with PostgreSQL (it does most things well enough)
```

### The "Just Use Postgres" Rule

PostgreSQL handles 80% of use cases well. Before reaching for a specialized database, ask:
- Can Postgres do this with an extension? (pgvector, TimescaleDB, PostGIS, pg_trgm)
- Is the specialized need actually my bottleneck, or am I optimizing prematurely?
- Can my team operate another database in production?

**Use a specialized DB when:** Postgres can technically do it, but you're hitting real performance limits at your actual scale, or the specialized DB's API dramatically simplifies your code.

## Quick Comparisons

| Need | First Choice | When to Upgrade |
|------|-------------|----------------|
| General web app | PostgreSQL | You probably don't need to |
| Caching / sessions | Redis | When you need persistence → Redis with AOF |
| Document store | MongoDB | When you need transactions → Postgres JSONB |
| Embeddings / RAG | pgvector | >10M vectors or <10ms latency → Pinecone/Qdrant |
| Time-series | TimescaleDB (Postgres ext) | >1M inserts/sec → QuestDB or InfluxDB |
| Graph queries | PostgreSQL recursive CTEs | >3 hops or complex traversals → Neo4j |
| Full-text search | PostgreSQL ts_vector | Complex facets or relevance tuning → Elasticsearch |
| Prototype / local | SQLite | Going to production with concurrent writes |

## Deep References

For detailed guidance on specific topics, load:
- `references/sql-vs-nosql.md` -- When each paradigm wins
- `references/vector-databases.md` -- Embeddings, RAG, similarity search
- `references/time-series-graph.md` -- Time-series and graph database specifics

## Response Format

When advising on databases:
1. **Recommendation** (specific database name)
2. **Why it fits** (match to their data shape and access patterns)
3. **What you're trading off** (what this choice is worse at)
4. **Migration path** (how to move if you outgrow it)
