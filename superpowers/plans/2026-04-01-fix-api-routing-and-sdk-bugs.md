# Fix API Routing Prefix & SDK Bugs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the URL routing mismatch between the API server (`/api/` prefix) and all clients (SDKs, CLI, MCP) so that every interface correctly hits production endpoints, and fix secondary bugs found during testing.

**Architecture:** The API server mounts all oRPC routes under `/api/` prefix. Three SDKs (Node, Python, Go) are missing this prefix entirely. The CLI and parts of the MCP server use a nonexistent `/api/v1/` prefix. The fix normalizes all clients to include `/api` in their URL building, without changing the server. Email send returns 500 due to missing error handling around the SES call.

**Tech Stack:** TypeScript (Node SDK, CLI, MCP), Python (Python SDK), Go (Go SDK), Fastify/oRPC (API server)

---

## Test Results Summary

| Interface | Tests Run | Passed | Failed | Root Cause |
|-----------|-----------|--------|--------|------------|
| **curl (direct API)** | 15+ | All working | email send 500 | SES config / no error handling |
| **Node SDK** (default baseUrl) | 14 | 0 | 14 | Missing `/api` prefix |
| **Node SDK** (with `/api` workaround) | 15 | 12 | 3 | delete 204 bug, email 500, webhook auth |
| **Python SDK** (with `/api` workaround) | 17 | 16 | 1 | email 500 only |
| **Go SDK** (with `/api` workaround) | 14 | 13 | 1 | email 500 only |
| **CLI** | 3 | 0 | 3 | Uses `/api/v1/` (nonexistent) |
| **MCP** | not tested live | — | — | Mixed: some no prefix, some `/api/v1/` |

## Issues Found

### P0 — All SDK/CLI/MCP requests fail (routing prefix mismatch)

1. **Node SDK**: `buildUrl()` in `client.ts` builds `{baseUrl}{path}` → missing `/api`
2. **Python SDK**: `_build_url()` in `_http.py` builds `{base_url}{path}` → missing `/api`
3. **Go SDK**: `buildURL()` in `http.go` builds `{baseURL}{path}` → missing `/api`
4. **CLI**: All commands hardcode `/api/v1/{resource}` paths → should be `/api/{resource}`
5. **MCP**: Mixed — agent/email tools use `/{resource}` (missing `/api`), some tools use `/api/v1/{resource}` (extra `/v1`)

### P1 — Email send returns 500

6. **Server**: `sendEmailForAgent()` in `router-utils.ts` has no try-catch around `ses.sendEmail()` — any SES error becomes an unhandled 500

### P2 — Node SDK delete handling

7. **Node SDK**: `agents.delete()` crashes with "Cannot read properties of undefined (reading 'slice')" — the 204 response returns `undefined` but something downstream expects an object

### P2 — OpenAPI spec generation error

8. **Server**: `GET /openapi.json` returns `{"error":{"code":"INTERNAL_ERROR","message":"Internal server error"}}` — spec generation is broken

---

## File Structure

### Files to Modify

| File | Change |
|------|--------|
| `node/src/client.ts:112` | Add `/api` prefix in `buildUrl()` |
| `node/src/resources/agents.ts:35` | Fix delete return type |
| `python/src/anima/_http.py:150-152,227-229` | Add `/api` prefix in both `_build_url()` methods |
| `go/http.go:176` | Add `/api` prefix in `buildURL()` |
| `cli/src/lib/api-client.ts:53` | Add `/api` prefix in request method (centralized fix) |
| `cli/src/commands/**/*.ts` (~67 files) | Strip `/api/v1/` → bare paths (e.g., `/agents`) |
| `mcp/src/api-client.ts:58` | Add `/api` prefix in request method (centralized fix) |
| `mcp/src/tools/invoice/*.ts` | Strip `/api/v1/` → bare paths |
| `anima/apps/api/src/routes/router-utils.ts:2415` | Wrap SES call in try-catch |

