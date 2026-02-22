# Mocking Patterns

## When to Mock

Mock things that are **external, slow, non-deterministic, or expensive**:
- External HTTP APIs (third-party services, payment providers)
- Time (`Date.now()`, `new Date()`) when behavior depends on it
- Randomness (`Math.random()`, UUIDs) when you need deterministic output
- File system operations in unit tests
- Expensive computations you've already tested elsewhere
- Email/SMS/notification services

## When NOT to Mock

This is more important than knowing when to mock. **Over-mocking is the #1 testing mistake.**

- **Your own code**: If you mock the module you're testing, you're testing nothing. If you mock its internal dependencies, you're testing implementation details.
- **Your database**: Use a real test database. Mocking SQL queries means you're testing that your mock returns what you told it to -- that's circular.
- **Internal modules**: If `serviceA` calls `serviceB`, test them together. Mocking `serviceB` means you'll never catch when they break each other.
- **Simple utilities**: Don't mock `formatDate()` inside a component test. Let it run.

**The rule:** Mock at the boundary of your system, not inside it. If you own the code, don't mock it.

## Mock Hierarchy

From least to most fake:

### Spy (Observe)
Wraps the real function. It still runs, but you can see how it was called.
```
// "Did this function get called with the right args?"
const spy = jest.spyOn(analytics, 'track')
doSomething()
expect(spy).toHaveBeenCalledWith('event_name', { userId: '123' })
```
**Use when:** You want to verify a side effect happened without changing behavior.

### Stub (Replace Return Value)
Replaces the return value but doesn't assert on calls.
```
// "Make this function return a specific value"
jest.spyOn(userService, 'getUser').mockReturnValue({ id: '1', name: 'Test' })
```
**Use when:** You need to control a dependency's output to test different code paths.

### Mock (Replace + Assert)
Replaces the function entirely and lets you assert on how it was called.
```
// "Replace this function and verify it was called correctly"
const sendEmail = jest.fn()
notifyUser(user, { sendEmail })
expect(sendEmail).toHaveBeenCalledWith(user.email, expect.any(String))
```
**Use when:** You need to verify both the output consumed and the interaction.

### Fake (Simplified Implementation)
A working implementation that's simpler than the real thing.
```
// In-memory database instead of real Postgres
class FakeUserRepository {
  users = new Map()
  async save(user) { this.users.set(user.id, user) }
  async findById(id) { return this.users.get(id) }
}
```
**Use when:** The real dependency is complex but the interface is simple. Fakes give you the most realistic behavior without the infrastructure cost.

## Dependency Injection for Testability

You don't need a DI framework. Just pass dependencies as arguments.

**Hard to test:**
```javascript
import { db } from './database'
export function getActiveUsers() {
  return db.query('SELECT * FROM users WHERE active = true')
}
```

**Easy to test:**
```javascript
export function getActiveUsers(db) {
  return db.query('SELECT * FROM users WHERE active = true')
}
```

Now you can pass a test database, a fake, or a mock. No framework needed -- just function arguments or constructor parameters.

**Don't over-engineer it.** You don't need interfaces, abstract factories, or IoC containers for most applications. If passing the dependency as an argument works, that's enough.

## Test Databases

### SQLite In-Memory
- **Good for:** Simple schemas, fast tests, no Docker needed
- **Bad for:** Postgres-specific features (JSONB, arrays, window functions, extensions)
- **Warning:** SQLite has different type coercion and syntax than Postgres. Your tests can pass and production can fail.

### Docker Test Database (Postgres, MySQL)
- **Good for:** Testing against the real engine, Postgres-specific features, CI environments
- **Pattern:** Start container in `beforeAll`, run migrations, seed data, truncate between tests
- **Tools:** `testcontainers` (Node/Java/Go), Docker Compose for CI

### Transaction Rollback
- **Pattern:** Wrap each test in a transaction, rollback at the end
- **Good for:** Speed (no truncation needed), isolation between tests
- **Bad for:** Tests that need to test transaction behavior itself

### Test Data
- Use factory functions, not hardcoded fixtures
- Each test should create its own data (don't share test data between tests)
- Use realistic-looking data (`faker`) but deterministic seeds for reproducibility

## HTTP Mocking

### MSW (Mock Service Worker)
**Best for frontend.** Intercepts at the network level, works with any HTTP client.
```javascript
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) => {
    return res(ctx.json([{ id: 1, name: 'Test User' }]))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### nock (Node.js)
**Best for Node backends.** Intercepts `http`/`https` module requests.
```javascript
nock('https://api.example.com')
  .get('/users')
  .reply(200, [{ id: 1, name: 'Test User' }])
```

### responses (Python)
**Best for Python.** Decorates test functions to mock `requests` library.
```python
@responses.activate
def test_get_users():
    responses.add(responses.GET, 'https://api.example.com/users',
                  json=[{'id': 1, 'name': 'Test User'}])
    result = get_users()
    assert len(result) == 1
```

## Time Mocking

When tests depend on the current time:

**Jest:**
```javascript
jest.useFakeTimers()
jest.setSystemTime(new Date('2024-01-15T10:00:00Z'))
// ... test code ...
jest.useRealTimers()
```

**Sinon:**
```javascript
const clock = sinon.useFakeTimers(new Date('2024-01-15T10:00:00Z'))
// ... test code ...
clock.restore()
```

**Python (freezegun):**
```python
@freeze_time("2024-01-15 10:00:00")
def test_something():
    assert datetime.now() == datetime(2024, 1, 15, 10, 0, 0)
```

## Common Anti-Patterns

### Mocking What You Don't Own
**Bad:** Mocking `axios` or `fetch` internals directly.
**Good:** Create a thin adapter (`apiClient.getUser()`) and mock that. When `axios` changes its API, you update one adapter, not fifty tests.

### Testing Mock Behavior
If your test asserts that a mock returned what you told it to return, you're testing the mock framework. This test proves nothing:
```javascript
// This is useless
const getUser = jest.fn().mockReturnValue({ name: 'Test' })
const result = getUser()
expect(result.name).toBe('Test') // You just tested jest.fn()
```

### Coupling Tests to Implementation
**Bad:** Asserting that function A calls function B with specific args (breaks when you refactor internals).
**Good:** Asserting that function A produces the correct output or side effect (survives refactoring).

### Over-Mocking
If your test has more mock setup than actual assertions, step back and ask:
- Am I testing at the wrong level? (Should this be an integration test?)
- Am I testing implementation details? (Mock fewer things, assert on outcomes)
- Is this code hard to test because it's doing too much? (Refactor the code, not the test)

**The smell:** If changing how code works (but not what it does) breaks your tests, you're over-mocking.
