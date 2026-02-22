# REST API Design

## URL Structure Conventions

**Resources are nouns, always plural:**
- `/users` -- collection
- `/users/:id` -- single resource
- `/users/:id/posts` -- nested resource (user's posts)
- `/users/:id/posts/:postId/comments` -- avoid going deeper than 3 levels

**No verbs in URLs:**
- Good: `POST /users/:id/activate` (action as sub-resource)
- Bad: `/getUser`, `/createPost`, `/deleteAllComments`

**Use kebab-case for multi-word resources:**
- `/api-keys`, not `/apiKeys` or `/api_keys`
- Paths are case-sensitive; lowercase is the convention

**Query params for filtering, sorting, searching:**
- `/users?status=active&sort=-created_at&limit=20`
- Prefix with `-` for descending sort

## HTTP Methods

| Method | Purpose | Request Body | Idempotent | Safe |
|--------|---------|-------------|------------|------|
| GET | Read resource(s) | No | Yes | Yes |
| POST | Create resource / trigger action | Yes | No | No |
| PUT | Replace entire resource | Yes | Yes | No |
| PATCH | Partial update | Yes | No* | No |
| DELETE | Remove resource | No | Yes | No |

**When to use PUT vs PATCH:**
- PUT: You're sending the complete resource. Missing fields get set to defaults/null.
- PATCH: You're sending only the fields that changed. Missing fields stay as they are.
- Most apps want PATCH for updates. PUT is rarely what you actually mean.

## Status Codes That Matter

### Success
- **200 OK** -- Request succeeded, response has body (GET, PUT, PATCH)
- **201 Created** -- Resource created, include `Location` header (POST)
- **204 No Content** -- Success, no body needed (DELETE, some PUT/PATCH)

### Client Errors
- **400 Bad Request** -- Malformed syntax, missing required field
- **401 Unauthorized** -- Not authenticated (no/bad credentials)
- **403 Forbidden** -- Authenticated but not authorized (you know who they are, they can't do this)
- **404 Not Found** -- Resource doesn't exist (also use for "exists but you can't see it" to avoid leaking info)
- **409 Conflict** -- Resource state conflict (duplicate email, version mismatch)
- **422 Unprocessable Entity** -- Valid syntax but semantically wrong (email format invalid, age is negative)
- **429 Too Many Requests** -- Rate limited, include `Retry-After` header

### Server Errors
- **500 Internal Server Error** -- Something broke, log it, alert on it

**Avoid:** 200 for everything, custom status codes, using 400 when you mean 422, using 401 when you mean 403.

## Pagination

### Cursor-Based (Preferred)

Best for large/dynamic datasets. Stable across inserts/deletes.

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```

Client requests: `GET /posts?cursor=eyJpZCI6MTAwfQ==&limit=20`

The cursor is an opaque token (usually base64-encoded ID or timestamp). Clients don't parse it; they just pass it back.

### Offset-Based (Simpler)

Fine for small, static datasets. Breaks if data shifts between pages.

```json
{
  "data": [...],
  "pagination": {
    "total": 342,
    "page": 2,
    "per_page": 20
  }
}
```

Client requests: `GET /posts?page=2&per_page=20`

### Keyset

Like cursor-based but the client knows the sort key:

`GET /posts?created_after=2024-01-15T00:00:00Z&limit=20`

Good when the sort field is meaningful to the client (timestamps, alphabetical).

**Rule of thumb:** Use cursor-based unless you have a reason not to. Offset pagination is a trap at scale.

## Filtering and Sorting

**Simple filters as query params:**
```
GET /posts?status=published&author_id=42
GET /users?role=admin&created_after=2024-01-01
```

**Sorting:**
```
GET /posts?sort=created_at       # ascending
GET /posts?sort=-created_at      # descending (prefix with -)
GET /posts?sort=-created_at,title # multi-field sort
```

**Complex filtering:** If you need operators (greater than, contains, in), pick a convention and document it:
```
GET /products?price[gte]=10&price[lte]=100
GET /products?price_gte=10&price_lte=100
```

Don't invent a query language. If you need that much flexibility, you probably want GraphQL or a dedicated search endpoint.

## HATEOAS

Hypermedia as the Engine of Application State. The idea: responses include links to related actions/resources.

```json
{
  "id": 42,
  "name": "Alice",
  "_links": {
    "self": "/users/42",
    "posts": "/users/42/posts",
    "deactivate": "/users/42/deactivate"
  }
}
```

**In theory:** Clients discover the API by following links, no hardcoded URLs.
**In practice:** Almost nobody does this well, and clients hardcode paths anyway.

**Verdict:** Nice for truly public APIs with many third-party consumers. Not worth the effort for internal APIs or apps where you control both client and server.

## Versioning

### URL Path (Recommended)

```
/v1/users
/v2/users
```

Simple, explicit, easy to route, easy to deprecate. You can see the version in logs and docs. This is what most major APIs use (Stripe, GitHub, Twilio).

### Header-Based

```
Accept: application/vnd.myapi.v2+json
```

Cleaner URLs but harder to test (can't just paste a URL in a browser), harder to route, easy to forget.

**Verdict:** Use URL path versioning. It's simpler, more explicit, and debuggable. Save clever for your product, not your versioning strategy.

**When to version:** When you make a breaking change. Adding fields is not breaking. Removing fields, renaming fields, or changing types is breaking.

## Idempotency

An operation is idempotent if doing it twice has the same effect as doing it once.

- **GET, PUT, DELETE**: Should always be idempotent by nature
- **POST**: Not idempotent by default (creating twice = two resources)

**Idempotency keys for POST:**

Have clients send a unique key with each request. If you've seen that key before, return the original response instead of creating a duplicate.

```
POST /payments
Idempotency-Key: 8a3b1c2d-...
```

Server: store the key + response, check before processing. Essential for payment APIs and anything where double-execution is dangerous.

## Request/Response Patterns

### Envelope (Consistent Wrapper)

```json
{
  "data": { ... },
  "meta": { "request_id": "abc123" }
}
```

Pros: Consistent structure, room for metadata.
Cons: Extra nesting, more bytes.

### Flat (Direct Response)

```json
{
  "id": 42,
  "name": "Alice",
  "email": "alice@example.com"
}
```

Pros: Simpler, less nesting.
Cons: Harder to add metadata later without breaking changes.

**Recommendation:** Use an envelope for list endpoints (you need pagination metadata anyway). For single resources, either works -- just be consistent.

## OpenAPI / Swagger

**Generate the spec from your code, not the other way around.** Writing OpenAPI YAML by hand is tedious and falls out of sync immediately.

Good tools:
- **Node.js**: `tsoa` (generates routes + OpenAPI from TypeScript), `fastify-swagger` (generates from Fastify schemas)
- **Python**: FastAPI generates OpenAPI automatically
- **Go**: `swag` generates from comments

Use the generated spec for:
- Auto-generated documentation (Redoc, Scalar, Swagger UI)
- Client SDK generation (openapi-generator, but review the output)
- Contract testing

Don't use OpenAPI as a design tool unless you're designing a large public API with a dedicated team. For most projects, write the code and let the spec follow.
