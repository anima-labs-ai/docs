# Vault Identity Platform — Design Specification

> **Date:** April 5, 2026
> **Author:** Diyan Bogdanov
> **Status:** Active
> **Companion Documents:** [Business Plan](../../../anima/BUSINESS_PLAN.md) · [Technical Plan](../../../anima/TECHNICAL_PLAN.md) · [Vault Business Plan](./2026-04-05-vault-business-plan.md)

---

## 1. Executive Summary

Transform Anima's credential vault from a Bitwarden-backed CRUD store into a **market-leading agent secrets platform** with four strategic layers:

1. **Ship What's Built** — enable the feature flag, fix integration gaps, add per-agent encryption
2. **Differentiate** — ephemeral scoped credentials, intent-aware policy enforcement, step-up authorization
3. **Build the Moat** — cross-channel identity analytics, device attestation, agent-to-agent credential delegation
4. **Platform Endgame** — identity federation ("Sign in with Anima"), framework SDK plugins, full secrets elimination

**Core design principle:** The LLM (brain of each agent) must NEVER have direct access to secrets. Agents use secrets through four injection patterns: proxy-based injection, environment variable injection, brokered/delegated access, and ephemeral token issuance.

---

## 2. Architecture Overview

### 2.1 Current State

```
Agent (LLM) → MCP Tool Call → mcp-vault → Anima REST API → Vault Provider → Vaultwarden
                                                                    ↓
                                                          vault_get_credential
                                                          → returns plaintext to agent context ❌
```

**Problem:** Today, `vault_get_credential` returns the secret value directly into the MCP tool response, which means it enters the LLM's context window. This is the fundamental issue every competitor is racing to solve.

### 2.2 Target State

```
┌──────────────────────────────────────────────────────────────┐
│                    Anima Vault Platform                        │
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │ Credential Store │  │ Token Issuer     │  │ Policy      │ │
│  │                  │  │                  │  │ Engine      │ │
│  │ • Per-org vaults │  │ • Ephemeral      │  │             │ │
│  │ • Per-agent keys │  │   scoped tokens  │  │ • Allow     │ │
│  │ • 7 cred types   │  │ • TTL + scope    │  │ • Deny      │ │
│  │ • Audit trail    │  │ • Task binding   │  │ • Observe   │ │
│  │ • Rotation       │  │ • Revocation     │  │ • Step-up   │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬──────┘ │
│           │                     │                    │        │
│  ┌────────┴─────────────────────┴────────────────────┴──────┐ │
│  │              Secret Injection Layer                       │ │
│  │                                                           │ │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐  │ │
│  │  │ CLI Inject   │ │ Browser      │ │ Proxy Inject      │  │ │
│  │  │ (env vars)   │ │ Autofill     │ │ (HTTP header      │  │ │
│  │  │              │ │ (Chrome ext) │ │  injection)        │  │ │
│  │  └─────────────┘ └──────────────┘ └───────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Cross-Channel Analytics                       │ │
│  │                                                           │ │
│  │  Email patterns + Call behavior + Spend patterns           │ │
│  │  + Vault access → Composite risk score per agent           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Identity Federation                           │ │
│  │                                                           │ │
│  │  OIDC Provider · "Sign in with Anima" · Framework plugins  │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Secret Injection Patterns (LLM Never Sees Secret)

| Pattern | How It Works | Use Case | Implementation |
|---------|-------------|----------|----------------|
| **CLI Env Injection** | `am vault exec --credential <id> -- <command>` injects secrets as env vars into child process | CI/CD, scripts, local dev | CLI wraps child process with injected env |
| **Browser Autofill** | Chrome extension fills login forms using vault credentials, agent never sees values | Web automation, SaaS login | Chrome extension + content scripts |
| **Proxy Injection** | HTTP proxy intercepts requests and injects auth headers before forwarding | API calls, webhooks | Sidecar proxy or gateway mode |
| **Brokered Access** | Agent expresses intent ("log in to GitHub"), vault service executes with credentials | Complex multi-step workflows | MCP tools with `vault_use_credential` |

---

## 3. Data Model

### 3.1 New Prisma Models

```prisma
// Ephemeral scoped credential tokens
model VaultToken {
  id              String    @id @default(cuid())
  orgId           String
  agentId         String
  credentialId    String?   // null for org-wide tokens

  // Scope binding
  taskId          String?   // bound to specific task
  scope           String[]  // allowed actions: ["read", "inject", "rotate"]
  allowedTools    String[]  // MCP tools this token can access

  // Lifecycle
  token           String    @unique // SHA-256 hashed
  tokenPrefix     String    // first 8 chars for identification
  expiresAt       DateTime
  revokedAt       DateTime?
  revokedBy       String?   // userId or "system" or "policy"

  // Context
  issuedBy        String    // userId who authorized
  delegationChain Json?     // cryptographic chain: human → agent → action
  deviceFingerprint String? // bound to runtime environment

  // Audit
  lastUsedAt      DateTime?
  useCount        Int       @default(0)
  maxUses         Int?      // null = unlimited within TTL

  createdAt       DateTime  @default(now())

  agent           Agent     @relation(fields: [agentId], references: [id], onDelete: Cascade)
  org             Organization @relation(fields: [orgId], references: [id], onDelete: Cascade)

  @@index([orgId])
  @@index([agentId])
  @@index([token])
  @@index([expiresAt])
}

