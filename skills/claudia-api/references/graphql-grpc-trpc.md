# GraphQL, gRPC, and tRPC

## GraphQL

### When It Shines

- **Mobile apps with varied screens**: Each screen fetches exactly the data it needs, no over-fetching
- **Multiple client types**: Web, mobile, TV, third-party -- each queries differently against one schema
- **Complex nested data**: "Get user, their posts, each post's comments, and each commenter's avatar" in one request
- **Rapid frontend iteration**: Frontend devs can change data requirements without backend changes

### When It Hurts

- **Simple CRUD**: If your API is mostly "get thing, create thing, update thing," REST is simpler
- **Small teams**: The tooling overhead (schema, resolvers, codegen) doesn't pay off with 2-3 developers
- **Caching**: HTTP caching works beautifully with REST (GET /users/42 is a cacheable URL). GraphQL is POST to one endpoint -- CDN and browser caching don't work out of the box
- **File uploads**: No native support. You end up bolting on multipart or using presigned URLs alongside GraphQL
- **Authorization**: Field-level auth is possible but complex. Easy to accidentally expose data through nested resolvers

### GraphQL Gotchas

**N+1 queries:** The biggest performance trap. A query for 20 users with their posts fires 1 query for users + 20 queries for posts.

Fix: Use **DataLoader** (batches + caches within a request). This is not optional -- every GraphQL server needs it.

```javascript
const userLoader = new DataLoader(ids => db.users.findByIds(ids));
// Instead of 20 individual queries, one query with WHERE id IN (...)
```

**Query complexity:** Clients can request arbitrarily deep/wide queries. Without limits, one query can bring down your server.

Fix: Implement query depth limiting and complexity analysis. Libraries like `graphql-query-complexity` help.

**Schema sprawl:** GraphQL schemas grow fast. Without discipline, you end up with hundreds of types and no one knows what's deprecated.

Fix: Treat your schema like a public API. Review changes, deprecate before removing, document types.

### GraphQL Tooling

**Servers:**
- **Apollo Server**: Most popular, heavy, lots of features
- **GraphQL Yoga**: Lighter, Envelop plugin system, good defaults
- **Mercurius**: Fastify-based, performant

**Schema building:**
- **Schema-first**: Write `.graphql` files, generate resolvers. Good for teams with non-TS backend.
- **Code-first** (recommended): **Pothos** (TypeScript) -- type-safe schema from code, no codegen step. Nexus is similar but less maintained.

**Clients:**
- **Apollo Client**: Full-featured, normalized cache, complex. Use for large apps.
- **urql**: Lighter, simpler caching, good default choice.
- **Relay**: Facebook's client. Opinionated, powerful, steep learning curve. Only worth it for very large apps.
- **graphql-request**: Minimal, no cache. Good for server-side or simple cases.

**Codegen:**
- **GraphQL Code Generator**: Generates TypeScript types from your schema. Essential for type safety. Run it in watch mode during development.

## gRPC

### When to Use

- **Service-to-service communication**: The primary use case. Two backend services talking to each other.
- **High throughput**: Protobuf is 2-10x smaller than JSON, faster to serialize/deserialize.
- **Streaming**: Native support for server streaming, client streaming, and bidirectional streaming.
- **Polyglot microservices**: Define the contract in `.proto` files, generate clients in any language. Python service talks to Go service with type-safe contracts.
- **Strict contracts**: Protobuf enforces schema. Fields have types, required/optional is explicit. No ambiguity.

### When Not to Use

- **Browser clients**: gRPC uses HTTP/2 + protobuf, browsers can't call gRPC directly. You need gRPC-Web (a proxy that translates) -- it works but adds a moving part.
- **Simple APIs**: If you have 5 endpoints and one client, the proto compilation step and tooling aren't worth it.
- **Third-party APIs**: External developers expect REST + JSON. Don't make them learn protobuf.
- **Rapid prototyping**: Writing `.proto` files, compiling, regenerating -- slower iteration than REST.

### gRPC Concepts

**Protobuf:** Binary serialization format. You define messages and services in `.proto` files, compile them to language-specific code.

```protobuf
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (ListUsersRequest) returns (stream User);  // server streaming
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}
```

**Streaming types:**
- **Unary**: Normal request/response (like REST)
- **Server streaming**: Client sends one request, server sends back a stream (live updates, large datasets)
- **Client streaming**: Client sends a stream, server responds once (file upload, aggregation)
- **Bidirectional streaming**: Both sides stream (chat, real-time sync)

**Deadlines:** Every gRPC call should have a deadline (timeout). This propagates across services -- if Service A calls B calls C with a 5s deadline, C knows how much time is left. Always set deadlines. A missing deadline = potential infinite hang.

**Interceptors:** gRPC's version of middleware. Use for logging, auth, metrics, tracing. Chain them like Express middleware.

**Error codes:** gRPC has its own status codes (OK, NOT_FOUND, PERMISSION_DENIED, etc.). Map them to HTTP codes at the gateway if you need a REST facade.

## tRPC

### When to Use

- **TypeScript fullstack**: Next.js, Remix, or any setup where client and server share a TypeScript codebase
- **Internal tools and dashboards**: Fast to build, type safety catches bugs early
- **Prototypes**: Zero schema definition, zero codegen. Define a function on the server, call it on the client with full types.

### Limitations

- **TypeScript only**: If any client will ever be written in Python, Swift, Kotlin, or anything else -- tRPC can't help them.
- **Tight coupling**: Client types are derived directly from server code. Deploying independently is harder.
- **Not a standard**: There's no tRPC spec. It's a library, not a protocol. If you switch frameworks, you rewrite.
- **Scaling concerns**: Fine for monorepos. Gets awkward with separate repos or when you need API versioning.

### tRPC Setup Pattern

```typescript
// server: define router
const appRouter = router({
  user: router({
    get: publicProcedure
      .input(z.object({ id: z.string() }))
      .query(({ input }) => db.user.findUnique({ where: { id: input.id } })),
    create: publicProcedure
      .input(z.object({ name: z.string(), email: z.string().email() }))
      .mutation(({ input }) => db.user.create({ data: input })),
  }),
});

// client: call with full type safety
const user = await trpc.user.get.query({ id: '42' });
// user is fully typed -- no codegen, no schema file
```

### When to Outgrow tRPC

You've outgrown tRPC when:
- You need non-TypeScript clients (mobile team writes Swift/Kotlin)
- You need a public API with documentation
- You want to deploy client and server independently with versioned contracts
- You're splitting into multiple services with separate teams

Migration path: tRPC -> REST (extract your Zod schemas into request/response types) or tRPC -> GraphQL (if you need the query flexibility).

## Comparison Table

| | REST | GraphQL | gRPC | tRPC |
|---|------|---------|------|------|
| **Wire format** | JSON | JSON | Protobuf (binary) | JSON |
| **Type safety** | Manual (OpenAPI) | Schema-based | Proto-based | Automatic (TypeScript) |
| **Latency** | Standard | Standard | Lower (binary + HTTP/2) | Standard |
| **Caching** | Excellent (HTTP native) | Hard (POST-based) | Application-level | Application-level |
| **Tooling maturity** | Excellent | Good | Good | Young but growing |
| **Learning curve** | Low | Medium | High | Low (if you know TS) |
| **Browser support** | Native | Native | Needs proxy (gRPC-Web) | Native |
| **Best documentation** | OpenAPI/Swagger | GraphQL Playground/Docs | Proto files | TypeScript types |
