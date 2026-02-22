# Secrets Management

## The Secrets Lifecycle

1. **Generation** -- Use cryptographically secure random generators, never predictable values
2. **Storage** -- Appropriate tool for the environment (see below)
3. **Distribution** -- Secrets reach the app at runtime, never baked into images/builds
4. **Rotation** -- Automated rotation on a schedule, immediate rotation on compromise
5. **Revocation** -- Ability to instantly invalidate any secret
6. **Audit** -- Log who accessed what secret when

## Storage by Environment

### Local Development
- `.env` file with `dotenv` library
- **Must be in `.gitignore`** -- check this first
- Provide `.env.example` with dummy values for onboarding
- Never use production secrets in development

### CI/CD
- **GitHub Actions**: Repository or organization secrets
- **GitLab CI**: CI/CD variables (masked + protected)
- **CircleCI**: Project environment variables or contexts
- Never echo secrets in logs; mask them in CI output

### Production

| Tool | Best For | Notes |
|------|----------|-------|
| AWS SSM Parameter Store | Simple key-value, AWS-native | Free for standard params, integrates with IAM |
| AWS Secrets Manager | Rotation needed, RDS credentials | Auto-rotation for supported services, costs per secret |
| HashiCorp Vault | Multi-cloud, complex policies | Self-hosted or HCP, steep learning curve |
| Doppler | Team-friendly, multi-environment | SaaS, good DX, syncs to cloud providers |
| 1Password (Connect) | Small teams already using 1Password | Simple, familiar UI |

### Kubernetes
- Kubernetes Secrets (base64, not encrypted by default)
- Better: External Secrets Operator + cloud secret manager
- Best: Sealed Secrets or SOPS for GitOps

## Common Mistakes

**Committing secrets to git:**
- Even if you delete the file, it's in git history
- Use `git-secrets` or `trufflehog` as pre-commit hooks
- If it happens: rotate the secret immediately, then clean history with `git filter-branch` or BFG

**Hardcoding in application code:**
- Claudia's `check-secrets.sh` hook catches this at edit time
- Always use environment variables or secret manager SDK

**Sharing secrets in Slack/email:**
- Use a secret-sharing tool (1Password, Vault, even `age` encryption)
- Secrets in chat persist in search forever

**Not rotating:**
- Set calendar reminders or automate with your secret manager
- 90-day rotation for most secrets, immediate on personnel changes
