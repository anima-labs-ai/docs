# Phase E — Vault Identity Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform mcp-vault from a Bitwarden-backed CRUD store into a market-leading agent secrets platform. Ship per-agent encryption, secret injection (CLI + browser + proxy), ephemeral scoped credentials, intent-aware policy enforcement, cross-channel analytics, and identity federation.

**Architecture:** Multi-repo at `/Users/diyanbogdanov/projects/agenticmail/`. Core platform at `anima/` (packages: `vault`, `security`, `contracts`, `db`, `shared`, `agent-identity`). MCP servers at `mcp-vault/`, `mcp-core/`, `mcp/`. SDKs at `node/`, `python/`, `go/`. CLI at `cli/`. Extension at `anima/apps/extension/`. Docs at `docs/`. Skill at `skill/`.

**Tech Stack:** TypeScript (Bun), Hono, oRPC, Prisma, AES-256-GCM, HKDF-SHA256, Ed25519, BullMQ, pgvector, Chrome Extensions API

**Spec:** `docs/superpowers/specs/2026-04-05-vault-identity-platform-design.md`
**Business Plan:** `docs/superpowers/specs/2026-04-05-vault-business-plan.md`

**Depends on:** Phases A-D complete (verified)

---

## Layer 1: Ship What's Built (Table Stakes)

### Task 1: Enable Vault Feature Flag & Fix Integration Gaps (E1)

**Files:**
- Modify: `anima/apps/api/src/config/features.ts` (or equivalent feature flag location)
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Modify: `anima/packages/vault/src/bw-serve-client.ts`
- Verify: `anima/apps/api/src/__tests__/integration/vault-crud.test.ts`
- Verify: `anima/apps/api/src/__tests__/e2e/vault-lifecycle.test.ts`

- [ ] **Step 1: Enable vault feature flag**
  - Find and set `FEATURE_VAULT_ENABLED` (or equivalent `isVaultEnabled()`) to `true` by default
  - Fix any "comming soon" typos to "coming soon" (search codebase)
  - Ensure env var override still works for disabling in specific environments

- [ ] **Step 2: Verify Vaultwarden connectivity**
  - Ensure `BW_SERVE_URL` and `VAULTWARDEN_URL` are properly configured in `.env.example`
  - Test `bw serve` sidecar connectivity from API
  - Verify SSL/TLS to Vaultwarden at `vault.useanima.sh`

- [ ] **Step 3: Run existing tests and fix any failures**
  - Run `vault-crud.test.ts` — fix any broken tests from API changes since vault was built
  - Run `vault-lifecycle.test.ts` — fix e2e test failures
  - Run `mcp-vault/src/__tests__/tool-registration.test.ts`
  - Ensure all vault-related tests are green

- [ ] **Step 4: Add missing error handling**
  - Add proper error responses when Vaultwarden is unavailable (503 with retry-after)
  - Add circuit breaker pattern for Vaultwarden calls (already in mcp-core, wire to API)
  - Add health check endpoint: `GET /vault/health`

**Acceptance criteria:** All vault endpoints return 200 (not 403). Existing tests pass. Health check reports healthy.

**Git commit:** `feat(vault): enable vault feature flag and fix integration gaps`

---

### Task 2: Per-Agent Encryption Keys (E2)