### Files to Test

| File | Purpose |
|------|---------|
| `node/src/__tests__/client.test.ts` | Verify URL building includes `/api` |
| `python/tests/test_http.py` or equivalent | Verify URL building |
| `go/http_test.go` or `go/anima_test.go` | Verify URL building |
| `cli/src/__tests__/` | Verify CLI commands use correct paths |

---

### Task 1: Fix Node SDK URL prefix

**Files:**
- Modify: `node/src/client.ts:110-115`

- [ ] **Step 1: Read the current buildUrl method**

```typescript
// Current (line 112):
const url = new URL(`${this.baseUrl}${normalizedPath}`);
```

- [ ] **Step 2: Fix buildUrl to include /api prefix**

Change `client.ts` line 112:
```typescript
// Before:
const url = new URL(`${this.baseUrl}${normalizedPath}`);
// After:
const url = new URL(`${this.baseUrl}/api${normalizedPath}`);
```

- [ ] **Step 3: Verify with existing tests**

Run: `cd node && npm test 2>&1 | tail -20`

- [ ] **Step 4: Commit**

```bash
git add node/src/client.ts
git commit -m "fix(node-sdk): add /api prefix to all request URLs"
```

---

### Task 2: Fix Node SDK delete 204 handling

**Files:**
- Modify: `node/src/resources/agents.ts:34-36` and potentially other resource files
- Investigate: `node/src/client.ts:56-64` (204 response handling)

**Note:** The error "Cannot read properties of undefined (reading 'slice')" is a **runtime** crash. TypeScript generics are erased at runtime, so changing `<{ success: true }>` to `<void>` alone won't fix it. The root cause is that something downstream of the `delete()` call tries to access `.slice()` on the `undefined` return value. This needs investigation.

- [ ] **Step 1: Reproduce and trace the error**

Run the delete test and look at the full stack trace to find where `.slice()` is called:
```bash
node -e "
const { Anima } = require('@anima-labs/sdk');
const c = new Anima({ apiKey: 'mk_...', baseUrl: 'https://api.useanima.sh/api', maxRetries: 0 });
// Create then delete an agent, catch the full error with stack
"
```

- [ ] **Step 2: Fix based on investigation**

Likely fixes:
- If `.slice()` is in the SDK's error/response parsing: guard against undefined
- If the API returns 200 with `{"success":true}` for some deletes but 204 for others: ensure consistent handling
- Update all delete methods across resources (15+ files use `<{ success: true }>` pattern):

```bash
grep -rn 'request<{ success' node/src/resources/
```

- [ ] **Step 3: Run tests**

Run: `cd node && npm test 2>&1 | tail -20`

- [ ] **Step 4: Commit**

```bash
git add node/src/
git commit -m "fix(node-sdk): fix delete methods crashing on 204 No Content responses"
```

---

### Task 3: Fix Python SDK URL prefix

**Files:**
- Modify: `python/src/anima/_http.py:150-152,227-229`

- [ ] **Step 1: Fix sync HTTPClient._build_url (line ~150)**

```python
# Before:
def _build_url(self, path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{self._base_url}{normalized}"

# After:
def _build_url(self, path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{self._base_url}/api{normalized}"
```

- [ ] **Step 2: Fix async AsyncHTTPClient._build_url (line ~227)**

Same change as above for the async client.

- [ ] **Step 3: Run tests**

Run: `cd python && python -m pytest tests/ -v 2>&1 | tail -20`

- [ ] **Step 4: Commit**

```bash
git add python/src/anima/_http.py
git commit -m "fix(python-sdk): add /api prefix to all request URLs"
```

---

### Task 4: Fix Go SDK URL prefix

**Files:**
- Modify: `go/http.go:176`

- [ ] **Step 1: Fix buildURL method**

```go
// Before (line 176):
u, err := url.Parse(hc.baseURL + path)

// After:
u, err := url.Parse(hc.baseURL + "/api" + path)
```

