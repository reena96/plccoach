# Security Policy

## 🚨 Security Issue - Google OAuth Credentials Exposed

**CRITICAL**: The Google OAuth client secret was committed to git in `api-service/docker-compose.yml`.

### Immediate Actions Required

1. **Rotate Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to: APIs & Services → Credentials
   - Delete the OAuth 2.0 Client ID that was exposed
   - Create new OAuth credentials
   - Update `.env` file with new credentials (DO NOT commit!)

2. **Update Local Environment**
   ```bash
   cd api-service
   cp .env.example .env
   # Edit .env and add your new Google credentials
   ```

3. **Verify Secrets Not Committed**
   ```bash
   git diff HEAD docker-compose.yml
   # Should show secrets removed
   ```

---

## Secrets Management

### ✅ What's Protected

- `.env` file is gitignored ✓
- Secrets loaded from environment variables ✓
- `.env.example` template provided ✓

### ❌ Previous Issues (FIXED)

- ❌ Google OAuth secret was hardcoded in `docker-compose.yml`
- ❌ Session secret was hardcoded in `docker-compose.yml`
- ✅ Now using `${VARIABLE}` syntax to load from `.env`

---

## Current Secrets Inventory

| Secret | Location | Protected? | Exposure Level |
|--------|----------|------------|----------------|
| `GOOGLE_CLIENT_SECRET` | `.env` only | ✅ Yes | Previously exposed in git |
| `CLEVER_CLIENT_SECRET` | `.env` only | ✅ Yes | Placeholder only |
| `SESSION_SECRET_KEY` | `.env` only | ✅ Yes | Dev secret (rotate for prod) |
| `DATABASE_URL` | `.env` | ✅ Yes | Local dev only |
| `AWS credentials` | Not used yet | N/A | For production deployment |

---

## Best Practices

### For Developers

1. **NEVER commit secrets to git**
   - Always use `.env` file (gitignored)
   - Use `.env.example` as template
   - Use `${VARIABLE}` syntax in docker-compose.yml

2. **Use strong secrets in production**
   ```bash
   # Generate secure random key:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Check for secrets before committing**
   ```bash
   git diff --cached | grep -i "secret\|password\|key"
   ```

### For Production

1. **Use AWS Secrets Manager or equivalent**
   - Store all secrets in AWS Secrets Manager
   - Retrieve at runtime via IAM roles
   - Never store in environment variables in prod

2. **Rotate secrets regularly**
   - OAuth credentials: Every 90 days
   - Session keys: Every 30 days
   - Database passwords: Every 90 days

3. **Monitor for exposed secrets**
   - Enable GitHub secret scanning
   - Use tools like `git-secrets` or `truffleHog`
   - Regular security audits

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email: security@plccoach.example.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours.

---

## Cleanup Checklist

- [ ] Rotate Google OAuth credentials
- [ ] Update `.env` with new credentials
- [ ] Verify `docker-compose.yml` has no hardcoded secrets
- [ ] Test that services still work with new credentials
- [ ] Commit the fixed `docker-compose.yml`
- [ ] Monitor for any unauthorized OAuth usage

---

## Git History Note

⚠️ **The exposed Google OAuth secret exists in git history.**

To completely remove from history (destructive operation):
```bash
# WARNING: This rewrites git history - coordinate with team!
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch api-service/docker-compose.yml" \
  --prune-empty --tag-name-filter cat -- --all

# Then force push
git push origin --force --all
```

**Better approach**: Just rotate the credentials and move on. The old secret will be invalid.
