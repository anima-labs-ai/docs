# Phase C — Agent Identity & Commerce Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the identity protocol moat. DID/VC, agent registry, wallet with x402, OAuth vault, multi-tenancy, A2A. Transform Anima from a product into a standard.

**Architecture:** Multi-repo at `/Users/diyanbogdanov/projects/agenticmail/`. Core platform at `anima/` (packages: `agent-identity`, `protocols`, `contracts`, `db`). SDKs at `python/` and `node/`, toolkit at `toolkit/`, skill at `skill/`, MCP at `mcp/`, CLI at `cli/`, docs at `docs/`.

**Tech Stack:** TypeScript (Bun), Python, Hono, oRPC, Prisma, Ed25519/P-256 crypto, JWT-VC, WebSockets

**Spec:** `docs/superpowers/specs/2026-03-28-anima-platform-roadmap-design.md` (Phase C section)

**Depends on:** Phase A + B complete (verified)

---

## Task 1: DID Method + DID Documents (C1 — Part 1)

**Files:**
- Modify: `anima/packages/agent-identity/src/index.ts`
- Create: `anima/packages/agent-identity/src/did.ts`
- Create: `anima/packages/agent-identity/src/crypto.ts`
- Modify: `anima/packages/db/prisma/schema.prisma` (add DID fields to Agent)
- Create: `anima/packages/contracts/src/contracts/identity.ts`
- Create: `anima/packages/contracts/src/schemas/identity.ts`
- Modify: `anima/packages/contracts/src/contracts/index.ts`
- Modify: `anima/apps/api/src/router.ts` (add identity routes)

- [ ] **Step 1: Add crypto utilities for DID key management**

Create `anima/packages/agent-identity/src/crypto.ts`:
- `generateKeyPair(algorithm: 'Ed25519' | 'P-256')` → `{ publicKey, privateKey }` using Node.js `crypto` module
- `signPayload(privateKey, payload)` → signature string
- `verifySignature(publicKey, payload, signature)` → boolean
- Key serialization: JWK format for DID Documents, base58btc for multibase encoding
- Key types: Ed25519VerificationKey2020, JsonWebKey2020

- [ ] **Step 2: Implement DID Document generation**

Create `anima/packages/agent-identity/src/did.ts`:
- DID format: `did:anima:<orgId>:<agentId>`
- `createDidDocument(agent, publicKey, services)` → W3C DID Document (JSON-LD)
- DID Document fields: `@context`, `id`, `controller`, `verificationMethod`, `authentication`, `assertionMethod`, `service`
- Service endpoints: email inbox, phone, webhook URL, MCP endpoint
- `resolveDidDocument(did)` → DID Document or null
- `deactivateDidDocument(did)` → marks DID as deactivated

- [ ] **Step 3: Add DID fields to Prisma schema**

Modify `anima/packages/db/prisma/schema.prisma`:
- Add to `Agent` model: `did String? @unique`, `publicKey String?`, `privateKeyEnc String?` (encrypted), `didDocument Json?`, `didDeactivated Boolean @default(false)`
- Create migration

- [ ] **Step 4: Create identity oRPC contracts and schemas**

Create `anima/packages/contracts/src/schemas/identity.ts`:
- `DidDocumentOutput` — W3C DID Document shape
- `ResolveDidInput` — `{ did: string }`

Create `anima/packages/contracts/src/contracts/identity.ts`:
- `resolveDid`: GET `/identity/did/:did` → DidDocumentOutput
- `getAgentDid`: GET `/agents/:agentId/did` → DidDocumentOutput
- `rotateKeys`: POST `/agents/:agentId/did/rotate` → DidDocumentOutput

Export from `contracts/index.ts`

- [ ] **Step 5: Add DID API routes**

Add to `anima/apps/api/src/router.ts`:
- `GET /identity/did/:did` — public DID resolution (no auth required)
- `GET /agents/:agentId/did` — get agent's DID Document (auth required)
- `POST /agents/:agentId/did/rotate` — rotate agent's keys
- Auto-create DID + keypair when agent is created (modify agent creation handler)

---

## Task 2: Verifiable Credentials (C1 — Part 2)

**Files:**
- Create: `anima/packages/agent-identity/src/vc.ts`
- Create: `anima/packages/agent-identity/src/revocation.ts`
- Modify: `anima/packages/db/prisma/schema.prisma` (VC storage)
- Modify: `anima/packages/contracts/src/schemas/identity.ts` (VC schemas)
- Modify: `anima/packages/contracts/src/contracts/identity.ts` (VC routes)
- Modify: `anima/apps/api/src/router.ts` (VC handlers)

- [ ] **Step 1: Implement VC issuance**

