---
name: claudia-testing
description: >
  Testing strategy knowledge domain for Claudia. Use this skill when the user asks about testing
  approaches, what to test, test frameworks, unit vs integration vs e2e, mocking, TDD, test coverage,
  CI testing, or testing architecture. Triggers on phrases like "how to test", "should I test",
  "Jest vs", "unit test", "integration test", "e2e test", "test coverage", "mocking", "TDD",
  "testing strategy", "Playwright vs", "Vitest", or "test pyramid".
version: 0.1.0
---

# Claudia Testing Domain

## Overview

Testing is about confidence, not coverage numbers. Test the things that would hurt if they broke. A 40% coverage suite that tests critical paths well beats a 95% coverage suite full of snapshot tests and trivial assertions.

## The Test Pyramid: What Goes Where

```
What are you testing?
├── Pure logic, utilities, data transformations
│   └── Unit tests (fast, many, isolated)
├── API routes, database queries, component interactions
│   └── Integration tests (moderate speed, test real connections)
├── Critical user flows (signup, checkout, auth)
│   └── E2E tests (slow, few, high-value)
└── Not sure
    └── Ask: "If this broke in production, how bad would it be?"
        ├── Very bad → E2E test for the flow
        ├── Bad → Integration test
        └── Annoying → Unit test or skip it
```

### Unit Tests

Test pure functions, business logic, utilities, data transformations, state machines. These should be fast (< 1ms each), have no I/O, no network, no database. If you need mocks to test it, it might not be a unit test.

### Integration Tests

Test API route handlers with real middleware, database queries against a test database, component trees that interact (parent-child data flow), service layers that coordinate multiple modules. These can be slower and use real dependencies.

### E2E Tests

Test only critical user flows: can a user sign up, log in, and do the core thing your app exists for? Keep these minimal. Every E2E test you add is a test you have to maintain against flakiness.

## What NOT to Test

- **Implementation details**: Don't test that a function calls another function internally. Test the output.
- **Framework internals**: Don't test that React renders a div. React already tests that.
- **Trivial getters/setters**: `getName()` returning `this.name` doesn't need a test.
- **1:1 mock-heavy tests**: If your test mocks everything the function touches, you're testing the mocks, not the code.
- **CSS/styling**: Visual regression tools exist, but manual review catches more real issues.
- **Third-party libraries**: Don't test that `lodash.sortBy` works. Test your code that uses it.

## Framework Quick Comparison

| Framework | Best For | Why |
|-----------|----------|-----|
| Jest | Default for Node.js, React (CRA) | Mature, huge ecosystem, built-in mocking |
| Vitest | Vite projects, modern setups | Jest-compatible API, native ESM, faster |
| Playwright | E2E testing | Best cross-browser DX, auto-wait, trace viewer |
| Cypress | E2E + component testing | Great DX, time-travel debugging, component mode |
| pytest | Python (anything) | Fixtures, parametrize, best-in-class test runner |
| Testing Library | React/DOM component tests | Tests behavior not implementation, accessible queries |

**Quick picks:**
- Vite project? **Vitest**
- CRA or existing Jest setup? **Jest**
- E2E for web app? **Playwright** (Cypress if you need component testing too)
- Python? **pytest**, always
- Need to test components? **Testing Library** + your runner of choice

## Testing Strategy by App Type

```
What are you building?
├── REST/GraphQL API
│   ├── Heavy on: Integration tests (route handlers + DB)
│   ├── Some: Unit tests (validation, business logic)
│   └── Few: E2E tests (critical workflows via HTTP)
├── React / frontend app
│   ├── Heavy on: Component tests (Testing Library)
│   ├── Some: E2E tests (Playwright for critical flows)
│   └── Few: Unit tests (hooks, utils, state logic)
├── CLI tool
│   ├── Heavy on: Unit tests (command parsing, logic)
│   ├── Some: Integration tests (actual command execution)
│   └── Few: E2E tests (full command runs with assertions)
├── Library / package
│   ├── Heavy on: Unit tests (every public API surface)
│   ├── Some: Integration tests (common usage patterns)
│   └── Few: Property-based tests (for parsers, serialization)
└── Microservices
    ├── Heavy on: Integration tests (service boundaries)
    ├── Some: Contract tests (Pact, schema validation)
    └── Few: E2E tests (critical cross-service flows)
```

## Deep References

For detailed guidance on specific topics, load:
- `references/testing-approaches.md` -- Unit, integration, E2E, TDD, property-based, and CI strategies
- `references/mocking-patterns.md` -- When to mock, mock hierarchy, anti-patterns, test databases

## Response Format

When advising on testing:
1. **What to test** (specific recommendation for their situation)
2. **At which level** (unit / integration / e2e and why)
3. **With what tool** (framework recommendation)
4. **What NOT to test** (what they might be tempted to test but shouldn't)
