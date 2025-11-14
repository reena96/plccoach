# Security Incident Report - Exposed OAuth Credentials

**Date**: 2025-11-14  
**Severity**: HIGH  
**Status**: MITIGATED (Credentials removed from code, rotation required)

---

## Summary

During a security audit, Google OAuth client secret was discovered hardcoded in `api-service/docker-compose.yml` and committed to git repository.

---

## Affected Secrets

### 1. Google OAuth Client Secret (CRITICAL)
- **Value**: `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`
- **Client ID**: `541993388762-fl23squpneq9soort2p0rs8cib2hqc5e.apps.googleusercontent.com`
- **Location**: `api-service/docker-compose.yml` (line 39)
- **Committed**: YES (visible in git history)
- **Exposure**: Public git repository (if pushed to GitHub/GitLab)

### 2. Session Secret (LOW)
- **Value**: `dev-secret-key-for-oauth-state-change-in-production`
- **Location**: `api-service/docker-compose.yml` (line 36)
- **Risk**: Low (development only, needs rotation for production anyway)

---

## Impact Assessment

### Potential Risks

1. **OAuth Token Hijacking**
   - Attacker could create malicious OAuth flows
   - Users could be redirected to attacker-controlled sites
   - User consent could be forged

2. **Data Access**
   - Attacker could potentially access Google user profiles
   - Email addresses and names could be harvested

3. **Reputation**
   - If exploited, could damage trust in the platform
   - Potential GDPR/privacy violations

### Actual Impact

- **Repository visibility**: Check if repo is public or private
- **Time exposed**: Since commit date (check `git log`)
- **Known exploitation**: NONE DETECTED (yet)

---

## Remediation Steps Completed

### ✅ Immediate Actions (DONE)

1. **Removed hardcoded secrets from docker-compose.yml**
   - Changed to use environment variables: `${GOOGLE_CLIENT_SECRET}`
   - Updated all OAuth-related secrets to load from `.env`
   - Added safe defaults for local development

2. **Created .env.example template**
   - Template file for developers to copy
   - No actual secrets included
   - Instructions for obtaining credentials

3. **Updated .dockerignore**
   - Ensures `.env` never enters Docker images
   - Alembic config included for migrations

4. **Documentation**
   - Created `SECURITY.md` with security policies
   - Created `SECURITY_INCIDENT_REPORT.md` (this file)
   - Updated validation guides

---

## Required Next Steps

### 🚨 URGENT (Within 24 hours)

1. **Rotate Google OAuth Credentials**
   ```
   1. Go to: https://console.cloud.google.com/apis/credentials
   2. Select project: PLC Coach (or your project name)
   3. Find OAuth 2.0 Client ID: 541993388762-fl23squpneq9soort2p0rs8cib2hqc5e
   4. Click "Delete" or "Regenerate Secret"
   5. Create new OAuth 2.0 credentials:
      - Application type: Web application
      - Authorized redirect URIs: http://localhost:8000/auth/google/callback
   6. Save new CLIENT_ID and CLIENT_SECRET
   7. Update api-service/.env file
   8. Test OAuth flow works
   ```

2. **Verify Repository Visibility**
   ```bash
   # Check if repo is public
   gh repo view --json visibility
   
   # If public, check when secret was first committed
   git log --all --full-history --source -- api-service/docker-compose.yml
   ```

3. **Check for Unauthorized Usage**
   - Review Google Cloud Console → APIs & Services → Credentials → OAuth consent screen → User data access
   - Check for any suspicious OAuth grants
   - Monitor for unusual authentication patterns

### 📋 Within 1 Week

4. **Generate New Session Secret**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Update SESSION_SECRET_KEY in .env
   ```

5. **Security Audit**
   - Scan codebase for other potential secret leaks:
   ```bash
   grep -r "secret\|password\|key\|token" --exclude-dir=node_modules --exclude-dir=venv --exclude=*.md
   ```

6. **Enable Secret Scanning**
   - Enable GitHub Advanced Security (if private repo)
   - Install git-secrets: `brew install git-secrets`
   - Configure pre-commit hooks

7. **Team Training**
   - Review secrets management best practices
   - Implement peer review for docker-compose.yml changes
   - Document in team wiki

---

## Prevention Measures

### Implemented

✅ `.env` file is gitignored  
✅ `.env.example` template with placeholders  
✅ `docker-compose.yml` uses environment variable syntax  
✅ Security documentation created  
✅ `.dockerignore` prevents secrets in images  

### To Implement

- [ ] Pre-commit hooks to prevent secret commits
- [ ] GitHub secret scanning enabled
- [ ] Regular security audits (quarterly)
- [ ] Secrets rotation schedule
- [ ] AWS Secrets Manager for production
- [ ] Monitoring and alerting for unauthorized access

---

## Timeline

| Date | Event |
|------|-------|
| Unknown | Secret first committed to git |
| 2025-11-14 | Security audit discovered issue |
| 2025-11-14 | Secrets removed from docker-compose.yml |
| 2025-11-14 | Documentation created |
| **PENDING** | **Google OAuth credentials rotated** |
| **PENDING** | Repository visibility verified |
| **PENDING** | Security scan completed |

---

## Verification Checklist

After rotating credentials:

- [ ] New Google OAuth credentials generated
- [ ] Old credentials deleted from Google Cloud Console
- [ ] `.env` file updated with new credentials
- [ ] Application tested with new credentials
- [ ] OAuth flow works for Google login
- [ ] No hardcoded secrets in any committed files
- [ ] `.env` file remains gitignored
- [ ] Team notified of new credential location
- [ ] This incident documented in team wiki

---

## Lessons Learned

### What Went Wrong

1. Hardcoded secrets in docker-compose.yml for "convenience"
2. No pre-commit hooks to catch secrets
3. No peer review caught the issue
4. Docker-compose.yml treated as "configuration" not "code"

### What Went Right

1. `.env` file was properly gitignored
2. Issue discovered before production deployment
3. Quick remediation possible
4. Clear documentation trail

### Improvements

1. **Never hardcode secrets** - Always use environment variables
2. **Review tool configuration files** - docker-compose, GitHub Actions, etc.
3. **Automate secret detection** - Pre-commit hooks, CI/CD scanning
4. **Principle of least privilege** - Limit who can access production secrets
5. **Regular audits** - Quarterly security reviews

---

## Sign-off

**Incident Discovered By**: Security Audit (2025-11-14)  
**Remediation By**: Development Team  
**Reviewed By**: _________________  
**Date Closed**: _________________  

**Notes**: Incident will be closed after:
1. Google OAuth credentials rotated
2. Verification checklist completed
3. No unauthorized access detected
