---
name: claudia-api
description: >
  API design knowledge domain for Claudia. Use this skill when the user asks about API architecture,
  REST vs GraphQL, tRPC, gRPC, API versioning, pagination, rate limiting, error handling, webhook
  design, or API security. Triggers on phrases like "REST or GraphQL", "API design", "tRPC vs",
  "gRPC", "API versioning", "paginate", "rate limit", "webhook", "API error", "endpoint design",
  "OpenAPI", or "API gateway".
version: 0.1.0
---

# Claudia API Design Domain

## Overview

Most APIs should be REST. GraphQL and gRPC solve specific problems -- if you don't have those problems, the added complexity isn't worth it. tRPC is a shortcut for TypeScript fullstack apps, not an architecture for the ages.

Pick the simplest style that fits your actual constraints. You can always add complexity later; removing it is much harder.

## API Style Decision Tree

```
What are you building?
├── Internal service-to-service communication
│   ├── High throughput / streaming needed → gRPC
│   └── Simple request/response → REST (internal) or gRPC
├── TypeScript fullstack (Next.js, Remix, shared codebase)
│   └── tRPC (outgrow it when you need non-TS clients)
├── Mobile app with varied data needs
│   ├── Many different screens, each needing different data shapes → GraphQL
│   └── Straightforward CRUD → REST
├── Public API for third parties
│   └── REST (it's what everyone expects)
├── Browser SPA + backend
│   ├── Shared TypeScript → tRPC
│   └── Otherwise → REST
└── Not sure
    └── REST (you can always add GraphQL later)
```

## Quick Comparison

| | REST | GraphQL | gRPC | tRPC |
|---|------|---------|------|------|
| **Strengths** | Universal, cacheable, simple tooling | Flexible queries, one endpoint, typed schema | Fast (protobuf), streaming, polyglot | Zero boilerplate, end-to-end type safety |
| **Weaknesses** | Over/under-fetching, many endpoints | Caching is hard, N+1 queries, complexity | No browser support (needs proxy), steep learning curve | TypeScript only, tight client-server coupling |
| **Best for** | Public APIs, most web apps, CRUD | Mobile apps, complex nested data, varied clients | Microservices, high throughput, streaming | TS fullstack apps, prototypes, internal tools |
| **Avoid when** | You need real-time streaming | Small teams, simple CRUD, caching matters | Browser-facing APIs, small projects | Non-TS clients exist or will exist |

## REST Design Principles (The Short Version)

- **Nouns, not verbs**: `/users/:id/posts`, not `/getUserPosts`
- **Plural resources**: `/users`, not `/user`
- **HTTP methods do the verb work**: GET reads, POST creates, PUT replaces, PATCH updates, DELETE removes
- **Status codes mean things**: Don't return 200 with `{ "error": true }` -- use proper HTTP status codes
- **Consistent naming**: Pick `snake_case` or `camelCase` and stick with it everywhere

## Error Handling Pattern

Every API should return structured errors. Don't make clients parse error messages.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email address is invalid",
    "details": [
      {
        "field": "email",
        "issue": "Must be a valid email address"
      }
    ]
  }
}
```

Rules:
- Machine-readable `code` (for programmatic handling)
- Human-readable `message` (for logging/debugging)
- Optional `details` array (for field-level validation errors)
- Same structure for every error, every endpoint

## Deep References

For detailed guidance on specific topics, load:
- `references/rest-design.md` -- URL conventions, status codes, pagination, versioning, idempotency
- `references/graphql-grpc-trpc.md` -- When each alternative wins, gotchas, tooling
- `references/api-patterns.md` -- Auth, rate limiting, webhooks, real-time, caching, file uploads

## Response Format

When advising on API design:
1. **Recommendation** (specific style and pattern)
2. **Why it fits** (match to their constraints, team, and clients)
3. **Patterns to follow** (concrete conventions and examples)
4. **Common mistakes to avoid** (what goes wrong with this choice)
