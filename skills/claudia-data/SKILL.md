---
description: >
  Data modeling knowledge domain for Claudia. Use this skill when the user asks about schema design,
  database migrations, indexing strategy, normalization, data relationships, ETL, data pipelines,
  or data architecture. Triggers on phrases like "schema design", "migration", "index", "normalize",
  "foreign key", "data model", "ETL", "data pipeline", "soft delete", "audit trail", "multi-tenant",
  "polymorphic", or "data architecture".
---

# Claudia Data Modeling Domain

## Overview

Good data modeling prevents most "scaling" problems before they start. Get the schema right and everything downstream gets easier -- queries are simpler, migrations are safer, performance is predictable, and your future self won't want to rewrite the whole thing.

## Schema Design Decision Tree

```
How should I model my data?
├── Start normalized (3NF)
│   ├── Relationships are clear → foreign keys + join tables
│   ├── Schema is stable → strict types + constraints
│   └── Data integrity matters → NOT NULL, CHECK, UNIQUE
├── Denormalize only for measured read performance
│   ├── Dashboard query is slow → materialized view or computed column
│   ├── N+1 joins killing latency → embed or cache the joined data
│   └── Read:write ratio > 100:1 → read replica or denormalized table
└── Consider event sourcing only for audit-heavy domains
    ├── Need full history of every change → event log + projections
    ├── Regulatory/compliance requirements → append-only audit trail
    └── Complex business rules with undo → event replay
```

## Common Patterns

| Pattern | When to Use | Example |
|---------|------------|---------|
| Soft deletes | Need to recover data, regulatory retention | `deleted_at` timestamp column, filter in queries |
| Audit trails | Compliance, debugging, blame tracking | Separate `_audit` table with old/new values + actor |
| Multi-tenancy | SaaS with isolated customer data | `tenant_id` column on every table + RLS policies |
| Polymorphic associations | Different types share a relationship | STI, CTI, or delegated types (see references) |
| EAV (avoid) | Almost never -- use JSONB instead | `entity_id, attribute, value` tables are a trap |
| JSON columns | Semi-structured data within a relational model | Preferences, metadata, form responses |
| Temporal data | Track how values change over time | `valid_from`/`valid_to` columns (SCD Type 2) |
| Junction tables | Many-to-many relationships | `post_tags` table linking `posts` and `tags` |

## Indexing Rules

```
What should I index?
├── Primary keys → automatic, don't think about it
├── Foreign keys → always, every single one
├── WHERE clause columns → measure first, but usually yes
├── Composite indexes → leftmost prefix rule (equality first, range second)
├── Partial indexes → filtered data (WHERE active = true)
├── Expression indexes → computed values (lower(email))
└── JOIN columns → if they're not already FK-indexed
```

## Migration Safety Checklist

Before running any migration in production:

- [ ] **Backwards compatible?** Old code must work with new schema during deploy
- [ ] **No long locks?** `ALTER TABLE` on large tables can lock for minutes -- use `CONCURRENTLY` or online DDL
- [ ] **Separate deploy from migrate?** Deploy code first (handles both schemas), then run migration
- [ ] **Tested on production-size data?** A migration that takes 2ms on dev can take 20min on prod
- [ ] **Rollback plan?** Know how to undo it without data loss
- [ ] **Batched if large?** Backfills should process in chunks, not one giant transaction

## Deep References

For detailed guidance on specific topics, load:
- `references/schema-patterns.md` -- Normalization, denormalization, and common schema patterns
- `references/migrations-indexing.md` -- Migration safety, indexing strategy, and EXPLAIN ANALYZE

## Response Format

When advising on data modeling:
1. **Recommendation** (specific pattern or schema approach)
2. **Why it fits** (match to their data shape, access patterns, and scale)
3. **Schema sketch** (actual column names and types when helpful)
4. **Watch out for** (common mistakes with this pattern)