**Files:**
- Modify: `anima/packages/shared/src/key-management.ts`
- Modify: `anima/packages/shared/src/field-encryption.ts`
- Create: `anima/packages/vault/src/agent-encryption.ts`
- Modify: `anima/packages/vault/src/bw-serve-client.ts`
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/shared/src/__tests__/agent-encryption.test.ts`

- [ ] **Step 1: Add agent DEK derivation to key-management.ts**
  - Add `deriveAgentDEK(orgDEK: Buffer, agentId: string): Buffer` using HKDF-SHA256
  - Salt: `SHA-256(agentId + "vault-agent-dek" + version)`
  - Return a 256-bit key suitable for AES-256-GCM
  - Add key versioning support for rotation

- [ ] **Step 2: Create agent-encryption.ts in vault package**
  - `encryptForAgent(agentId: string, orgId: string, plaintext: string): string` — encrypts with agent-specific DEK
  - `decryptForAgent(agentId: string, orgId: string, ciphertext: string): string` — decrypts with agent-specific DEK
  - Use the same `enc:v1:` prefix format as field-encryption.ts
  - Include AAD (Additional Authenticated Data) with agentId to prevent ciphertext transplant

- [ ] **Step 3: Add agentDekVersion to VaultIdentity model**
  - Add `agentDekVersion Int @default(1)` to VaultIdentity in schema.prisma
  - Create Prisma migration
  - Add `agentDekFingerprint String?` for key verification

- [ ] **Step 4: Wrap credential storage with per-agent encryption**
  - Modify `bw-serve-client.ts`: before storing a credential in Vaultwarden, encrypt sensitive fields with agent DEK
  - On retrieval: decrypt with agent DEK before returning
  - Encrypted fields: password, notes, card number, CVV, API key value, certificate private key
  - Non-encrypted fields: name, username, URIs (needed for search/display)

- [ ] **Step 5: Write unit tests for agent encryption**
  - Test key derivation produces consistent output for same inputs
  - Test different agents produce different DEKs from same org
  - Test encrypt/decrypt roundtrip
  - Test AAD prevents cross-agent decryption
  - Test key rotation (re-encrypt with new version)

**Acceptance criteria:** Each agent's vault credentials are encrypted with agent-specific keys. Cross-agent decryption fails. Existing tests still pass.

**Git commit:** `feat(vault): add per-agent encryption with HKDF-derived keys`

---

### Task 3: Cross-Module Integration — Vault Wiring (E3)

**Files:**
- Modify: `anima/apps/api/src/routes/handlers/email.ts`
- Modify: `anima/apps/api/src/routes/handlers/phone.ts`
- Create: `anima/packages/vault/src/credential-resolver.ts`
- Create: `anima/packages/vault/src/__tests__/credential-resolver.test.ts`

- [ ] **Step 1: Create credential resolver service**
  - `resolveCredential(agentId: string, orgId: string, type: string, filter?: CredentialFilter): Credential`
  - Filter by type (login, oauth_token, api_key), provider name, URI pattern
  - Returns decrypted credential (using agent DEK) for internal service use
  - Never exposes credential to MCP/LLM layer — only for server-side service consumption

- [ ] **Step 2: Wire vault to email service**
  - When sending email through external SMTP (not Stalwart), check vault for SMTP credentials
  - Auto-resolve `login` credentials with URI matching `smtp://` or `smtps://`
  - If found, use vault credentials instead of requiring explicit SMTP config
  - Audit log: record credential usage for email sending

- [ ] **Step 3: Wire vault to phone service**
  - Check vault for Telnyx/Twilio API credentials per agent (if agent has custom provider)
  - Auto-resolve `api_key` credentials with provider matching `telnyx` or `twilio`
  - Fall back to platform credentials if no agent-specific ones found

- [ ] **Step 4: Write integration tests**
  - Test: store SMTP credential → send email → verify credential was used from vault
  - Test: store API key → make phone call → verify API key was used
  - Test: fallback to platform credentials when no vault credential exists

**Acceptance criteria:** Vault credentials are automatically consumed by email and phone services. Audit trail records each cross-module credential usage.

**Git commit:** `feat(vault): wire vault credentials to email and phone services`

---