- [ ] **Step 2: Run tests**

Run: `cd go && go test ./... -v 2>&1 | tail -30`

- [ ] **Step 3: Commit**

```bash
git add go/http.go
git commit -m "fix(go-sdk): add /api prefix to all request URLs"
```

---

### Task 5: Fix CLI route prefix (centralized fix + strip /api/v1/)

**Approach:** Like the SDK fixes, add `/api` in the CLI's central `api-client.ts`, then strip all `/api/v1/` prefixes from command files to bare paths. This is architecturally consistent with the SDK approach.

**Files:**
- Modify: `cli/src/lib/api-client.ts:53` (centralized fix)
- Modify: ~67 files in `cli/src/commands/` (strip `/api/v1/` → bare paths)

- [ ] **Step 1: Add /api prefix in api-client.ts**

In `cli/src/lib/api-client.ts` line 53, the `get()` method builds URLs as `${this.baseUrl}${path}`:
```typescript
// Before (line 53):
let url = `${this.baseUrl}${path}`;
// After:
let url = `${this.baseUrl}/api${path}`;
```

Also check `post()`, `put()`, `patch()`, `delete()` methods (lines 62, 66, 70, 74) — they also concatenate `${this.baseUrl}${path}`. Apply the same fix.

- [ ] **Step 2: Strip /api/v1/ from all command files to bare paths**

```bash
# Change /api/v1/agents → /agents, /api/v1/email/send → /email/send, etc.
find cli/src/commands -name '*.ts' -not -path '*__tests__*' -exec sed -i '' 's|/api/v1/|/|g' {} +
```

- [ ] **Step 3: Verify no /api/v1/ remains and paths are now bare**

```bash
grep -rn '/api/v1/' cli/src/commands/ | grep -v __tests__
# Should return nothing
grep -rn 'client\.\(get\|post\|put\|patch\|delete\)' cli/src/commands/ | head -5
# Should show bare paths like '/agents', '/email/send', etc.
```

- [ ] **Step 4: Run CLI tests**

Run: `cd cli && bun test 2>&1 | tail -30`

- [ ] **Step 5: Commit**

```bash
git add cli/src/lib/api-client.ts cli/src/commands/
git commit -m "fix(cli): centralize /api prefix in api-client, strip /api/v1/ from commands"
```

---

### Task 6: Fix MCP tool route prefixes (centralized fix)

**Approach:** Like the SDK and CLI fixes, add `/api` in the MCP's central `api-client.ts`. Most tools already use bare paths like `/agents` — these will just work. A few files use `/api/v1/` and need to be stripped to bare paths.

**Files:**
- Modify: `mcp/src/api-client.ts:58` (centralized fix)
- Modify: `mcp/src/tools/invoice/index.ts` (strip `/api/v1/`)

- [ ] **Step 1: Add /api prefix in mcp/src/api-client.ts**

In `mcp/src/api-client.ts` line 58:
```typescript
// Before:
const url = `${this.baseUrl}${path}`;
// After:
const url = `${this.baseUrl}/api${path}`;
```

- [ ] **Step 2: Strip /api/v1/ from the 3 affected files**

```bash
# Invoice tools use /api/v1/ — strip to bare paths
sed -i '' 's|/api/v1/|/|g' mcp/src/tools/invoice/index.ts
```

- [ ] **Step 3: Verify — check /health endpoint is handled**

The MCP utility tools call `/health` which is served at the root level (NOT under `/api`). Check `mcp/src/tools/utility/index.ts` — if it uses `/health`, it may need to be changed to use a raw fetch or the health endpoint needs to also work at `/api/health`.

Verify: `curl -s https://api.useanima.sh/api/health` — if this also returns 200, no special handling needed.

- [ ] **Step 4: Run MCP tests**

Run: `cd mcp && bun test 2>&1 | tail -30`

- [ ] **Step 5: Commit**

