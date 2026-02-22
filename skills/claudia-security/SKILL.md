---
description: >
  Security knowledge domain for Claudia. Use this skill when the user asks about authentication,
  authorization, secrets management, encryption, sandboxing, TEEs, API security, OWASP,
  OAuth, JWT, session management, CORS, CSP, or any security-related architecture decision.
  Triggers on phrases like "is this secure", "how should I authenticate", "store passwords",
  "API keys", "encrypt", "sandbox", or "zero trust".
---

# Claudia Security Domain

## Overview

This skill provides security decision frameworks. It doesn't replace a security audit -- it helps you make informed choices and avoid common pitfalls.

## Decision Trees

### Authentication: Which Method?

```
What are you building?
├── API consumed by other services
│   ├── Internal only → API keys + mTLS
│   └── External/public → OAuth 2.0 client credentials
├── Web app with users
│   ├── Simple/small scale → Session-based auth (cookie + server session)
│   ├── SPA + API backend → JWT (short-lived) + refresh tokens (httpOnly cookie)
│   └── Enterprise/SSO needs → OIDC with identity provider (Auth0, Okta, Keycloak)
├── Mobile app
│   └── OAuth 2.0 + PKCE (always PKCE for public clients)
└── CLI tool
    └── OAuth 2.0 device flow or API key
```

### Secrets: Where Do They Go?

```
What kind of secret?
├── API keys / tokens
│   ├── Development → .env file (gitignored) + dotenv library
│   ├── CI/CD → Pipeline secrets (GitHub Actions secrets, etc.)
│   └── Production → Secret manager (AWS SSM, Vault, Doppler)
├── Database credentials
│   ├── Local dev → .env or docker-compose env
│   └── Production → Secret manager + IAM roles where possible
├── Encryption keys
│   └── Always → KMS (AWS KMS, GCP KMS, Azure Key Vault)
└── User passwords
    └── Never store → bcrypt/argon2 hash only
```

### Common Mistakes (and fixes)

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| JWT in localStorage | XSS can steal tokens | httpOnly cookie for refresh, memory for access |
| Long-lived JWT (days/weeks) | Stolen token = long compromise | 15min access + rotating refresh tokens |
| Rolling your own auth | You will miss something | Use a library (Passport, NextAuth, Lucia) |
| Hardcoded secrets in code | Ends up in git history | .env + secret manager |
| CORS `*` in production | Any site can call your API | Whitelist specific origins |
| No rate limiting on auth | Brute force attacks | Rate limit login + lockout after N failures |
| MD5/SHA1 for passwords | Fast to crack | bcrypt (cost 12+) or argon2id |
| No CSRF protection | Forged requests from other sites | SameSite cookies + CSRF tokens |

## Deep References

For detailed guidance on specific topics, load:
- `references/auth-patterns.md` -- Full auth implementation patterns
- `references/secrets-management.md` -- Secrets lifecycle and tooling
- `references/tees-sandboxing.md` -- TEEs, sandboxing, and isolation

## Response Format

When advising on security:
1. **What to do** (concrete recommendation)
2. **Why** (what attack it prevents)
3. **How** (implementation sketch or library recommendation)
4. **What NOT to do** (common mistake for this scenario)