### Task 4: Credential Sharing Model (E4)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/contracts/src/schemas/vault-sharing.ts`
- Create: `anima/packages/contracts/src/contracts/vault-sharing.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Create: `anima/apps/api/src/__tests__/integration/vault-sharing.test.ts`

- [ ] **Step 1: Add CredentialShare model to Prisma schema**
  - Fields: id, orgId, credentialId, sharedWithType (agent|member|pod), sharedWithId, permissions (read|use|rotate), expiresAt, maxUses, createdAt, createdBy
  - Unique constraint: [orgId, credentialId, sharedWithType, sharedWithId]
  - Indexes: orgId, credentialId, sharedWithId
  - Create migration

- [ ] **Step 2: Create sharing oRPC contracts and schemas**
  - `ShareCredentialInput`: credentialId, sharedWithType, sharedWithId, permissions, expiresAt?, maxUses?
  - `ShareCredentialOutput`: share details
  - `ListSharesInput`: credentialId
  - `ListSharesOutput`: paginated list of shares
  - `RevokeShareInput`: credentialId, shareId

- [ ] **Step 3: Implement sharing API handlers**
  - `POST /vault/credentials/:id/share` — share credential (requires owner or master key)
  - `GET /vault/credentials/:id/shares` — list shares for credential
  - `DELETE /vault/credentials/:id/shares/:shareId` — revoke share
  - Verify caller owns the credential before allowing share
  - Audit log: record share creation and revocation

- [ ] **Step 4: Modify credential access to check shares**
  - When an agent requests `vault_get_credential`, check:
    1. Does agent own the credential directly? → allow
    2. Does a CredentialShare exist for this agent/credential? → check permissions + expiry + maxUses
    3. Is the agent a member of a pod that has a share? → check pod share
    4. None of the above? → deny
  - Increment use count on each access via share

- [ ] **Step 5: Write integration tests**
  - Test: share credential with another agent → agent can read it
  - Test: share with expiry → access denied after expiry
  - Test: share with maxUses → access denied after max uses reached
  - Test: revoke share → access denied
  - Test: share with pod → all pod agents can access
  - Test: non-owner cannot share

**Acceptance criteria:** Credentials can be shared granularly within an org. Access control enforces permissions, expiry, and max uses.

**Git commit:** `feat(vault): add credential sharing with granular permissions`

---

## Layer 2: Differentiate (Competitive Edge)

### Task 5: Ephemeral Scoped Credentials (E5)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/vault/src/token-issuer.ts`
- Create: `anima/packages/contracts/src/schemas/vault-tokens.ts`
- Create: `anima/packages/contracts/src/contracts/vault-tokens.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Create: `anima/apps/api/src/workers/vault-token-cleanup-worker.ts`
- Create: `anima/packages/vault/src/__tests__/token-issuer.test.ts`
- Create: `anima/apps/api/src/__tests__/integration/vault-tokens.test.ts`

- [ ] **Step 1: Add VaultToken model to Prisma schema**
  - Fields: id, orgId, agentId, credentialId?, taskId?, scope[], allowedTools[], token (hashed), tokenPrefix, expiresAt, revokedAt, revokedBy, issuedBy, delegationChain (Json), deviceFingerprint?, lastUsedAt, useCount, maxUses?, createdAt
  - Indexes: orgId, agentId, token, expiresAt
  - Create migration

- [ ] **Step 2: Implement token issuer service**
  - `issueToken(params: IssueTokenParams): VaultToken` — creates token with:
    - 32 random bytes, base64url encoded, `vtk_` prefix
    - SHA-256 hashed before storage (same pattern as API keys)
    - TTL (default 15 min, max 24h, configurable)
    - Scope: array of allowed actions (read, use, inject, rotate)
    - Task binding: optional taskId that restricts token to specific task
    - Delegation chain: cryptographic proof of who authorized this token
  - `validateToken(rawToken: string): TokenValidation` — validates token:
    - Hash and lookup in DB
    - Check expiry, revocation, maxUses
    - Return token metadata (scope, agentId, taskId, etc.)
  - `revokeToken(tokenId: string, revokedBy: string): void`
  - `revokeAllAgentTokens(agentId: string): void`

- [ ] **Step 3: Create token oRPC contracts**
  - `POST /vault/tokens` — issue token (requires auth + scope specification)
  - `GET /vault/tokens` — list active tokens for agent
  - `GET /vault/tokens/:id` — get token details (not the raw token value)
  - `DELETE /vault/tokens/:id` — revoke token
  - `POST /vault/tokens/:id/refresh` — extend TTL (if policy allows, within max TTL)

- [ ] **Step 4: Add token-based authentication to vault endpoints**
  - Accept `vtk_` prefixed tokens in Bearer auth for vault operations
  - When a vault operation uses a `vtk_` token, enforce scope restrictions
  - Increment useCount on each use
  - Deny access if scope doesn't include required action

- [ ] **Step 5: Create token cleanup BullMQ worker**
  - Run every 5 minutes
  - Delete expired tokens older than 24 hours (keep for audit trail)
  - Mark expired tokens as revoked (revokedBy: "system")
  - Log cleanup statistics

- [ ] **Step 6: Integrate with existing DID system**
  - Token's delegation chain references agent's DID
  - Token issuance requires valid agent DID
  - Delegation chain is Ed25519-signed using agent's private key

- [ ] **Step 7: Write unit and integration tests**
  - Unit: token generation, hashing, validation, expiry, scope checking
  - Integration: issue token → use for vault access → verify scope enforcement
  - Integration: issue token → wait for expiry → verify access denied
  - Integration: issue token → revoke → verify access denied
  - Integration: issue token with maxUses=3 → use 3 times → verify 4th denied

**Acceptance criteria:** Ephemeral tokens can be issued, scoped, and revoked. Token-based auth works for all vault operations. Expired tokens are cleaned up automatically.

**Git commit:** `feat(vault): add ephemeral scoped credential tokens with TTL and task binding`

---

### Task 6: Intent-Aware Policy Engine (E6)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/vault/src/policy-engine.ts`
- Create: `anima/packages/contracts/src/schemas/vault-policies.ts`
- Create: `anima/packages/contracts/src/contracts/vault-policies.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Create: `anima/packages/vault/src/__tests__/policy-engine.test.ts`
- Create: `anima/apps/api/src/__tests__/integration/vault-policies.test.ts`

- [ ] **Step 1: Add VaultPolicy model to Prisma schema**
  - Fields: id, orgId, name, description?, rules (Json), priority, isDefault, version, previousVersion?, createdAt, updatedAt, createdBy
  - Unique: [orgId, name]
  - Create migration
  - Seed default policy: "allow all for org members, observe for agents"

- [ ] **Step 2: Implement policy engine**
  - `evaluatePolicy(context: PolicyContext): PolicyDecision`
  - PolicyContext: agentId, orgId, credentialId, credentialType, action, taskId?, riskScore?, timeOfDay, deviceFingerprint?
  - PolicyDecision: `{ outcome: "allow" | "deny" | "observe" | "step_up", reason: string, policyId: string, ruleId: string }`
  - Rule evaluation order: highest priority first, first match wins
  - Conditions: timeOfDay, maxUsesPerHour, requireApproval, allowedAgents, allowedTasks, riskScoreBelow, credentialTypes
  - "Observe" outcome: allow access but flag for review and log with elevated detail

- [ ] **Step 3: Create policy oRPC contracts**
  - `GET /vault/policies` — list org policies
  - `POST /vault/policies` — create policy (master key required)
  - `GET /vault/policies/:id` — get policy with version history
  - `PUT /vault/policies/:id` — update policy (creates new version, preserves old)
  - `DELETE /vault/policies/:id` — soft delete policy
  - `POST /vault/policies/evaluate` — dry-run policy evaluation (for testing)

- [ ] **Step 4: Wire policy engine into all vault access paths**
  - Before any credential read/use/inject: evaluate policy
  - On "deny": return 403 with reason
  - On "observe": allow but log with `severity: "warning"` and `observation: true`
  - On "step_up": return 403 with step-up instructions (see Task 7)
  - On "allow": proceed normally

- [ ] **Step 5: Add intent-aware context to policy evaluation**
  - Extract "intent" from MCP tool call context (tool name, tool arguments)
  - Pass intent to policy engine as additional context
  - Example: `vault_get_credential` with tool context showing it's for an email send vs. a database query → different policy rules can apply
  - Log intent alongside policy decision for forensic traceability

- [ ] **Step 6: Write tests**
  - Unit: rule evaluation, condition matching, priority ordering, default policies
  - Unit: allow/deny/observe/step_up outcomes with various conditions
  - Integration: create policy → access credential → verify policy enforced
  - Integration: update policy → verify new version applied, old version preserved
  - Integration: time-based rules (only allow during business hours)
  - Integration: rate-based rules (max 10 accesses per hour)

**Acceptance criteria:** Policies are evaluated on every vault access. Four outcomes work correctly. Intent context is captured and logged. Policy versioning preserves history.

**Git commit:** `feat(vault): add intent-aware policy engine with allow/deny/observe/step-up outcomes`

---

### Task 7: Step-Up Authorization (E7)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/vault/src/step-up.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Modify: `anima/apps/api/src/workers/` (notification worker)
- Create: `anima/apps/api/src/__tests__/integration/vault-step-up.test.ts`

- [ ] **Step 1: Add VaultStepUp model to Prisma schema**
  - Fields: id, orgId, agentId, credentialId, tokenId?, action, reason?, policyId, status (pending|approved|denied|expired), resolvedBy?, resolvedAt?, expiresAt, notificationChannel?, notificationSentAt?, createdAt
  - Indexes: [orgId, status], agentId
  - Create migration

- [ ] **Step 2: Implement step-up service**
  - `requestStepUp(params): VaultStepUp` — creates pending step-up request
  - `resolveStepUp(stepUpId, resolution, resolvedBy): VaultStepUp` — approves or denies
  - Auto-expire after configurable timeout (default 5 minutes)
  - On approval: issue a time-limited VaultToken with the originally requested scope

- [ ] **Step 3: Wire step-up notifications**
  - Use existing email service to send step-up requests to org admins
  - Include: agent name, credential name (not value), action requested, approve/deny links
  - Future: SMS and push notifications (phone service already exists)

- [ ] **Step 4: Create step-up API endpoints**
  - `GET /vault/step-ups` — list pending step-ups (for admin dashboard)
  - `POST /vault/step-ups/:id/approve` — approve (requires master key or admin)
  - `POST /vault/step-ups/:id/deny` — deny with reason

- [ ] **Step 5: Wire step-up into policy engine**
  - When policy returns "step_up", create VaultStepUp and return 403 with stepUpId
  - Agent polls or receives WebSocket notification when step-up is resolved
  - On approval, agent retries original operation with step-up token

- [ ] **Step 6: Write integration tests**
  - Test: policy triggers step-up → notification sent → admin approves → agent retries → success
  - Test: step-up expires → agent retry fails
  - Test: admin denies → agent retry fails
  - Test: step-up for different credential types

**Acceptance criteria:** Step-up authorization works end-to-end. Notifications are sent. Approvals and denials are enforced.

**Git commit:** `feat(vault): add step-up authorization with notification and approval flow`

---

### Task 8: CLI Credential Injection (E8)

**Files:**
- Modify: `cli/src/commands/vault.ts`
- Create: `cli/src/commands/vault-exec.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts` (add injection endpoint)
- Create: `cli/src/__tests__/vault-exec.test.ts`

- [ ] **Step 1: Add injection API endpoint**
  - `POST /vault/inject/env` — accepts credentialId(s), returns env var map
  - Response: `{ vars: { DB_PASSWORD: "value", API_KEY: "value" } }`
  - Requires valid VaultToken or API key
  - Policy engine evaluates with action="inject"
  - Audit log: record injection request with target env var names

- [ ] **Step 2: Implement `am vault exec` command**
  - Syntax: `am vault exec --credential <id> [--as <ENV_VAR>] -- <command> [args...]`
  - Multiple credentials: `--credential <id1> --credential <id2>`
  - Flow: authenticate → fetch env vars → spawn child process with injected env → wait → exit
  - Env vars are set ONLY in child process environment (not parent)
  - On child exit: log exit code and duration to audit trail

- [ ] **Step 3: Implement credential-to-env-var mapping**
  - Default mapping by credential type:
    - login: `{NAME}_USERNAME`, `{NAME}_PASSWORD`
    - api_key: `{NAME}_API_KEY`
    - oauth_token: `{NAME}_ACCESS_TOKEN`, `{NAME}_REFRESH_TOKEN`
    - certificate: `{NAME}_CERT`, `{NAME}_KEY`
  - `--as` flag overrides default env var name
  - Credential name is sanitized: uppercase, spaces→underscores, special chars removed

- [ ] **Step 4: Add `am vault list` and `am vault get` commands**
  - `am vault list` — list credentials (names only, not values)
  - `am vault get <id>` — show credential details (mask sensitive fields unless --reveal)
  - `am vault store` — interactively store a new credential
  - `am vault delete <id>` — delete credential

- [ ] **Step 5: Write tests**
  - Test: `am vault exec` injects env vars into child process
  - Test: child process can read env vars
  - Test: parent process does NOT have the env vars
  - Test: multiple credentials inject multiple vars
  - Test: `--as` flag overrides env var name
  - Test: audit trail records injection

**Acceptance criteria:** `am vault exec` injects credentials as env vars. LLM/agent never sees the secret values. Audit trail is complete.

**Git commit:** `feat(cli): add vault exec command for CLI credential injection`

---

### Task 9: Browser Autofill via Chrome Extension (E9)

**Files:**
- Modify: `anima/apps/extension/` (existing Chrome extension)
- Create: `anima/apps/extension/src/vault/` (vault module)
- Modify: `anima/apps/api/src/routes/handlers/vault.ts` (browser injection endpoint)
- Create: `anima/apps/extension/src/__tests__/vault-autofill.test.ts`

- [ ] **Step 1: Add browser injection API endpoint**
  - `POST /vault/inject/browser` — accepts credentialId, returns credential data
  - Response sent over authenticated WebSocket (not HTTP, to avoid request interception)
  - Requires valid VaultToken with scope including "inject"
  - Policy engine evaluates with action="browser_autofill"

- [ ] **Step 2: Add vault module to Chrome extension**
  - Create `anima/apps/extension/src/vault/autofill.ts`
  - Connect to API via authenticated WebSocket
  - Receive credential data in extension's service worker
  - Store temporarily in `chrome.storage.session` (cleared on browser close)
  - Never expose to page JavaScript (use isolated content script world)

- [ ] **Step 3: Implement content script for form filling**
  - Create `anima/apps/extension/src/vault/content-script.ts`
  - Detect login forms (username/password fields)
  - Fill form fields using credential data from service worker
  - Handle TOTP: auto-fill OTP fields if credential has TOTP
  - Confirm success/failure back to service worker

- [ ] **Step 4: Add MCP tool for browser autofill**
  - `vault_use_credential` MCP tool in mcp-vault:
    - Agent calls: `vault_use_credential(credentialId, "browser_autofill")`
    - Policy engine evaluates
    - If allowed: sends credential to Chrome extension
    - Agent receives success/failure (never the credential values)
    - Returns: `{ success: true, action: "browser_autofill", site: "github.com" }`

- [ ] **Step 5: Write tests**
  - Unit: form detection logic
  - Unit: credential injection into form fields
  - Integration: store credential → call vault_use_credential → verify form filled
  - E2E: full browser automation flow with autofill

**Acceptance criteria:** Agent can trigger browser autofill without seeing credential values. Extension fills forms and reports success/failure.

**Git commit:** `feat(extension): add vault browser autofill via Chrome extension`

---

## Layer 3: Build the Moat

### Task 10: Cross-Channel Identity Analytics (E10)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/vault/src/analytics.ts`
- Create: `anima/apps/api/src/workers/cross-channel-analytics-worker.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`
- Create: `anima/apps/api/src/__tests__/integration/vault-analytics.test.ts`

