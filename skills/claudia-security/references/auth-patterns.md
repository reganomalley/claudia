# Authentication Patterns

## Session-Based Auth

**Best for:** Server-rendered apps, simple web apps, small-medium scale.

**How it works:**
1. User submits credentials
2. Server validates, creates session (stored server-side: memory, Redis, DB)
3. Server sends session ID in httpOnly, Secure, SameSite=Lax cookie
4. Browser sends cookie on every request
5. Server looks up session, gets user

**Pros:** Simple, easy to revoke (delete session), no token parsing on every request.
**Cons:** Server-side state, harder to scale horizontally (need shared session store), CSRF risk.

**Implementation notes:**
- Use `express-session` + Redis for Node.js
- Regenerate session ID on login (prevents session fixation)
- Set cookie flags: `httpOnly`, `Secure`, `SameSite=Lax`
- Implement idle timeout (30min) and absolute timeout (24h)

## JWT-Based Auth

**Best for:** SPAs with API backends, microservices, mobile apps.

**How it works:**
1. User submits credentials
2. Server validates, issues access token (JWT, 15min) + refresh token (opaque, httpOnly cookie)
3. Client stores access token in memory (NOT localStorage)
4. Client sends access token in Authorization header
5. On expiry, client uses refresh token to get new access token

**Pros:** Stateless verification, works across services, good for APIs.
**Cons:** Can't revoke access tokens (only wait for expiry), complexity of refresh flow.

**Critical rules:**
- Access token: 15 minutes max, stored in memory only
- Refresh token: httpOnly cookie, rotate on use, store hash server-side
- Always validate `iss`, `aud`, `exp` claims
- Use RS256 (asymmetric) for multi-service, HS256 (symmetric) for single service
- Never put sensitive data in JWT payload (it's base64, not encrypted)

## OAuth 2.0 / OIDC

**Best for:** "Login with Google/GitHub", enterprise SSO, delegated access.

**Flows:**
- **Authorization Code + PKCE**: Web apps, SPAs, mobile (always use PKCE)
- **Client Credentials**: Server-to-server (no user involved)
- **Device Flow**: CLI tools, TVs, devices without browsers

**Implementation:**
- Use a library (Passport.js, NextAuth, Auth0 SDK) -- don't implement the flows yourself
- Always validate the `state` parameter (CSRF protection)
- Store tokens server-side when possible
- Implement proper token refresh handling

## Passwordless

**Best for:** Modern apps prioritizing UX, reducing credential-stuffing risk.

**Options:**
- **Magic links**: Email a login link with short-lived token (15min)
- **WebAuthn/Passkeys**: Hardware/biometric auth, phishing-resistant
- **OTP**: Email/SMS codes (SMS is weaker due to SIM swapping)

**Recommendation:** Passkeys are the future but magic links are the pragmatic choice today for most apps.