// Vault access policies
model VaultPolicy {
  id              String    @id @default(cuid())
  orgId           String
  name            String
  description     String?

  // Policy rules (evaluated per tool call)
  rules           Json      // Array of VaultPolicyRule
  // Rule shape: {
  //   action: "allow" | "deny" | "observe" | "step_up",
  //   credentialTypes: ["login", "api_key", ...],
  //   conditions: {
  //     timeOfDay?: { start: "09:00", end: "17:00" },
  //     maxUsesPerHour?: number,
  //     requireApproval?: boolean,
  //     allowedAgents?: string[],
  //     allowedTasks?: string[],
  //     riskScoreBelow?: number,
  //   }
  // }

  priority        Int       @default(0) // higher = evaluated first
  isDefault       Boolean   @default(false)

  // Versioning
  version         Int       @default(1)
  previousVersion String?   // link to previous policy version

  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  createdBy       String

  org             Organization @relation(fields: [orgId], references: [id], onDelete: Cascade)

  @@unique([orgId, name])
  @@index([orgId])
}

// Step-up authorization requests
model VaultStepUp {
  id              String    @id @default(cuid())
  orgId           String
  agentId         String
  credentialId    String
  tokenId         String?   // VaultToken that triggered step-up

  // Request context
  action          String    // what the agent wants to do
  reason          String?   // why step-up was triggered
  policyId        String    // which policy triggered it

  // Resolution
  status          String    @default("pending") // pending, approved, denied, expired
  resolvedBy      String?   // userId who approved/denied
  resolvedAt      DateTime?
  expiresAt       DateTime  // auto-deny after this time

  // Notification
  notificationChannel String? // email, sms, push
  notificationSentAt  DateTime?

  createdAt       DateTime  @default(now())

  agent           Agent     @relation(fields: [agentId], references: [id], onDelete: Cascade)
  org             Organization @relation(fields: [orgId], references: [id], onDelete: Cascade)

  @@index([orgId, status])
  @@index([agentId])
}