- [ ] **Step 1: Add AgentBehaviorProfile model to Prisma schema**
  - Fields: id, orgId, agentId (unique), emailPattern (vector(256)), phonePattern (vector(256)), vaultPattern (vector(256)), compositePattern (vector(256)), riskScore (float), riskFactors (Json), lastAnomalyAt, anomalyCount, emailsLast24h, callsLast24h, vaultAccessLast24h, updatedAt
  - Create migration with pgvector extension

- [ ] **Step 2: Create analytics worker**
  - BullMQ worker running every 5 minutes
  - Aggregates events from: Message (email), CallRecord (phone), CredentialAuditLog (vault)
  - Builds behavioral feature vectors per agent
  - Computes composite risk score using existing anomaly detection (from Phase D) + cross-channel correlation
  - Stores embeddings in pgvector for similarity search

- [ ] **Step 3: Implement cross-channel anomaly detection**
  - Detect patterns that span channels:
    - Volume spikes in one channel correlated with credential access in another
    - Unusual credential type escalation (agent usually reads login creds, suddenly accesses prod API keys)
    - Spend pattern change correlated with vault access change
  - Use z-score detection from existing `anima/packages/security/src/` anomaly detector
  - Add cross-channel correlation logic

- [ ] **Step 4: Wire risk score to policy engine**
  - Policy rules can now include `riskScoreBelow` condition
  - If agent's risk score exceeds threshold, policy can trigger step-up or deny
  - Real-time risk score update when significant events occur

