# Testing Approaches

## Unit Testing

A good unit test is:
- **Fast**: Runs in under 1ms. If your unit test touches the filesystem, network, or database, it's not a unit test.
- **Isolated**: Fails for exactly one reason. No shared state between tests.
- **Behavioral**: Tests what the function does, not how it does it. Assert on outputs and side effects, not internal calls.
- **Readable**: The test name tells you what broke. `test('returns null for invalid email')` not `test('validateEmail case 3')`.

**Structure every test as Arrange-Act-Assert:**
```
// Arrange: set up inputs and expected outputs
// Act: call the function
// Assert: check the result
```

**What makes a bad unit test:**
- Tests implementation details (asserts on internal method calls)
- Requires complex setup or many mocks (it's probably an integration test)
- Tests multiple behaviors in one test
- Uses the same logic as the code under test to compute the expected value

## Integration Testing

Integration tests verify that real components work together. The key difference from unit tests: you use real dependencies, not mocks.

**What to integration test:**
- API route handlers: send HTTP requests, assert on response status + body
- Database queries: run against a test database, verify data is stored/retrieved correctly
- Component trees: render parent with real children, test data flow and user interaction
- Service layers: test the coordination between modules with real (or test) dependencies

**Setup patterns:**
- Use a test database (same engine as production, never SQLite-for-Postgres)
- Reset state between tests (truncate tables, not drop/recreate)
- Use factories or fixtures for test data, not hardcoded SQL
- Run in transactions and rollback for speed (when your test doesn't need to test transactions)

## E2E Testing

E2E tests verify critical user flows through the real application. They're expensive to write and maintain, so be selective.

**Rules for E2E:**
- Test only critical paths: signup, login, core feature, payment, data export
- Use `data-testid` attributes for selectors, never CSS classes or DOM structure
- Build in resilience: use auto-wait (Playwright does this), avoid hard `sleep()`
- Run against a seeded test environment, not production data
- Keep them independent: each test should set up its own state

**Dealing with flakiness:**
- Flaky tests destroy trust. A flaky test is worse than no test.
- Most flakiness comes from: timing issues (use auto-wait), shared state (isolate tests), external dependencies (mock at the network boundary)
- If a test is flaky and you can't fix it, delete it and replace with a more targeted integration test

## TDD (Test-Driven Development)

**When TDD helps:**
- Requirements are clear and well-defined
- Pure logic, algorithms, business rules
- Bug fixes (write the test that reproduces the bug, then fix)
- Library/API design (writing tests first clarifies the interface)

**When TDD slows you down:**
- Exploratory work where you don't know the interface yet
- UI development (the shape changes too fast)
- Unclear or shifting requirements
- Prototyping (test after you know what you're building)

**Practical TDD:**
1. Write the smallest failing test
2. Write the minimum code to pass it
3. Refactor
4. Repeat

Don't be dogmatic. If writing the test first isn't giving you signal, write the code first and test after. The goal is well-tested code, not religious adherence to a process.

## Property-Based Testing

Instead of testing specific examples, property-based testing generates random inputs and verifies that properties always hold.

**When to use:**
- Parsers (parse then serialize should round-trip)
- Serialization/deserialization (encode then decode = identity)
- Mathematical operations (commutativity, associativity)
- Data structure invariants (sorted output is same length as input)

**Tools:**
- JavaScript: `fast-check`
- Python: `Hypothesis`
- Rust: `proptest`

**Example property:** "For any valid JSON string, `parse(stringify(parse(s)))` equals `parse(s)`"

Property-based testing finds edge cases you'd never write by hand. Use it for anything with a clear invariant.

## Snapshot Testing

**Usually bad.** Snapshot tests:
- Test nothing specific (they just assert "nothing changed")
- Break on any change, training developers to blindly update snapshots
- Don't communicate intent (what is the test actually verifying?)
- Create massive diffs in PRs that nobody reviews

**Rare exceptions:**
- Serialization format stability (API response shapes, file formats)
- Error message wording (if exact wording matters for UX)

If you use snapshots, keep them small and focused. A snapshot of an entire component tree is a maintenance nightmare.

## Contract Testing

For systems where multiple services communicate, contract tests verify that the API contract between producer and consumer stays compatible.

**When to use:**
- Microservices that deploy independently
- Public APIs with external consumers
- Teams that own different services

**Tools:**
- **Pact**: Consumer-driven contract testing. Consumer defines expectations, provider verifies.
- **Schema validation**: OpenAPI/JSON Schema validation in CI (lighter weight than Pact)

**How it works with Pact:**
1. Consumer writes a test that defines expected request/response
2. Pact generates a contract file
3. Provider runs the contract against their real API
4. If it passes, the services are compatible

## Testing in CI

**Order matters for fast feedback:**
1. **Lint + type check** (seconds) -- catch syntax errors and type issues instantly
2. **Unit tests** (seconds-minutes) -- fast, high signal
3. **Integration tests** (minutes) -- slower, catch real interaction bugs
4. **E2E tests** (minutes-tens of minutes) -- slowest, highest confidence

**CI best practices:**
- Fail fast: run cheap checks first so developers get feedback quickly
- Parallelize: split test suites across workers (Jest `--shard`, Playwright `--workers`)
- Cache dependencies: don't reinstall node_modules on every run
- Use test databases in CI: Docker services in GitHub Actions, or in-memory where appropriate
- Report coverage but don't gate on it: coverage thresholds create perverse incentives to write bad tests
- Run E2E on merge to main, not on every PR (unless they're fast)