// Cross-channel behavioral profile for analytics
model AgentBehaviorProfile {
  id              String    @id @default(cuid())
  orgId           String
  agentId         String    @unique

  // Behavioral vectors (pgvector embeddings)
  emailPattern    Unsupported("vector(256)")?
  phonePattern    Unsupported("vector(256)")?
  spendPattern    Unsupported("vector(256)")?
  vaultPattern    Unsupported("vector(256)")?
  compositePattern Unsupported("vector(256)")?

  // Risk scoring
  riskScore       Float     @default(0) // 0-100
  riskFactors     Json?     // breakdown of contributing factors
  lastAnomalyAt   DateTime?
  anomalyCount    Int       @default(0)

  // Stats
  emailsLast24h   Int       @default(0)
  callsLast24h    Int       @default(0)
  spendsLast24h   Int       @default(0)
  vaultAccessLast24h Int    @default(0)

  updatedAt       DateTime  @updatedAt

  agent           Agent     @relation(fields: [agentId], references: [id], onDelete: Cascade)
  org             Organization @relation(fields: [orgId], references: [id], onDelete: Cascade)

  @@index([orgId])
  @@index([riskScore])
}
```

### 3.2 Credential Sharing Model

```prisma
// Fine-grained credential sharing within an org
model CredentialShare {
  id              String    @id @default(cuid())
  orgId           String
  credentialId    String    // Vaultwarden item ID

  // Who can access
  sharedWithType  String    // "agent" | "member" | "pod"
  sharedWithId    String    // agentId, userId, or podId

  // What they can do
  permissions     String[]  // ["read", "use", "rotate"]

  // Constraints
  expiresAt       DateTime?
  maxUses         Int?

  createdAt       DateTime  @default(now())
  createdBy       String

  org             Organization @relation(fields: [orgId], references: [id], onDelete: Cascade)

  @@unique([orgId, credentialId, sharedWithType, sharedWithId])
  @@index([orgId])
  @@index([credentialId])
  @@index([sharedWithId])
}
```

---

## 4. API Design

### 4.1 New Vault Endpoints

#### Token Management
```
POST   /vault/tokens              — Issue ephemeral scoped token
GET    /vault/tokens              — List active tokens
GET    /vault/tokens/:id          — Get token details
DELETE /vault/tokens/:id          — Revoke token
POST   /vault/tokens/:id/refresh  — Extend token TTL (if policy allows)
```

#### Policy Management
```
GET    /vault/policies            — List org policies
POST   /vault/policies            — Create policy
GET    /vault/policies/:id        — Get policy
PUT    /vault/policies/:id        — Update policy (creates new version)
DELETE /vault/policies/:id        — Delete policy
POST   /vault/policies/evaluate   — Dry-run policy evaluation
```

#### Step-Up Authorization
```
GET    /vault/step-ups            — List pending step-ups
POST   /vault/step-ups/:id/approve — Approve step-up
POST   /vault/step-ups/:id/deny    — Deny step-up
```

#### Credential Sharing
```
POST   /vault/credentials/:id/share    — Share credential
GET    /vault/credentials/:id/shares   — List shares
DELETE /vault/credentials/:id/shares/:shareId — Revoke share
```

#### Secret Injection
```
POST   /vault/inject/env         — Get credential as env var map (for CLI)
POST   /vault/inject/header      — Get credential as HTTP headers (for proxy)
POST   /vault/inject/browser     — Get credential for browser autofill (for extension)
```

#### Cross-Channel Analytics
```
GET    /vault/analytics/risk-scores     — Agent risk scores
GET    /vault/analytics/anomalies       — Cross-channel anomalies
GET    /vault/analytics/behavior/:agentId — Agent behavioral profile
```

#### Identity Federation
```
GET    /.well-known/openid-configuration — OIDC discovery
GET    /oauth/authorize                   — Authorization endpoint
POST   /oauth/token                       — Token endpoint
GET    /oauth/userinfo                    — UserInfo endpoint
GET    /oauth/jwks                        — JSON Web Key Set
```

### 4.2 New MCP Tools

```
// Ephemeral tokens
vault_issue_token        — Issue scoped token for current task
vault_revoke_token       — Revoke a specific token
vault_list_tokens        — List active tokens for agent

// Secret injection (LLM never sees secret)
vault_use_credential     — Use credential without seeing it (brokered access)
vault_inject_env         — Inject credential as env vars into subprocess
vault_inject_header      — Inject credential as HTTP auth header

// Policy
vault_check_access       — Check if agent can access a credential
vault_request_step_up    — Request elevated access for sensitive credential

// Sharing
vault_share_credential   — Share credential with another agent/member
vault_list_shared        — List credentials shared with me