- [ ] **Step 5: Create analytics API endpoints**
  - `GET /vault/analytics/risk-scores` — all agent risk scores in org
  - `GET /vault/analytics/anomalies` — recent anomalies with cross-channel context
  - `GET /vault/analytics/behavior/:agentId` — detailed behavioral profile
  - Dashboard data format for console UI

- [ ] **Step 6: Write tests**
  - Unit: feature extraction from events
  - Unit: cross-channel correlation logic
  - Integration: simulate events → verify risk score update
  - Integration: high risk score → policy triggers step-up
  - Integration: anomaly detected → alert generated

**Acceptance criteria:** Cross-channel behavioral profiles are maintained per agent. Risk scores update based on activity across all channels. Anomalies trigger policy enforcement.

**Git commit:** `feat(vault): add cross-channel identity analytics with pgvector behavioral profiles`

---

### Task 11: Forensic Traceability (E11)

**Files:**
- Modify: `anima/packages/vault/src/token-issuer.ts`
- Modify: `anima/packages/vault/src/policy-engine.ts`
- Create: `anima/packages/vault/src/delegation-chain.ts`
- Modify: `anima/apps/api/src/routes/handlers/vault.ts`

- [ ] **Step 1: Implement delegation chain builder**
  - Create `delegation-chain.ts`:
    - `buildChain(principal, action, scope, parentChain?): DelegationChain`
    - Each link is Ed25519-signed by the principal
    - Chain is serializable to JSON and base64
    - Verification: `verifyChain(chain): boolean` — checks all signatures

