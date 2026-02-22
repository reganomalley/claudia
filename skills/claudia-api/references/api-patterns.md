# API Patterns

## Authentication for APIs

### API Keys

**Best for:** Server-to-server, internal services, simple third-party access.

How: Client sends key in header (`Authorization: Bearer sk_live_...` or `X-API-Key: ...`). Server looks up key, gets associated account.

Rules:
- Prefix keys to indicate type: `sk_live_`, `sk_test_`, `pk_` (publishable)
- Store hashed (SHA-256 is fine here -- not passwords, no need for bcrypt)
- Support key rotation: allow multiple active keys per account
- Log key prefix for debugging, never log the full key

### OAuth 2.0

**Best for:** Delegated access ("let this app read my data"), user-facing APIs, third-party integrations.

Use **Client Credentials** flow for service-to-service (no user involved).
Use **Authorization Code + PKCE** for user-facing apps (web, mobile, SPA).

Don't implement OAuth yourself. Use a provider (Auth0, Clerk, AWS Cognito) or a well-maintained library.

### JWT Bearer Tokens

**Best for:** Stateless auth across microservices, short-lived access tokens.

Rules:
- 15 minutes max expiry for access tokens
- Validate `iss`, `aud`, `exp` on every request
- Use asymmetric signing (RS256) if multiple services verify tokens
- Never put secrets in the payload (it's base64, not encrypted)
- Pair with refresh tokens for session continuity

## Rate Limiting

### Algorithms

**Token bucket:** Each client gets a bucket that refills at a steady rate. Each request takes a token. When empty, requests are rejected. Allows bursts up to bucket size.

**Sliding window:** Count requests in a rolling time window. Smoother than fixed windows, slightly more memory.

**Fixed window:** Count requests per calendar interval (per minute, per hour). Simple but allows bursts at window boundaries (59th second + 1st second = 2x the limit in 2 seconds).

**Recommendation:** Token bucket for most APIs. Sliding window if you need strict per-interval limits.

### Implementation

**Per-user vs per-IP:**
- Authenticated endpoints: rate limit by user/API key
- Unauthenticated endpoints: rate limit by IP (but be aware of shared IPs / NAT)
- Sensitive endpoints (login, signup): rate limit by IP AND by target account

**Response headers** (always include these):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1640995200
Retry-After: 30
```

When limited, return **429 Too Many Requests** with `Retry-After` header.

**Where to implement:** API gateway (Kong, AWS API Gateway) for global limits. Application code for per-endpoint or per-user logic. Redis is the standard backing store for distributed rate limiting.

## Webhook Design

### Sending Webhooks

**Signing:** Every webhook must be signed so receivers can verify it came from you.

```
Webhook-Signature: sha256=abc123...
Webhook-Timestamp: 1640995200
```

Compute HMAC-SHA256 over `timestamp.body` using a shared secret. Include the timestamp to prevent replay attacks (receiver rejects if timestamp is too old).

**Retry with exponential backoff:**
- Attempt 1: immediate
- Attempt 2: 1 minute
- Attempt 3: 5 minutes
- Attempt 4: 30 minutes
- Attempt 5: 2 hours
- After 5 failures: mark endpoint as failing, notify the user, stop retrying

**Idempotency:** Include a unique event ID. Receivers should deduplicate by event ID in case retries deliver the same event twice.

**Event types:** Use dot-notation: `user.created`, `payment.succeeded`, `invoice.finalized`. Let users subscribe to specific event types.

**Payload structure:**
```json
{
  "id": "evt_abc123",
  "type": "user.created",
  "created_at": "2024-01-15T10:30:00Z",
  "data": {
    "id": "usr_456",
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```

### Receiving Webhooks

- Always verify the signature before processing
- Return 200 immediately, process asynchronously (queue the event)
- Store events for debugging and replay
- Handle out-of-order delivery (events may not arrive in sequence)

## API Gateway Patterns

### When You Need One

- **Multiple backend services**: Route `/users` to user service, `/orders` to order service
- **Centralized auth**: Validate tokens once at the gateway, pass user context downstream
- **Rate limiting**: Apply limits before requests hit your services
- **Request transformation**: Convert between external API shape and internal service shapes
- **SSL termination**: Handle TLS at the edge

### When You Don't

- **Single service**: Just put auth and rate limiting in your app. A gateway adds latency and a failure point.
- **Simple proxy needs**: Nginx or Caddy can handle routing without a full gateway.

**Options:** Kong (self-hosted, plugin ecosystem), AWS API Gateway (managed, pay-per-request), Traefik (container-native), Express Gateway (Node.js native).

## Caching

### HTTP Caching (GET endpoints)

**ETags:** Server sends `ETag: "abc123"` with response. Client sends `If-None-Match: "abc123"` on next request. Server returns 304 Not Modified if nothing changed. Saves bandwidth, not server processing.

**Cache-Control:**
```
Cache-Control: public, max-age=3600          # CDN + browser cache for 1 hour
Cache-Control: private, max-age=60           # Browser only, 1 minute (user-specific data)
Cache-Control: no-store                       # Never cache (sensitive data)
```

**CDN caching:** Put a CDN (Cloudflare, CloudFront) in front of your API for public GET endpoints. Vary header by Authorization if responses differ per user.

### Application-Level Caching

For data that's expensive to compute but doesn't change often:
- Cache in Redis with TTL
- Invalidate on write (cache-aside pattern)
- Use stale-while-revalidate for high-traffic endpoints

## Long-Running Operations

### Decision Tree

```
How long does the operation take?
├── < 1 second → Synchronous response
├── 1-30 seconds → Synchronous with timeout, or async with polling
├── 30 seconds - 5 minutes → Async with polling or webhooks
└── > 5 minutes → Async with webhooks (and a status endpoint)
```

### Polling Pattern

```
POST /exports → 202 Accepted
  { "id": "job_123", "status": "processing", "status_url": "/exports/job_123" }

GET /exports/job_123 → 200 OK
  { "id": "job_123", "status": "processing", "progress": 45 }

GET /exports/job_123 → 200 OK
  { "id": "job_123", "status": "complete", "result_url": "/exports/job_123/download" }
```

Return 202 Accepted (not 200) for the initial request. Include a URL to check status.

### Webhooks

Better than polling for long operations. Client provides a callback URL, you POST results when done.

### Server-Sent Events (SSE)

**Best for:** Server-push updates, progress tracking, live feeds.

Simpler than WebSockets. Unidirectional (server to client). Works over HTTP/1.1. Auto-reconnects. Good browser support.

Use when: Client needs real-time updates but doesn't need to send data back.

### WebSockets

**Best for:** Bidirectional real-time (chat, collaborative editing, gaming).

More complex than SSE. Needs its own connection management, reconnection logic, heartbeats. Use only when you genuinely need two-way communication.

### Polling (Simple)

Sometimes the simple answer is: client sends GET every 5 seconds.

Works everywhere, no special infrastructure, easy to debug. Inefficient at scale, but if you have 100 users checking job status, polling is fine. Don't over-engineer.

## Batch Endpoints

### When to Add Them

- Clients regularly need to create/read/update multiple resources in one request
- Mobile apps minimizing round trips
- Import/export workflows

### How to Design Them

```
POST /users/batch
{
  "operations": [
    { "method": "create", "body": { "name": "Alice" } },
    { "method": "create", "body": { "name": "Bob" } }
  ]
}
```

Response should report per-item success/failure:
```json
{
  "results": [
    { "status": 201, "data": { "id": "1", "name": "Alice" } },
    { "status": 422, "error": { "code": "VALIDATION_ERROR", "message": "Name too short" } }
  ]
}
```

Set a reasonable batch size limit (100-1000 items). Document it. Return 207 Multi-Status if some items succeed and others fail.

## File Uploads

### Direct Upload (multipart/form-data)

**Best for:** Small files (< 10MB), simple setups.

```
POST /avatars
Content-Type: multipart/form-data
```

Parse with multer (Node.js), python-multipart (Python), etc. Validate file type and size before processing.

### Presigned URLs (Large Files)

**Best for:** Large files, direct-to-storage uploads, reducing server load.

Flow:
1. Client requests upload URL: `POST /uploads/request → { "upload_url": "https://s3.../presigned", "file_id": "abc" }`
2. Client uploads directly to storage (S3, GCS) using the presigned URL
3. Client confirms: `POST /uploads/abc/complete`
4. Server validates the upload and processes it

This keeps large files off your API servers entirely. Essential for files over 10MB or when you're running on serverless (which has body size limits).

**Multipart uploads for very large files (>100MB):** S3 multipart upload with presigned URLs for each part. Libraries handle this -- don't implement the chunking yourself.