```bash
git add mcp/src/api-client.ts mcp/src/tools/
git commit -m "fix(mcp): centralize /api prefix in api-client, strip /api/v1/ from tools"
```

---

### Task 7: Fix email send error handling

**Files:**
- Modify: `anima/apps/api/src/routes/router-utils.ts:2410-2470`

- [ ] **Step 1: Read the current code around the SES call**

The current code at line ~2415:
```typescript
const sent = await ses.sendEmail({
    from: emailIdentity.email,
    to: params.to,
    cc: params.cc,
    bcc: params.bcc,
    subject: params.subject,
    body: params.body,
    bodyHtml: params.bodyHtml,
    headers: params.headers,
});
```

- [ ] **Step 2: Wrap in try-catch with meaningful error**

```typescript
let sent;
try {
    sent = await ses.sendEmail({
        from: emailIdentity.email,
        to: params.to,
        cc: params.cc,
        bcc: params.bcc,
        subject: params.subject,
        body: params.body,
        bodyHtml: params.bodyHtml,
        headers: params.headers,
    });
} catch (error) {
    const message = error instanceof Error ? error.message : "Unknown email delivery error";
    throw new InternalError(`Failed to send email via SES: ${message}`);
}
```

- [ ] **Step 3: Commit**

```bash
git add anima/apps/api/src/routes/router-utils.ts
git commit -m "fix(api): add error handling around SES sendEmail call"
```

---

### Task 8: Investigate and fix OpenAPI spec generation

**Files:**
- Modify: `anima/apps/api/src/server.ts:434-466`

- [ ] **Step 1: Read the OpenAPI endpoint handler**

Check the `openApiGenerator.generate()` call and what contract it receives.

- [ ] **Step 2: Check for runtime errors**

The 500 error on `/openapi.json` suggests the oRPC OpenAPI generator is crashing. Common causes:
- Missing or malformed contract definitions
- Incompatible oRPC version
- Circular references in Zod schemas

- [ ] **Step 3: Fix the issue based on findings**

This task requires investigation. Check server logs or add try-catch to capture the actual error.

- [ ] **Step 4: Commit if fix found**

```bash
git add anima/apps/api/src/server.ts
git commit -m "fix(api): fix OpenAPI spec generation"
```

---

### Task 9: End-to-end validation

- [ ] **Step 1: Run the Node SDK test script**

```bash
node test-node-sdk-fixed.mjs
# Update BASE_URL back to "https://api.useanima.sh" (without /api) to verify the fix
```

- [ ] **Step 2: Run the Python SDK test script**

```bash
python3 test-python-sdk.py
# Update BASE_URL back to "https://api.useanima.sh"
```

- [ ] **Step 3: Run the Go SDK test**

```bash
cd test-go-sdk && go run main.go
# Update baseURL back to "https://api.useanima.sh"
```

- [ ] **Step 4: Test CLI commands**

```bash
cd cli && bun src/cli.ts identity list --token "mk_..." --api-url "https://api.useanima.sh" --org "..." --json
```

- [ ] **Step 5: Verify email send returns a proper error (not 500)**

```bash
curl -s -X POST -H "Authorization: Bearer ak_..." -H "Content-Type: application/json" \
  -d '{"agentId":"...","to":["test@test.com"],"subject":"Test","body":"Test"}' \
  https://api.useanima.sh/api/email/send
```

- [ ] **Step 6: Clean up test files**

```bash
rm test-node-sdk.mjs test-node-sdk-fixed.mjs test-python-sdk.py
rm -rf test-go-sdk/
```

---

## Migration Note

**Breaking change for workaround users:** Anyone who worked around the missing `/api` prefix by setting `baseUrl` to `https://api.useanima.sh/api` will now get double-prefixed URLs (`/api/api/...`). After this fix, the correct `baseUrl` is `https://api.useanima.sh` (without `/api`). This should be documented in the changelog and SDK README update notes.