- [ ] **Step 2: Capture originating prompt hash**
  - When an MCP tool call triggers vault access, capture:
    - Hash of the prompt that led to the tool call (SHA-256, not the prompt itself)
    - Tool name and arguments
    - Session ID
  - Store in audit log as `forensicContext`

- [ ] **Step 3: Enhanced audit log entries**
  - Every vault operation now includes:
    - `delegationChain`: full chain from human → agent → action
    - `promptHash`: SHA-256 of originating prompt
    - `toolContext`: MCP tool name + arguments
    - `policyDecision`: which policy evaluated, outcome, reason
    - `riskScoreAtTime`: agent's risk score when action was taken

- [ ] **Step 4: Write tests**
  - Unit: delegation chain construction and verification
  - Unit: prompt hash computation
  - Integration: full trace from MCP tool call → vault access → audit log with complete context

**Acceptance criteria:** Every vault access has a complete forensic trail linking it back to the human principal and originating context.

**Git commit:** `feat(vault): add forensic traceability with delegation chains and prompt hash`

---

## Layer 4: Platform Endgame

### Task 12: Identity Federation — OIDC Provider (E12)

**Files:**
- Create: `anima/packages/oauth/src/provider.ts`
- Create: `anima/packages/oauth/src/jwks.ts`
- Create: `anima/packages/oauth/src/authorization.ts`
- Create: `anima/packages/oauth/src/token.ts`
- Modify: `anima/packages/db/prisma/schema.prisma`
- Modify: `anima/apps/api/src/router.ts`
- Create: `anima/packages/oauth/src/__tests__/provider.test.ts`

- [ ] **Step 1: Add OAuth models to Prisma schema**
  - OAuthClient: id, orgId, clientId, clientSecretHash, name, redirectUris[], scopes[], grantTypes[]
  - OAuthAuthorizationCode: id, code (hashed), clientId, agentId, scope, redirectUri, expiresAt, usedAt
  - OAuthRefreshToken: id, token (hashed), clientId, agentId, scope, expiresAt, revokedAt

- [ ] **Step 2: Implement OIDC discovery endpoint**
  - `GET /.well-known/openid-configuration`
  - Returns: issuer, authorization_endpoint, token_endpoint, userinfo_endpoint, jwks_uri, supported scopes, response types, grant types

- [ ] **Step 3: Implement JWKS endpoint**
  - `GET /oauth/jwks`
  - RSA or Ed25519 key pair for signing tokens
  - Key rotation support

- [ ] **Step 4: Implement authorization endpoint**
  - `GET /oauth/authorize` — handles authorization code flow
  - Validates client_id, redirect_uri, scope
  - Authenticates agent (via DID verification or API key)
  - Issues authorization code