// Analytics
vault_risk_score         — Get agent's current risk score
```

---

## 5. Security Architecture

### 5.1 Encryption Layers

| Layer | Mechanism | Key Management |
|-------|-----------|---------------|
| **Transport** | TLS 1.3 | Let's Encrypt auto-renewal |
| **At-rest (Vaultwarden)** | AES-256-GCM | Vaultwarden master password |
| **At-rest (DB fields)** | AES-256-GCM with envelope encryption | Per-org KEK (HKDF-SHA256) → DEK → field |
| **Per-agent isolation** | Agent-specific DEK derived from org KEK + agentId | HKDF(orgKEK, agentId + salt) |
| **Token binding** | HMAC-SHA256 | Derived from agent DEK + taskId |
| **Audit log integrity** | HMAC-SHA256 chain | Previous log entry hash included |

### 5.2 Per-Agent Encryption (New)

```typescript
// Key derivation hierarchy
OrgRootKey (env var)
  └─ OrgKEK = HKDF-SHA256(OrgRootKey, orgId + kekVersion)
       └─ OrgDEK = AES-256-GCM.wrap(OrgKEK, randomDEK) // stored in DB
            └─ AgentDEK = HKDF-SHA256(OrgDEK, agentId + "vault-agent-dek")
                 └─ CredentialKey = HKDF-SHA256(AgentDEK, credentialId + "cred-enc")
```

Each agent's credentials are encrypted with a key derived from the agent's identity. Even if Vaultwarden is compromised, individual agent vaults remain isolated.

### 5.3 Delegation Chain

Every vault action carries a cryptographic delegation chain:

```json
{
  "chain": [
    {
      "principal": "user:clerk_user_123",
      "action": "delegate",
      "scope": ["vault.read", "vault.use"],
      "timestamp": "2026-04-05T10:00:00Z",
      "signature": "ed25519_sig_..."
    },
    {
      "principal": "agent:did:anima:org123:agent456",
      "action": "request",
      "scope": ["vault.use"],
      "credentialId": "cred_789",
      "taskId": "task_abc",
      "timestamp": "2026-04-05T10:00:05Z",
      "signature": "ed25519_sig_..."
    }
  ]
}
```

### 5.4 Forensic Traceability

Every vault access records:
- **Who**: delegation chain (human → agent → sub-agent)
- **What**: credential accessed, action performed
- **When**: timestamp with nanosecond precision
- **Where**: device fingerprint, IP, runtime environment
- **Why**: task context, originating prompt hash (not the prompt itself)
- **How**: injection method used (env, browser, proxy, brokered)

---

## 6. Browser Extension Architecture

### 6.1 Autofill Flow

```
1. Agent navigates to login page (via browser automation)
2. Agent calls vault_use_credential(credentialId, "browser_autofill")
3. Policy engine evaluates → allow / deny / step_up
4. If allowed: API sends credential to Chrome extension via secure channel
5. Extension fills form fields (username, password)
6. Extension submits TOTP if required
7. Extension confirms success/failure back to API
8. Audit log records: credential used, site URL, result
9. Agent receives success/failure (never the credential values)
```

### 6.2 Extension Security

- Extension communicates with API via authenticated WebSocket (not HTTP, to avoid request interception)
- Credentials are held in extension's `chrome.storage.session` (cleared on browser close)
- Extension never exposes credentials to page JavaScript (uses isolated content script world)
- Each autofill operation requires a valid, non-expired VaultToken
- Human-in-the-loop: step-up auth can require human approval before autofill

---

## 7. CLI Credential Injection

### 7.1 `am vault exec` Command

```bash
# Inject credentials as env vars and run a command
am vault exec --credential cred_123 -- node script.js

# Multiple credentials
am vault exec --credential cred_123 --credential cred_456 -- ./deploy.sh

# With custom env var mapping
am vault exec --credential cred_123 --as DB_PASSWORD -- psql