Create `anima/packages/agent-identity/src/vc.ts`:
- W3C VC Data Model 2.0 format
- JWT-VC encoding using Ed25519 issuer key
- Issuer DID: `did:anima:issuer`
- Credential types: `AnimaEmailVerified`, `AnimaPhoneVerified`, `AnimaAddressVerified`, `AnimaKYBCompleted`, `AnimaPaymentCapable`, `AnimaOwnerBound`, `AnimaTrustScore`
- `issueCredential(type, subject, claims, issuerKey)` → JWT-VC string
- `verifyCredential(jwtVc, issuerPublicKey)` → `{ valid, credential, errors }`
- `decodeCredential(jwtVc)` → decoded VC payload (no verification)

- [ ] **Step 2: Implement revocation list**

Create `anima/packages/agent-identity/src/revocation.ts`:
- StatusList2021 format (W3C standard for VC revocation)
- `createRevocationList(issuerId)` → compressed bitstring
- `revokeCredential(listId, credentialIndex)` → updated list
- `isRevoked(listId, credentialIndex)` → boolean
- Store revocation lists in database

- [ ] **Step 3: Add VC Prisma models**

Add to schema.prisma:
```
model VerifiableCredential {
  id              String   @id @default(cuid())
  agentId         String   @map("agent_id")
  orgId           String   @map("org_id")
  type            String   // AnimaEmailVerified, etc.
  jwtVc           String   @map("jwt_vc") @db.Text
  issuerDid       String   @map("issuer_did")
  subjectDid      String   @map("subject_did")
  issuedAt        DateTime @map("issued_at")
  expiresAt       DateTime? @map("expires_at")
  revoked         Boolean  @default(false)
  revokedAt       DateTime? @map("revoked_at")
  revocationIndex Int?     @map("revocation_index")
  metadata        Json?
  agent           Agent    @relation(...)
  organization    Organization @relation(...)
}
```

- [ ] **Step 4: Add VC contracts and API routes**

Contracts:
- `listCredentials`: GET `/agents/:agentId/credentials` → VC[]
- `verifyCredential`: POST `/identity/verify` → verification result
- `revokeCredential`: POST `/agents/:agentId/credentials/:vcId/revoke`

API routes: implement handlers with auto-issuance triggers:
- When email is verified → auto-issue `AnimaEmailVerified`
- When phone is verified → auto-issue `AnimaPhoneVerified`
- When address is validated → auto-issue `AnimaAddressVerified`
- When KYB completes → auto-issue `AnimaKYBCompleted`
- When card is created → auto-issue `AnimaPaymentCapable`

---

## Task 3: Agent Cards + .well-known (C1 — Part 3)

**Files:**
- Create: `anima/packages/agent-identity/src/agent-card.ts`
- Modify: `anima/apps/api/src/router.ts` (agent card routes)
- Modify: `anima/packages/contracts/src/contracts/identity.ts`

- [ ] **Step 1: Implement Agent Card generation**

Create `anima/packages/agent-identity/src/agent-card.ts`:
- A2A Agent Card format (Google spec)
- `generateAgentCard(agent, credentials, capabilities)` → Agent Card JSON
- Auto-populated from agent config: name, description, DID, capabilities, verification level, trust score, contact info
- Capabilities auto-detected: email (has EmailIdentity?), phone (has PhoneIdentity?), cards (has CardIdentity?), vault (has VaultIdentity?), address (has AddressIdentity?)

- [ ] **Step 2: Add well-known and card API routes**

Routes:
- `GET /.well-known/agent.json` — returns Agent Card for the agent matching the request hostname
- `GET /v1/agents/:agentId/card` — returns Agent Card by agent ID (auth required)
- `GET /v1/registry/agents/:did/card` — returns Agent Card by DID (public)

---

## Task 4: Agent Registry & Discovery (C2)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma` (RegistryEntry model)
- Create: `anima/packages/contracts/src/contracts/registry.ts`
- Create: `anima/packages/contracts/src/schemas/registry.ts`
- Modify: `anima/apps/api/src/router.ts` (registry routes)

- [ ] **Step 1: Create RegistryEntry Prisma model**

Add to schema.prisma:
```
model RegistryEntry {
  id           String   @id @default(cuid())
  did          String   @unique
  agentId      String   @map("agent_id")
  orgId        String   @map("org_id")
  public       Boolean  @default(false)
  name         String
  description  String?
  agentCard    Json     @map("agent_card")
  trustScore   Int      @default(20) @map("trust_score")
  kyaLevel     String   @default("BASIC") @map("kya_level")
  capabilities String[]
  tags         String[]
  verified     Boolean  @default(false)
  verifiedAt   DateTime? @map("verified_at")
  listedAt     DateTime @default(now()) @map("listed_at")
  updatedAt    DateTime @updatedAt @map("updated_at")
  agent        Agent    @relation(...)
  organization Organization @relation(...)
}
```

