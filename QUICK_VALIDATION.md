# Epic 1 - Quick Validation (5 Minutes)

## 1. Start System (30 seconds)

```bash
cd /Users/reena/plccoach/api-service
docker-compose up -d
sleep 5
```

## 2. Verify Health (15 seconds)

```bash
# Health check
curl http://localhost:8000/api/health
# ✅ Expected: {"status":"healthy","service":"PLC Coach API","version":"0.1.0"}

# Database check
curl http://localhost:8000/api/ready
# ✅ Expected: {"status":"ready","database":"connected"}
```

## 3. Run Tests (90 seconds)

```bash
docker-compose exec -T api pytest
# ✅ Expected: 80 passed, 12 skipped, 22 warnings in ~1.20s
```

## 4. Build Frontend (60 seconds)

```bash
cd ../frontend
npm run build
# ✅ Expected: dist/ folder created, ~295 KB bundle
```

## 5. Manual OAuth Test (90 seconds)

```bash
# Start dev server
npm run dev
```

**In browser:**
1. Open http://localhost:5173
2. Click "Login with Google"
3. Complete OAuth flow
4. ✅ Verify you're logged in (name in header)
5. Refresh page
6. ✅ Verify still logged in
7. Click "Logout"
8. ✅ Verify back at login page

---

## Pass Criteria Summary

- ✅ **Health**: Both endpoints return 200 OK
- ✅ **Tests**: 80 passed, 0 failed, 0 errors
- ✅ **Frontend**: Builds successfully
- ✅ **Auth**: Complete OAuth flow works
- ✅ **Session**: Persists across refresh
- ✅ **Logout**: Clears session properly

---

## If Everything Passes

**Epic 1 is validated! ✅**

See `MANUAL_VALIDATION_EPIC1.md` for comprehensive testing guide.

---

## If Something Fails

### Quick Fixes

**Tests failing?**
```bash
docker-compose restart api
docker-compose exec -T api pytest
```

**Database issues?**
```bash
docker-compose down -v
docker-compose up -d
sleep 10
```

**Frontend build fails?**
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

**OAuth not working?**
- Check `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Verify redirect URI matches: `http://localhost:8000/auth/google/callback`

---

## Detailed Validation

For comprehensive testing including:
- Role-based access control
- Session expiry and inactivity
- Database schema validation
- Error handling scenarios
- Performance monitoring

See: **`MANUAL_VALIDATION_EPIC1.md`**