- [ ] **Step 5: Implement token endpoint**
  - `POST /oauth/token` — exchanges code for tokens
  - Returns: access_token (JWT), id_token (JWT), refresh_token
  - JWT claims include: sub (agent DID), email, phone, capabilities, trust_score

- [ ] **Step 6: Implement userinfo endpoint**
  - `GET /oauth/userinfo` — returns agent identity details
  - Fields: sub, email, phone, did, org, name, capabilities, vault_access

- [ ] **Step 7: Write tests**
  - Unit: JWT signing and verification
  - Integration: full OIDC flow (authorize → code → token → userinfo)
  - Integration: scope restriction (request email scope only → get email only)
  - Integration: token refresh flow

**Acceptance criteria:** External applications can authenticate agents via standard OIDC flow. Agent identity tokens include full capability set.

**Git commit:** `feat(oauth): add OIDC provider for agent identity federation`

---

## Cross-Cutting: SDK, MCP, CLI, Docs Updates

### Task 13: Update All SDKs (E13)

**Files:**
- Modify: `node/src/resources/vault.ts`
- Create: `node/src/resources/vault-tokens.ts`
- Create: `node/src/resources/vault-policies.ts`
- Modify: `python/anima/resources/vault.py`
- Create: `python/anima/resources/vault_tokens.py`
- Create: `python/anima/resources/vault_policies.py`
- Modify: `go/vault.go`
- Create: `go/vault_tokens.go`
- Create: `go/vault_policies.go`

- [ ] **Step 1: Add vault token resources to Node SDK**
  - `client.vault.tokens.issue(params)` — issue ephemeral token
  - `client.vault.tokens.list()` — list active tokens
  - `client.vault.tokens.revoke(id)` — revoke token
  - `client.vault.tokens.refresh(id)` — extend TTL

- [ ] **Step 2: Add vault policy resources to Node SDK**
  - `client.vault.policies.list()` — list policies
  - `client.vault.policies.create(params)` — create policy
  - `client.vault.policies.update(id, params)` — update policy
  - `client.vault.policies.evaluate(params)` — dry-run evaluation

- [ ] **Step 3: Add vault sharing resources to Node SDK**
  - `client.vault.credentials.share(id, params)` — share credential
  - `client.vault.credentials.listShares(id)` — list shares
  - `client.vault.credentials.revokeShare(id, shareId)` — revoke share

- [ ] **Step 4: Add vault analytics resources to Node SDK**
  - `client.vault.analytics.riskScores()` — get risk scores
  - `client.vault.analytics.anomalies()` — get anomalies
  - `client.vault.analytics.behavior(agentId)` — get profile

- [ ] **Step 5: Mirror all additions in Python SDK (sync + async)**
- [ ] **Step 6: Mirror all additions in Go SDK**
- [ ] **Step 7: Update SDK READMEs with vault examples**
- [ ] **Step 8: Write SDK tests for all new resources**

**Acceptance criteria:** All three SDKs have complete vault coverage. READMEs document new features.

**Git commit:** `feat(sdks): add vault tokens, policies, sharing, and analytics to all SDKs`

---

### Task 14: Update MCP Servers (E14)

**Files:**
- Modify: `mcp-vault/src/tools/vault/index.ts`
- Modify: `mcp-vault/src/tools/security/index.ts`
- Modify: `mcp/src/tools/vault.ts` (monolith MCP)
- Modify: `mcp-core/src/config.ts`

- [ ] **Step 1: Add new vault MCP tools**
  - `vault_issue_token` — issue ephemeral scoped token
  - `vault_revoke_token` — revoke token
  - `vault_list_tokens` — list active tokens
  - `vault_use_credential` — use credential without seeing it (brokered access)
  - `vault_inject_env` — get credential as env vars
  - `vault_check_access` — check if agent can access a credential
  - `vault_request_step_up` — request elevated access
  - `vault_share_credential` — share credential
  - `vault_list_shared` — list shared credentials
  - `vault_risk_score` — get agent's risk score

- [ ] **Step 2: Update monolith MCP server**
  - Add all new tools to `mcp/src/tools/vault.ts`
  - Update tool count in README

- [ ] **Step 3: Update master key tool list**
  - Add `vault_issue_token`, `vault_share_credential` to MASTER_KEY_TOOLS if required

- [ ] **Step 4: Write tool registration tests**

**Acceptance criteria:** All new vault capabilities are accessible via MCP tools. Tool descriptions are clear and accurate.

**Git commit:** `feat(mcp): add vault tokens, injection, sharing, and analytics MCP tools`

---

### Task 15: Update CLI (E15)

**Files:**
- Modify: `cli/src/commands/vault.ts`
- Create: `cli/src/commands/vault-exec.ts` (from Task 8)
- Create: `cli/src/commands/vault-tokens.ts`
- Create: `cli/src/commands/vault-policies.ts`