- [ ] **Step 2: Create registry contracts and schemas**

Schemas: `RegisterAgentInput`, `RegistrySearchInput` (capability, trust_min, tags, kya_level, cursor, limit), `RegistryEntryOutput`, `RegistrySearchOutput`

Contract routes:
- `POST /registry/agents` — register
- `GET /registry/agents/search` — search
- `GET /registry/agents/:did` — lookup
- `PUT /registry/agents/:did` — update
- `DELETE /registry/agents/:did` — unlist

- [ ] **Step 3: Implement registry API handlers**

Full CRUD + search with:
- Full-text search on name/description
- Filter by capabilities, trust_min, kya_level, tags
- Pagination (cursor-based)
- Minimum trust score to list (configurable, default 20)
- Auto-update agent card when agent config changes
- Auto-delist when agent is deleted/deactivated

---

## Task 5: Agent Wallet + x402 + AP2 (C3)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma` (Wallet model)
- Create: `anima/packages/contracts/src/contracts/wallet.ts`
- Create: `anima/packages/contracts/src/schemas/wallet.ts`
- Modify: `anima/apps/api/src/router.ts` (wallet routes)

- [ ] **Step 1: Create Wallet Prisma model**

Add Wallet model with: id, agentId, orgId, did, balance (Decimal), currency, dailyLimit, monthlyLimit, totalSpent, spentToday, spentThisMonth, status (ACTIVE/FROZEN/SUSPENDED), metadata, timestamps.
Add relation to Agent (one-to-one).

- [ ] **Step 2: Create wallet contracts and schemas**

Schemas: `CreateWalletInput`, `WalletOutput`, `PaymentInput` (amount, currency, merchant, protocol preference), `PaymentOutput`, `WalletTransactionsInput/Output`

Contract routes:
- `POST /agents/:agentId/wallet` — create
- `GET /agents/:agentId/wallet` — get balance + status
- `PUT /agents/:agentId/wallet` — update limits
- `POST /agents/:agentId/wallet/pay` — unified pay
- `POST /agents/:agentId/wallet/x402-fetch` — x402 HTTP fetch
- `GET /agents/:agentId/wallet/transactions` — unified transaction history
- `POST /agents/:agentId/wallet/freeze` / `unfreeze`

- [ ] **Step 3: Implement wallet API with protocol router**

Wallet handlers with:
- Budget guards: per-request, daily, monthly limits
- Protocol auto-selection: x402 → AP2 → Visa TAP → Mastercard VI → card fallback
- Surface existing `@anima/protocols` router through the wallet API
- x402 fetch: intercept 402 responses, pay with wallet, retry request
- Transaction logging for all protocols
- Daily/monthly spend counter reset (scheduled job or on-read calculation)

---

## Task 6: OAuth Token Vault — Core (C4a)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma` (new credential type fields)
- Modify: `anima/apps/api/src/router.ts` (vault enhancements)
- Create: `anima/apps/api/src/workers/oauth-refresh-worker.ts`

- [ ] **Step 1: Extend vault for new credential types**

Add to existing vault schema/API:
- `oauth_token` type: accessToken, refreshToken, tokenEndpoint, clientId, clientSecret, scopes[], expiresAt, autoRefresh
- `api_key` type: key, prefix, rateLimit, expiresAt, scopes[]
- `certificate` type: format (pem/p12/jks), certificate, privateKey, chain[], expiresAt
- Modify existing credential store/get endpoints to support new types

- [ ] **Step 2: Implement OAuth auto-refresh worker**

Create background worker:
- Scan for `oauth_token` credentials expiring within 5 minutes
- Refresh using stored refresh_token + token_endpoint + client credentials
- Update stored access_token and expiry
- On failure: flag as `needs_reauth`, emit WebSocket event, webhook notification
- Support token rotation (new refresh_token replaces old)
- Run on interval (every 60 seconds)

- [ ] **Step 3: Add credential audit trail**

Add to schema:
```
model CredentialAuditLog {
  id           String   @id @default(cuid())
  credentialId String   @map("credential_id")
  agentId      String   @map("agent_id")
  orgId        String   @map("org_id")
  action       String   // access, refresh, store, delete, delegate, revoke
  actor        String   // agentId or system
  metadata     Json?
  createdAt    DateTime @default(now()) @map("created_at")
}
```

API: `GET /vault/audit?credentialId=X&since=Y` — queryable audit log

---