# With scoped token (short-lived)
am vault exec --token vtk_abc123 -- curl https://api.example.com
```

### 7.2 Injection Mechanism

```
1. CLI authenticates to Anima API
2. Requests credential injection: POST /vault/inject/env
3. Policy engine evaluates
4. API returns env var map (encrypted in transit)
5. CLI spawns child process with injected env vars
6. Child process uses env vars normally
7. On exit: env vars are destroyed (never written to disk)
8. Audit log records: credential injected, process PID, duration, exit code
```

---

## 8. Cross-Channel Analytics

### 8.1 Behavioral Profile Construction

```
┌──────────────────────────────────────────────────────┐
│            Cross-Channel Analytics Worker              │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Email    │  │ Phone    │  │ Vault│ │
│  │ Events   │  │ Events   │  │Events│ │
│  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       │              │           │     │
│       └──────────────┴───────────┘     │
│                         │                             │
│              ┌──────────┴──────────┐                  │
│              │ Feature Extraction  │                  │
│              │ + pgvector Embed    │                  │
│              └──────────┬──────────┘                  │
│                         │                             │
│              ┌──────────┴──────────┐                  │
│              │ Anomaly Detection   │                  │
│              │ (z-score + ML)      │                  │
│              └──────────┬──────────┘                  │
│                         │                             │
│              ┌──────────┴──────────┐                  │
│              │ Risk Score Update   │                  │
│              │ → Policy Trigger    │                  │
│              └─────────────────────┘                  │
└──────────────────────────────────────────────────────┘
```

### 8.2 Anomaly Examples

| Scenario | Channels Involved | Detection |
|----------|------------------|-----------|
| Agent sends 50 emails then accesses prod DB credentials | Email + Vault | Volume spike + credential type escalation |
| Agent makes calls to unusual numbers and accesses API keys | Phone + Vault | Geographic anomaly + credential access |
| Agent accesses 10 credentials in 1 minute (normal is 2/hour) | Vault only | Rate anomaly |

---

## 9. Identity Federation ("Sign in with Anima")

### 9.1 OIDC Provider Architecture

```
External Agent Framework (LangChain, CrewAI, AutoGen)
    │
    ├── 1. Redirect to /oauth/authorize
    │      (client_id, scope, redirect_uri)
    │
    ├── 2. Anima authenticates agent identity
    │      (DID verification, org membership)
    │
    ├── 3. Issue authorization code
    │      (redirect to callback URL)
    │
    ├── 4. Exchange code for tokens
    │      POST /oauth/token
    │      → { access_token, id_token, refresh_token }
    │
    └── 5. Access Anima resources
           GET /oauth/userinfo
           → { sub, email, phone, did, org, capabilities }
```

### 9.2 Agent Identity Token Claims

```json
{
  "sub": "did:anima:org123:agent456",
  "iss": "https://api.useanima.sh",
  "aud": "client_id_of_requesting_framework",
  "exp": 1712345678,
  "iat": 1712342078,
  "org": "org_123",
  "name": "Sales Agent",
  "email": "sales@company.useanima.sh",
  "phone": "+15551234567",
  "capabilities": ["email", "phone", "vault"],
  "trust_score": 0.95,
  "vault_access": true,
  "delegation_chain": "base64_encoded_chain"
}
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Encryption: key derivation, per-agent DEK generation, credential encryption/decryption
- Policy engine: rule evaluation, condition matching, priority ordering
- Token lifecycle: issuance, validation, expiration, revocation
- Delegation chain: construction, verification, serialization

### 10.2 Integration Tests

- Vault CRUD with per-agent encryption
- Token-based credential access (happy path + expired + revoked)
- Policy enforcement (allow, deny, observe, step-up)
- Credential sharing (share, access, revoke)
- Step-up authorization flow (request → notify → approve/deny)
- Cross-channel analytics worker (event ingestion → risk score update)

### 10.3 E2E Tests

- Full lifecycle: create agent → provision vault → store credential → issue token → use credential via injection → audit trail verified
- Browser autofill: store login → navigate to site → autofill → verify login success
- CLI injection: store secret → `am vault exec` → verify env var present in child process
- Step-up flow: agent requests sensitive credential → human receives notification → approves → agent gets access
- Cross-channel anomaly: simulate suspicious pattern → verify risk score increase → verify policy triggers

---

*Document created: April 5, 2026*