- [ ] **Step 1: Add vault token commands**
  - `am vault tokens issue --scope read --ttl 15m`
  - `am vault tokens list`
  - `am vault tokens revoke <id>`

- [ ] **Step 2: Add vault policy commands**
  - `am vault policies list`
  - `am vault policies create --name <name> --rules <json>`
  - `am vault policies evaluate --credential <id> --action read`

- [ ] **Step 3: Add vault sharing commands**
  - `am vault share <credentialId> --with <agentId> --permissions read,use`
  - `am vault shares list <credentialId>`
  - `am vault shares revoke <credentialId> <shareId>`

- [ ] **Step 4: Add vault analytics commands**
  - `am vault risk-scores`
  - `am vault anomalies`

- [ ] **Step 5: Write CLI tests**

**Acceptance criteria:** All vault features accessible via CLI. Help text is complete and accurate.

**Git commit:** `feat(cli): add vault tokens, policies, sharing, and analytics commands`

---

### Task 16: Update Documentation & Skills (E16)

**Files:**
- Create: `docs/content/vault/overview.mdx`
- Create: `docs/content/vault/quickstart.mdx`
- Create: `docs/content/vault/secret-injection.mdx`
- Create: `docs/content/vault/policies.mdx`
- Create: `docs/content/vault/ephemeral-tokens.mdx`
- Create: `docs/content/vault/browser-autofill.mdx`
- Create: `docs/content/vault/cross-channel-analytics.mdx`
- Create: `docs/content/vault/identity-federation.mdx`
- Modify: `skill/SKILL.md`
- Create: `anima/apps/web/content/posts/introducing-anima-vault.mdx`
- Create: `llm.txt` files in relevant repos

- [ ] **Step 1: Write vault documentation (MDX)**
  - Overview: what vault is, why it matters, architecture diagram
  - Quickstart: store first credential, inject into CLI, use in agent
  - Secret injection: CLI, browser, proxy patterns
  - Policies: creating and managing access policies
  - Ephemeral tokens: issuing, scoping, revoking
  - Browser autofill: extension setup, autofill flow
  - Cross-channel analytics: risk scores, anomaly detection
  - Identity federation: OIDC setup, framework integration

- [ ] **Step 2: Update SKILL.md with new vault tools**
  - Add all new vault MCP tools to the tool reference table
  - Update tool count
  - Add vault category description

- [ ] **Step 3: Create llm.txt files**
  - `mcp-vault/llm.txt` — vault MCP server capabilities for LLMs
  - `anima/llm.txt` — update with vault platform description

- [ ] **Step 4: Write blog post: "Introducing Anima Vault"**
  - Problem: secrets in agent context
  - Solution: vault with injection patterns
  - Key features: per-agent encryption, ephemeral tokens, policy enforcement
  - Code examples
  - Call to action

- [ ] **Step 5: Create example agents using vault**
  - `examples/vault-browser-automation/` — agent that logs into websites
  - `examples/vault-api-integration/` — agent that uses API keys from vault
  - `examples/vault-multi-agent/` — agents sharing credentials

- [ ] **Step 6: Update ROADMAP.md with vault section**
- [ ] **Step 7: Update BUSINESS_PLAN.md with vault competitive analysis**

**Acceptance criteria:** Complete documentation covering all vault features. SKILL.md updated. Blog post ready. Examples working.

**Git commit:** `docs: add vault documentation, examples, blog post, and llm.txt files`

---

## Summary

| Task | Layer | Repos Affected | Estimated Effort |
|------|-------|---------------|-----------------|
| E1: Enable Feature Flag | Ship | anima/ | 4h |
| E2: Per-Agent Encryption | Ship | anima/ | 8h |
| E3: Cross-Module Integration | Ship | anima/ | 8h |
| E4: Credential Sharing | Ship | anima/ | 6h |
| E5: Ephemeral Scoped Credentials | Differentiate | anima/ | 12h |
| E6: Intent-Aware Policy Engine | Differentiate | anima/ | 10h |
| E7: Step-Up Authorization | Differentiate | anima/ | 8h |
| E8: CLI Credential Injection | Differentiate | cli/, anima/ | 6h |
| E9: Browser Autofill | Differentiate | anima/apps/extension/, anima/ | 12h |
| E10: Cross-Channel Analytics | Moat | anima/ | 12h |
| E11: Forensic Traceability | Moat | anima/ | 6h |
| E12: Identity Federation (OIDC) | Platform | anima/ | 16h |
| E13: Update All SDKs | Cross-cutting | node/, python/, go/ | 12h |
| E14: Update MCP Servers | Cross-cutting | mcp-vault/, mcp/, mcp-core/ | 6h |
| E15: Update CLI | Cross-cutting | cli/ | 6h |
| E16: Update Docs & Skills | Cross-cutting | docs/, skill/, anima/ | 10h |
| **Total** | | | **~142h** |

---

*Plan created: April 5, 2026*