## Task 7: Multi-Tenancy Pods (C5)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma` (Pod model, podId on core models)
- Create: `anima/packages/contracts/src/contracts/pod.ts`
- Create: `anima/packages/contracts/src/schemas/pod.ts`
- Modify: `anima/apps/api/src/router.ts` (pod routes, pod-scoped auth middleware)

- [ ] **Step 1: Create Pod Prisma model and add podId to core models**

Pod model: id, orgId, name, slug (unique within org), status, limits (Json), metadata, timestamps.
Add optional `podId` to: Agent, Message, CardIdentity, PhoneIdentity, VaultIdentity, AddressIdentity, Webhook.
Create migration.

- [ ] **Step 2: Create pod contracts and API**

Contract routes: CRUD for pods, pod key generation, pod usage
Implement pod-scoped auth: `pk_` prefixed API keys resolve to pod context, all queries filter by podId.
Backward compatible: existing `ak_` keys work as before (org-level, no pod filter).

- [ ] **Step 3: Pod-scoped queries and isolation**

Modify all list/get handlers to filter by podId when present in auth context.
Cross-pod access returns 403.
Cascade delete: deleting a pod removes all scoped resources.

---

## Task 8: A2A Protocol Support (C6)

**Files:**
- Create: `anima/packages/a2a/src/server.ts`
- Create: `anima/packages/a2a/src/client.ts`
- Create: `anima/packages/a2a/src/types.ts`
- Modify: `anima/apps/api/src/router.ts` (A2A endpoint)

- [ ] **Step 1: Implement A2A types and task lifecycle**

Types: A2A Task (id, status, input, output, history), TaskStatus enum (submitted, working, input_required, completed, failed, canceled).
A2A Agent Card format (already done in Task 3).

- [ ] **Step 2: Implement A2A server (receiving tasks)**

Server endpoint: `POST /v1/agents/:agentId/a2a/tasks`
Task lifecycle: submit → work → complete/fail
SSE streaming for long-running tasks
DID-based sender authentication
Trust score gate: configurable minimum to accept tasks

- [ ] **Step 3: Implement A2A client (sending tasks)**

Client methods:
- `discover(agentUrl)` — fetch Agent Card
- `sendTask(agentUrl, task)` — send task
- `streamTask(agentUrl, task)` — stream updates
- Request signing with agent's private key
- Response verification via remote agent's DID

---

## Task 9: Identity/Registry/Wallet SDK + MCP + CLI (C1-C5 surface)

**Files:**
- Modify: `node/src/` (new resources: identity, registry, wallet, pods)
- Modify: `python/src/anima/` (new resources: identity, registry, wallet, pods)
- Modify: `mcp/src/tools/` (new tool groups: identity, registry, wallet, pod)
- Modify: `cli/src/commands/` (new command groups)
- Modify: `toolkit/` (expand all framework integrations)
- Modify: `skill/SKILL.md` (add new capabilities)

- [ ] **Step 1: Add identity/registry/wallet/pod resources to Node SDK**
- [ ] **Step 2: Add identity/registry/wallet/pod resources to Python SDK**
- [ ] **Step 3: Add identity/registry/wallet/pod MCP tools**
- [ ] **Step 4: Add identity/registry/wallet/pod CLI commands**
- [ ] **Step 5: Update toolkit integrations and skill**

---

## Task 10: A2A SDK + MCP + CLI (C6 surface)

**Files:**
- Modify: `node/src/` (a2a resource)
- Modify: `python/src/anima/` (a2a resource)
- Modify: `mcp/src/tools/` (a2a tools)
- Modify: `cli/src/commands/` (a2a commands)

- [ ] **Step 1: Add A2A resource to Node SDK**
- [ ] **Step 2: Add A2A resource to Python SDK**
- [ ] **Step 3: Add A2A MCP tools and CLI commands**

---

## Execution Strategy

**Parallel tracks:**
- Track 1 (Identity): Tasks 1 → 2 → 3 (sequential, C1 builds on itself)
- Track 2 (Registry): Task 4 (depends on Task 1 DID)
- Track 3 (Wallet): Task 5 (independent of identity)
- Track 4 (OAuth Vault): Task 6 (independent)
- Track 5 (Pods): Task 7 (independent)

**Then sequential:**
- Task 8 (A2A) depends on Tasks 1-4 (identity + registry)
- Task 9 (SDK/MCP/CLI surface) depends on Tasks 1-7
- Task 10 (A2A surface) depends on Tasks 8-9

**Optimal dispatch:**
1. Launch Tasks 1, 5, 6, 7 in parallel (independent backend work)
2. When Task 1 completes → launch Tasks 2, 4 in parallel
3. When Task 2 completes → launch Task 3
4. When Tasks 1-7 complete → launch Task 9
5. When Tasks 1-4 complete → launch Task 8
6. When Tasks 8-9 complete → launch Task 10
