# Scoped Tokens + Webhook DLQ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize ephemeral scoped tokens beyond vault (JWT signed by agent DID, scope[]/audience/parent_token_id, validation middleware, revocation table, cleanup worker, docs); add webhook DLQ with exponential backoff, glob event filtering, and a console replay button.

**Architecture:**
1. **Scoped Tokens (Item 1):** New `ScopedToken` model alongside (not replacing) `VaultToken`. Tokens are signed JWTs (Ed25519 via existing `agent-identity/crypto.ts`) with claims `{iss, sub, aud, scope[], parent_jti, exp, jti}`. The Fastify auth middleware learns to recognize `Bearer stk_<base64url-jwt>` tokens, verifies signature against the agent's stored public key, and treats them as a scoped auth principal. A `RevokedToken` table holds an explicit denylist (since JWTs are stateless). A 5-min worker prunes expired tokens.
2. **Webhook DLQ (Item 2):** Add `status`/`lastError`/`deadLetteredAt` columns to `WebhookDelivery`, plus a separate `webhook-dead-letter` BullMQ queue. The existing delivery worker moves exhausted deliveries to DLQ and updates status. A new DLQ worker just persists/logs failed payloads. Webhook event filtering moves from `events: { has: x }` (Postgres exact) to a glob matcher (`email.*`, `phone.*.failed`) — Postgres still does coarse filtering on prefix, then in-process matching on the glob. Console gets a "Replay" button that re-enqueues the delivery.

**Tech Stack:**
- Prisma + Postgres (schema + migrations)
- Fastify + oRPC (API routes & contracts)
- BullMQ + Redis (workers / DLQ queue)
- Bun test runner (`.test.ts` files run via `bun test`)
- Ed25519 JWTs (existing `node:crypto` via `@anima/agent-identity`)
- Next.js 15 + React Query (`apps/console`)

---

## File Structure

### Item 1: ScopedToken

**New files:**
- `packages/db/prisma/migrations/20260501100000_add_scoped_tokens/migration.sql` — Postgres migration creating `scoped_tokens` and `revoked_tokens`
- `packages/agent-identity/src/scoped-token.ts` — JWT issuer/verifier (uses existing crypto.ts)
- `packages/agent-identity/src/__tests__/scoped-token.test.ts` — unit tests for issuer/verifier
- `packages/contracts/src/scoped-token-grammar.ts` — scope grammar parser/validator (e.g. `email:send`)
- `packages/contracts/src/contracts/scoped-tokens.ts` — oRPC contract
- `packages/contracts/src/schemas/scoped-tokens.ts` — zod schemas
- `apps/api/src/middleware/scoped-token.ts` — Fastify middleware for `Bearer stk_*` tokens
- `apps/api/src/routes/handlers/scoped-tokens.ts` — issue/list/revoke handlers
- `apps/api/src/workers/scoped-token-cleanup-worker.ts` — 5-min interval worker
- `apps/api/src/__tests__/integration/scoped-tokens-crud.test.ts` — integration test
- `docs/scoped-tokens.md` — public docs page

**Modified files:**
- `packages/db/prisma/schema.prisma` — add `ScopedToken` and `RevokedToken` models, plus `scopedTokens` relation on `Agent`
- `packages/agent-identity/src/index.ts` — export new symbols
- `packages/contracts/src/index.ts` — re-export new contract & schemas
- `packages/contracts/src/contracts/index.ts` — register `scopedTokens` router
- `packages/contracts/src/scopes.ts` — register `scopedTokens.*` procedure paths
- `apps/api/src/middleware/auth.ts` — recognize `stk_` prefix and route to scoped-token verifier
- `apps/api/src/context.ts` — extend `AuthInfo` with `scopedTokenId?: string`, `parentTokenId?: string`
- `apps/api/src/routes/router-utils.ts` — register handlers; expose `mapScopedTokenToOutput`
- `apps/api/src/router.ts` — mount scopedTokens router
- `apps/api/src/workers/index.ts` — start scoped-token-cleanup-worker

### Item 2: Webhook DLQ + filtering

**New files:**
- `packages/db/prisma/migrations/20260501110000_add_webhook_dlq/migration.sql` — adds `status`, `last_error`, `dead_lettered_at` columns + `WebhookDeliveryStatus` enum
- `packages/shared/src/webhook-event-matcher.ts` — `matchesEventPattern` glob function
- `packages/shared/src/__tests__/webhook-event-matcher.test.ts` — unit tests
- `apps/api/src/workers/webhook-dead-letter.ts` — DLQ BullMQ worker
- `apps/api/src/__tests__/integration/webhook-dlq.test.ts` — integration test for replay + event globbing

**Modified files:**
- `packages/db/prisma/schema.prisma` — add columns + enum to `WebhookDelivery`
- `packages/shared/src/index.ts` — export matcher
- `packages/contracts/src/schemas/webhook.ts` — relax `WebhookEventSchema` to allow glob patterns; add `status`/`lastError`/`deadLetteredAt` to `WebhookDeliveryOutput`; add `ReplayWebhookDeliveryInput`/`Output`
- `packages/contracts/src/contracts/webhook.ts` — add `replayDelivery` procedure
- `packages/contracts/src/scopes.ts` — map `webhook.replayDelivery` → `webhooks:write`
- `apps/api/src/workers/webhook-delivery.ts` — set `status` on each transition; on max attempts move to DLQ queue + update `dead_lettered_at`; record `last_error`
- `apps/api/src/workers/index.ts` — start `webhook-dead-letter` worker
- `apps/api/src/routes/router-utils.ts` — `createWebhookDeliveriesForEvent` uses event matcher (find webhooks with prefix overlap, then glob filter in-process)
- `apps/api/src/routes/handlers/webhook.ts` — add `replayDelivery` handler
- `apps/console/src/components/webhooks/webhook-delivery-log.tsx` — show status badge + "Replay" button on dead-lettered rows

---

## Conventions

**Test runner:** `bun test path/to/file.test.ts` runs Bun's built-in test runner. Integration tests under `apps/api/src/__tests__/integration/` use `setup.ts` for shared fixtures (real Postgres + Prisma).

**Migrations:** This repo uses `prisma migrate deploy` in production. Locally: write the migration `.sql` by hand under a timestamped directory, then run `bun run db:deploy` from the repo root. The migration timestamp prefix MUST be later than `20260425140000_add_audit_events` (the current head).

**Commit cadence:** Each task ends with a commit. Commit messages use Conventional Commits (`feat:`, `fix:`, `test:`, etc.) — see `git log --oneline -20` for examples.

**File organization:** Each handler file has a matching `__tests__/integration/<name>.test.ts`. Each `packages/<pkg>/src/<feature>.ts` has `packages/<pkg>/src/__tests__/<feature>.test.ts`.

---

# PART A — Item 1: Scoped Tokens

## Task A1: Add ScopedToken & RevokedToken Prisma models

**Files:**
- Modify: `packages/db/prisma/schema.prisma:586-608` (after the existing `VaultToken` model)
- Modify: `packages/db/prisma/schema.prisma:392-440` (add relation to Agent)
- Create: `packages/db/prisma/migrations/20260501100000_add_scoped_tokens/migration.sql`

- [ ] **Step 1: Add models to schema.prisma**

After the `VaultToken` model block (`@@map("vault_tokens")` at line 607), append:

```prisma
/// General-purpose scoped tokens for delegated agent authority.
/// Unlike VaultToken (which is single-credential), ScopedToken
/// carries a scope[] (resource:action) plus audience and an optional
/// parent_token_id forming a delegation chain. Tokens are signed
/// JWTs (Ed25519) verified against the agent's DID public key.
model ScopedToken {
  id             String        @id @default(cuid())
  /// JWT id (`jti` claim) — the unique identifier baked into the JWT.
  /// Used as the lookup key when validating an incoming token.
  jti            String        @unique @map("jti")
  /// Issuing agent — `iss` claim resolves to this agent's DID.
  agentId        String        @map("agent_id")
  /// Organization that owns this token (matches the agent's org).
  orgId          String        @map("org_id")
  /// Scope strings, e.g. ["email:send", "vault:read"]
  scopes         String[]      @map("scopes")
  /// `aud` claim — typically a service identifier (e.g. "api.useanima.sh").
  audience       String        @map("audience")
  /// Parent token's jti for delegation chains. Null = root token.
  parentJti      String?       @map("parent_jti")
  /// Expiration timestamp.
  expiresAt      DateTime      @map("expires_at")
  /// Set when the token is explicitly revoked.
  revokedAt      DateTime?     @map("revoked_at")
  /// Free-form metadata (task id, conversation id, etc.).
  metadata       Json          @default("{}") @map("metadata")
  createdAt      DateTime      @default(now()) @map("created_at")
  agent          Agent         @relation(fields: [agentId], references: [id], onDelete: Cascade)

  @@index([agentId])
  @@index([orgId])
  @@index([expiresAt])
  @@index([parentJti])
  @@map("scoped_tokens")
}

/// Denylist for revoked JWT scoped tokens. Since JWTs are stateless,
/// we keep an explicit revocation list and check it on every verify.
/// Rows are pruned by the cleanup worker when the underlying token
/// expires (no point denylisting a token that's already expired).
model RevokedToken {
  jti          String   @id @map("jti")
  /// Mirrors the original token's expiry so the cleanup worker
  /// can drop the row once the token would have expired anyway.
  expiresAt    DateTime @map("expires_at")
  revokedAt    DateTime @default(now()) @map("revoked_at")
  /// Optional reason supplied at revocation time.
  reason       String?  @map("reason")

  @@index([expiresAt])
  @@map("revoked_tokens")
}
```

In the `Agent` model (line 432-436, around the `oboTokens` relation), add a `scopedTokens` relation:

```prisma
  oboTokens                   OboToken[]
  scopedTokens                ScopedToken[]
  quarantineLevel             QuarantineLevel @default(NONE) @map("quarantine_level")
```

- [ ] **Step 2: Write the migration SQL**

Create `packages/db/prisma/migrations/20260501100000_add_scoped_tokens/migration.sql`:

```sql
-- ScopedToken: general-purpose scoped tokens (JWT, signed by agent DID).
CREATE TABLE "scoped_tokens" (
  "id"          TEXT NOT NULL,
  "jti"         TEXT NOT NULL,
  "agent_id"    TEXT NOT NULL,
  "org_id"      TEXT NOT NULL,
  "scopes"      TEXT[] NOT NULL,
  "audience"    TEXT NOT NULL,
  "parent_jti"  TEXT,
  "expires_at"  TIMESTAMP(3) NOT NULL,
  "revoked_at"  TIMESTAMP(3),
  "metadata"    JSONB NOT NULL DEFAULT '{}',
  "created_at"  TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "scoped_tokens_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "scoped_tokens_jti_key" ON "scoped_tokens"("jti");
CREATE INDEX "scoped_tokens_agent_id_idx" ON "scoped_tokens"("agent_id");
CREATE INDEX "scoped_tokens_org_id_idx" ON "scoped_tokens"("org_id");
CREATE INDEX "scoped_tokens_expires_at_idx" ON "scoped_tokens"("expires_at");
CREATE INDEX "scoped_tokens_parent_jti_idx" ON "scoped_tokens"("parent_jti");

ALTER TABLE "scoped_tokens"
  ADD CONSTRAINT "scoped_tokens_agent_id_fkey"
  FOREIGN KEY ("agent_id") REFERENCES "agents"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

-- RevokedToken: denylist for revoked JWTs. Pruned by cleanup worker when expired.
CREATE TABLE "revoked_tokens" (
  "jti"        TEXT NOT NULL,
  "expires_at" TIMESTAMP(3) NOT NULL,
  "revoked_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "reason"     TEXT,

  CONSTRAINT "revoked_tokens_pkey" PRIMARY KEY ("jti")
);

CREATE INDEX "revoked_tokens_expires_at_idx" ON "revoked_tokens"("expires_at");
```

- [ ] **Step 3: Generate Prisma client and apply migration**

Run from repo root:
```bash
cd anima && bun run db:generate
bun run db:deploy
```

Expected: `Applying migration '20260501100000_add_scoped_tokens'` then `Database is now in sync`.

- [ ] **Step 4: Commit**

```bash
git add anima/packages/db/prisma/schema.prisma anima/packages/db/prisma/migrations/20260501100000_add_scoped_tokens
git commit -m "feat(db): add ScopedToken and RevokedToken models"
```

---

## Task A2: Scope grammar parser

**Files:**
- Create: `packages/contracts/src/scoped-token-grammar.ts`
- Create: `packages/contracts/src/__tests__/scoped-token-grammar.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `packages/contracts/src/__tests__/scoped-token-grammar.test.ts`:

```ts
import { describe, expect, it } from "bun:test";
import {
  isValidScopedTokenScope,
  parseScopedTokenScope,
  scopedTokenScopeSatisfies,
} from "../scoped-token-grammar";

describe("scoped-token-grammar", () => {
  describe("isValidScopedTokenScope", () => {
    it("accepts valid resource:action strings", () => {
      expect(isValidScopedTokenScope("email:send")).toBe(true);
      expect(isValidScopedTokenScope("vault:read")).toBe(true);
    });

    it("accepts the wildcard", () => {
      expect(isValidScopedTokenScope("*")).toBe(true);
    });

    it("rejects unknown resources", () => {
      expect(isValidScopedTokenScope("nonsense:read")).toBe(false);
    });

    it("rejects malformed strings", () => {
      expect(isValidScopedTokenScope("email")).toBe(false);
      expect(isValidScopedTokenScope("email:send:extra")).toBe(false);
      expect(isValidScopedTokenScope("")).toBe(false);
    });
  });

  describe("parseScopedTokenScope", () => {
    it("parses resource:action", () => {
      expect(parseScopedTokenScope("email:send")).toEqual({
        resource: "email",
        action: "send",
      });
    });

    it("returns null for invalid scopes", () => {
      expect(parseScopedTokenScope("not-a-scope")).toBeNull();
    });
  });

  describe("scopedTokenScopeSatisfies", () => {
    it("granted wildcard satisfies anything", () => {
      expect(scopedTokenScopeSatisfies(["*"], ["email:send"])).toBe(true);
    });

    it("requires every scope", () => {
      expect(
        scopedTokenScopeSatisfies(
          ["email:send"],
          ["email:send", "messages:send"],
        ),
      ).toBe(false);
      expect(
        scopedTokenScopeSatisfies(
          ["email:send", "messages:send"],
          ["email:send", "messages:send"],
        ),
      ).toBe(true);
    });

    it("empty required scope set is satisfied by anything", () => {
      expect(scopedTokenScopeSatisfies([], [])).toBe(true);
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd anima/packages/contracts && bun test src/__tests__/scoped-token-grammar.test.ts
```
Expected: FAIL with "Cannot find module './scoped-token-grammar'".

- [ ] **Step 3: Write the implementation**

Create `packages/contracts/src/scoped-token-grammar.ts`:

```ts
/**
 * Scoped Token Scope Grammar
 *
 * v1 grammar: `resource:action` (matches the existing API key SCOPE_CATALOGUE)
 * plus the `*` wildcard. Resource-instance binding (`email:send:agent_xyz`)
 * is intentionally out of scope for v1 — see plan §"Decision 2".
 */

import { SCOPE_CATALOGUE, WILDCARD_SCOPE, type Scope } from "./scopes";

export interface ParsedScope {
  resource: string;
  action: string;
}

export function isValidScopedTokenScope(candidate: string): candidate is Scope {
  if (candidate === WILDCARD_SCOPE) return true;
  return (SCOPE_CATALOGUE as readonly string[]).includes(candidate);
}

export function parseScopedTokenScope(scope: string): ParsedScope | null {
  if (scope === WILDCARD_SCOPE) {
    return { resource: "*", action: "*" };
  }
  if (!isValidScopedTokenScope(scope)) return null;
  const [resource, action, extra] = scope.split(":");
  if (!resource || !action || extra !== undefined) return null;
  return { resource, action };
}

/**
 * Does `granted` satisfy `required`? Wildcard short-circuits; otherwise
 * granted must contain every required scope (AND semantics, matching the
 * existing API-key scope check).
 */
export function scopedTokenScopeSatisfies(
  granted: readonly string[],
  required: readonly string[],
): boolean {
  if (required.length === 0) return true;
  if (granted.includes(WILDCARD_SCOPE)) return true;
  return required.every((r) => granted.includes(r));
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd anima/packages/contracts && bun test src/__tests__/scoped-token-grammar.test.ts
```
Expected: PASS (8 assertions).

- [ ] **Step 5: Commit**

```bash
git add anima/packages/contracts/src/scoped-token-grammar.ts anima/packages/contracts/src/__tests__/scoped-token-grammar.test.ts
git commit -m "feat(contracts): add scoped-token scope grammar parser"
```

---

## Task A3: JWT issuer/verifier in agent-identity

**Files:**
- Create: `packages/agent-identity/src/scoped-token.ts`
- Create: `packages/agent-identity/src/__tests__/scoped-token.test.ts`
- Modify: `packages/agent-identity/src/index.ts`

- [ ] **Step 1: Write the failing tests**

Create `packages/agent-identity/src/__tests__/scoped-token.test.ts`:

```ts
import { describe, expect, it } from "bun:test";
import { generateKeyPair } from "../crypto";
import {
  TOKEN_PREFIX,
  decodeScopedToken,
  isScopedToken,
  issueScopedToken,
  verifyScopedToken,
} from "../scoped-token";

describe("scoped-token", () => {
  const { publicKeyJwk, privateKeyJwk } = generateKeyPair("Ed25519");

  it("issues a token with stk_ prefix", () => {
    const { token, payload } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["email:send"],
      ttlSeconds: 60,
    });
    expect(token.startsWith(TOKEN_PREFIX)).toBe(true);
    expect(payload.iss).toBe("did:web:example.com:agent_abc");
    expect(payload.aud).toBe("api.useanima.sh");
    expect(payload.scope).toEqual(["email:send"]);
    expect(payload.jti).toMatch(/^[a-f0-9]{32}$/);
  });

  it("verifies a valid token", () => {
    const { token } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["vault:read"],
      ttlSeconds: 60,
    });
    const result = verifyScopedToken({ token, publicKeyJwk });
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.payload.scope).toEqual(["vault:read"]);
    }
  });

  it("rejects a tampered token", () => {
    const { token } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["vault:read"],
      ttlSeconds: 60,
    });
    const tampered = `${token.slice(0, -4)}AAAA`;
    const result = verifyScopedToken({ token: tampered, publicKeyJwk });
    expect(result.valid).toBe(false);
    if (!result.valid) expect(result.reason).toBe("invalid_signature");
  });

  it("rejects an expired token", () => {
    const { token } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["vault:read"],
      ttlSeconds: -10, // already expired
    });
    const result = verifyScopedToken({ token, publicKeyJwk });
    expect(result.valid).toBe(false);
    if (!result.valid) expect(result.reason).toBe("expired");
  });

  it("rejects audience mismatch", () => {
    const { token } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["vault:read"],
      ttlSeconds: 60,
    });
    const result = verifyScopedToken({
      token,
      publicKeyJwk,
      expectedAudience: "other.audience",
    });
    expect(result.valid).toBe(false);
    if (!result.valid) expect(result.reason).toBe("audience_mismatch");
  });

  it("isScopedToken recognizes the prefix", () => {
    expect(isScopedToken("stk_abc.def.ghi")).toBe(true);
    expect(isScopedToken("vtk_abc")).toBe(false);
    expect(isScopedToken("Bearer stk_abc.def.ghi")).toBe(false);
  });

  it("decodeScopedToken returns claims without verification", () => {
    const { token, payload } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["email:send"],
      ttlSeconds: 60,
    });
    const decoded = decodeScopedToken(token);
    expect(decoded?.jti).toBe(payload.jti);
    expect(decoded?.scope).toEqual(["email:send"]);
  });

  it("supports parent_jti delegation reference", () => {
    const { token, payload } = issueScopedToken({
      privateKeyJwk,
      issuer: "did:web:example.com:agent_abc",
      subject: "agent_abc",
      audience: "api.useanima.sh",
      scopes: ["email:send"],
      ttlSeconds: 60,
      parentJti: "deadbeefdeadbeefdeadbeefdeadbeef",
    });
    expect(payload.parent_jti).toBe("deadbeefdeadbeefdeadbeefdeadbeef");
    const decoded = decodeScopedToken(token);
    expect(decoded?.parent_jti).toBe("deadbeefdeadbeefdeadbeefdeadbeef");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd anima/packages/agent-identity && bun test src/__tests__/scoped-token.test.ts
```
Expected: FAIL with "Cannot find module './scoped-token'".

- [ ] **Step 3: Write the implementation**

Create `packages/agent-identity/src/scoped-token.ts`:

```ts
/**
 * Scoped Token (JWT)
 *
 * Self-contained, signed authority delegation. The token is a JSON Web
 * Token (RFC 7519) signed with the agent's DID key (Ed25519 by default).
 * Format: `stk_<header>.<payload>.<signature>` where the three sections
 * are base64url-encoded.
 *
 * Verification is stateless — the API only needs the agent's public key
 * (already stored in `agents.public_key`). Revocation is enforced by an
 * explicit denylist check (the `revoked_tokens` table) on top of the
 * signature/expiry checks here.
 *
 * v1 differences from a fully-spec JWT: we use Ed25519 (alg `EdDSA`) by
 * default; we do not support `kid` lookup chains or JWKS — the caller
 * supplies the public key directly.
 */

import { randomBytes } from "node:crypto";
import { signPayload, verifySignature } from "./crypto";

export const TOKEN_PREFIX = "stk_" as const;

export interface ScopedTokenClaims {
  /** Issuer — typically the agent's DID. */
  iss: string;
  /** Subject — usually the agent id. */
  sub: string;
  /** Audience — usually the service identifier. */
  aud: string;
  /** Scopes — array of `resource:action` strings. */
  scope: string[];
  /** Expiry time, seconds since epoch (RFC 7519 standard claim). */
  exp: number;
  /** Issued-at time, seconds since epoch. */
  iat: number;
  /** Unique token id (32-char hex). */
  jti: string;
  /** Optional parent token's jti for delegation chains. */
  parent_jti?: string;
}

export interface IssueScopedTokenParams {
  privateKeyJwk: JsonWebKey;
  issuer: string;
  subject: string;
  audience: string;
  scopes: string[];
  ttlSeconds: number;
  parentJti?: string;
}

export interface IssueScopedTokenResult {
  /** The full `stk_<jwt>` token to hand back to the caller. */
  token: string;
  /** The decoded payload (also useful for the issuer to persist). */
  payload: ScopedTokenClaims;
}

export type VerifyScopedTokenResult =
  | { valid: true; payload: ScopedTokenClaims }
  | {
      valid: false;
      reason:
        | "malformed"
        | "invalid_signature"
        | "expired"
        | "audience_mismatch"
        | "issuer_mismatch";
    };

export interface VerifyScopedTokenParams {
  token: string;
  publicKeyJwk: JsonWebKey;
  expectedAudience?: string;
  expectedIssuer?: string;
  /** Override `Date.now()` for tests. */
  now?: number;
}

const JWT_HEADER_EDDSA = { alg: "EdDSA", typ: "JWT" } as const;
const JWT_HEADER_ES256 = { alg: "ES256", typ: "JWT" } as const;

function base64urlEncode(bytes: Uint8Array | Buffer | string): string {
  return Buffer.from(bytes as Buffer | string).toString("base64url");
}

function base64urlDecodeJson<T>(encoded: string): T | null {
  try {
    return JSON.parse(Buffer.from(encoded, "base64url").toString("utf-8")) as T;
  } catch {
    return null;
  }
}

function pickHeader(jwk: JsonWebKey) {
  if (jwk.kty === "OKP") return JWT_HEADER_EDDSA;
  return JWT_HEADER_ES256;
}

export function issueScopedToken(
  params: IssueScopedTokenParams,
): IssueScopedTokenResult {
  const now = Math.floor(Date.now() / 1000);
  const jti = randomBytes(16).toString("hex");

  const claims: ScopedTokenClaims = {
    iss: params.issuer,
    sub: params.subject,
    aud: params.audience,
    scope: params.scopes,
    iat: now,
    exp: now + params.ttlSeconds,
    jti,
    ...(params.parentJti ? { parent_jti: params.parentJti } : {}),
  };

  const header = pickHeader(params.privateKeyJwk);
  const headerB64 = base64urlEncode(JSON.stringify(header));
  const payloadB64 = base64urlEncode(JSON.stringify(claims));
  const signingInput = `${headerB64}.${payloadB64}`;
  const signature = signPayload(params.privateKeyJwk, signingInput);
  const jwt = `${signingInput}.${signature}`;

  return { token: `${TOKEN_PREFIX}${jwt}`, payload: claims };
}

export function isScopedToken(value: string): boolean {
  return (
    value.startsWith(TOKEN_PREFIX) && value.split(".").length === 3
  );
}

export function decodeScopedToken(token: string): ScopedTokenClaims | null {
  if (!isScopedToken(token)) return null;
  const jwt = token.slice(TOKEN_PREFIX.length);
  const parts = jwt.split(".");
  if (parts.length !== 3) return null;
  return base64urlDecodeJson<ScopedTokenClaims>(parts[1] ?? "");
}

export function verifyScopedToken(
  params: VerifyScopedTokenParams,
): VerifyScopedTokenResult {
  if (!isScopedToken(params.token)) {
    return { valid: false, reason: "malformed" };
  }
  const jwt = params.token.slice(TOKEN_PREFIX.length);
  const parts = jwt.split(".");
  if (parts.length !== 3) return { valid: false, reason: "malformed" };
  const [headerB64, payloadB64, signature] = parts as [string, string, string];

  const claims = base64urlDecodeJson<ScopedTokenClaims>(payloadB64);
  if (!claims) return { valid: false, reason: "malformed" };

  const signingInput = `${headerB64}.${payloadB64}`;
  if (!verifySignature(params.publicKeyJwk, signingInput, signature)) {
    return { valid: false, reason: "invalid_signature" };
  }

  const nowSeconds = Math.floor((params.now ?? Date.now()) / 1000);
  if (claims.exp <= nowSeconds) {
    return { valid: false, reason: "expired" };
  }
  if (params.expectedAudience && claims.aud !== params.expectedAudience) {
    return { valid: false, reason: "audience_mismatch" };
  }
  if (params.expectedIssuer && claims.iss !== params.expectedIssuer) {
    return { valid: false, reason: "issuer_mismatch" };
  }

  return { valid: true, payload: claims };
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd anima/packages/agent-identity && bun test src/__tests__/scoped-token.test.ts
```
Expected: PASS (8 assertions).

- [ ] **Step 5: Export from package index**

Edit `packages/agent-identity/src/index.ts` — append at the end:

```ts
export {
  TOKEN_PREFIX as SCOPED_TOKEN_PREFIX,
  decodeScopedToken,
  isScopedToken,
  issueScopedToken,
  verifyScopedToken,
  type IssueScopedTokenParams,
  type IssueScopedTokenResult,
  type ScopedTokenClaims,
  type VerifyScopedTokenParams,
  type VerifyScopedTokenResult,
} from "./scoped-token";
```

- [ ] **Step 6: Commit**

```bash
git add anima/packages/agent-identity/src/scoped-token.ts anima/packages/agent-identity/src/__tests__/scoped-token.test.ts anima/packages/agent-identity/src/index.ts
git commit -m "feat(agent-identity): add JWT scoped-token issuer/verifier"
```

---

## Task A4: oRPC contract + zod schemas

**Files:**
- Create: `packages/contracts/src/schemas/scoped-tokens.ts`
- Create: `packages/contracts/src/contracts/scoped-tokens.ts`
- Modify: `packages/contracts/src/contracts/index.ts`
- Modify: `packages/contracts/src/index.ts`
- Modify: `packages/contracts/src/scopes.ts`

- [ ] **Step 1: Create the zod schemas**

Create `packages/contracts/src/schemas/scoped-tokens.ts`:

```ts
import { z } from "zod";
import { CursorPagination, PaginationInput } from "./common";

export const IssueScopedTokenInput = z
  .object({
    audience: z
      .string()
      .min(1)
      .describe("Token audience (typically the service identifier, e.g. 'api.useanima.sh')"),
    scopes: z
      .array(z.string().min(3))
      .min(1)
      .describe("Scope strings the token grants, e.g. ['email:send']"),
    ttlSeconds: z
      .number()
      .int()
      .positive()
      .max(3600)
      .default(300)
      .describe("Token TTL in seconds (max 1h)"),
    parentJti: z
      .string()
      .length(32)
      .optional()
      .describe("Parent token jti for delegation chains"),
    metadata: z
      .record(z.string(), z.unknown())
      .optional()
      .describe("Free-form metadata (task id, conversation id, etc.)"),
  })
  .describe("Issue a new scoped token");

export const ScopedTokenOutput = z
  .object({
    id: z.string().cuid2(),
    jti: z.string().length(32),
    agentId: z.string(),
    orgId: z.string(),
    scopes: z.array(z.string()),
    audience: z.string(),
    parentJti: z.string().nullable(),
    expiresAt: z.string().datetime(),
    revokedAt: z.string().datetime().nullable(),
    createdAt: z.string().datetime(),
  })
  .describe("Scoped token resource (does NOT include the raw JWT)");

export const IssueScopedTokenOutput = z
  .object({
    token: z
      .string()
      .startsWith("stk_")
      .describe("Raw JWT — only returned at issuance time"),
    record: ScopedTokenOutput.describe("Persisted record (no raw JWT)"),
  })
  .describe("Result of issuing a scoped token");

export const ListScopedTokensInput = PaginationInput.extend({
  agentId: z.string().optional(),
  includeExpired: z.boolean().default(false).optional(),
}).describe("Filter parameters for listing scoped tokens");

export const ListScopedTokensOutput = z
  .object({
    items: z.array(ScopedTokenOutput),
    pagination: CursorPagination,
  })
  .describe("Paginated list of scoped tokens");

export const RevokeScopedTokenInput = z
  .object({
    jti: z.string().length(32).describe("Token jti to revoke"),
    reason: z.string().max(200).optional(),
  })
  .describe("Revoke a scoped token by jti");

export const RevokeScopedTokenOutput = z
  .object({
    success: z.literal(true),
    jti: z.string().length(32),
  })
  .describe("Revocation confirmation");
```

- [ ] **Step 2: Create the oRPC contract**

Create `packages/contracts/src/contracts/scoped-tokens.ts`:

```ts
import { oc } from "@orpc/contract";
import {
  IssueScopedTokenInput,
  IssueScopedTokenOutput,
  ListScopedTokensInput,
  ListScopedTokensOutput,
  RevokeScopedTokenInput,
  RevokeScopedTokenOutput,
} from "../schemas/scoped-tokens";

export const scopedTokensContract = oc.router({
  issue: oc
    .route({ method: "POST", path: "/scoped-tokens" })
    .input(IssueScopedTokenInput)
    .output(IssueScopedTokenOutput),
  list: oc
    .route({ method: "GET", path: "/scoped-tokens" })
    .input(ListScopedTokensInput)
    .output(ListScopedTokensOutput),
  revoke: oc
    .route({ method: "POST", path: "/scoped-tokens/revoke" })
    .input(RevokeScopedTokenInput)
    .output(RevokeScopedTokenOutput),
});
```

- [ ] **Step 3: Register contract in `contracts/index.ts`**

Open `packages/contracts/src/contracts/index.ts` and add the import + the field. Read the file first to see the exact style:

```bash
cat anima/packages/contracts/src/contracts/index.ts
```

Then add an `import { scopedTokensContract } from "./scoped-tokens";` and a `scopedTokens: scopedTokensContract,` field to the main `contract` object — matching the pattern of e.g. `webhook: webhookContract`.

- [ ] **Step 4: Re-export from package index**

Edit `packages/contracts/src/index.ts` — find the block exporting webhook contracts and append:

```ts
export * from "./contracts/scoped-tokens";
export * from "./schemas/scoped-tokens";
export * from "./scoped-token-grammar";
```

- [ ] **Step 5: Register procedure scopes**

Edit `packages/contracts/src/scopes.ts:330` (just before the `apiKeys.listScopes` entry, in `PROCEDURE_SCOPE_MAP`):

```ts
  // ========== Scoped Tokens (issuance & management) ==========
  // Issuing tokens requires `agents:write` (only agent owners can mint
  // delegated tokens for their own agents). Listing and revoking are
  // gated by `agents:read` and `agents:write` respectively.
  "scopedTokens.issue": ["agents:write"],
  "scopedTokens.list": ["agents:read"],
  "scopedTokens.revoke": ["agents:write"],
```

- [ ] **Step 6: Verify the contracts package typechecks**

```bash
cd anima/packages/contracts && bun run typecheck
```
Expected: PASS (no errors).

- [ ] **Step 7: Commit**

```bash
git add anima/packages/contracts/src
git commit -m "feat(contracts): add scopedTokens oRPC contract & schemas"
```

---

## Task A5: Fastify middleware to verify scoped tokens

**Files:**
- Create: `apps/api/src/middleware/scoped-token.ts`
- Modify: `apps/api/src/middleware/auth.ts`
- Modify: `apps/api/src/context.ts`

- [ ] **Step 1: Read the existing AuthInfo definition**

```bash
grep -n "interface AuthInfo\|type AuthInfo" anima/apps/api/src/context.ts
```

Read the surrounding lines so the next edit fits the existing shape.

- [ ] **Step 2: Extend AuthInfo with scoped-token fields**

Edit `apps/api/src/context.ts` — in the `AuthInfo` interface, append two optional fields:

```ts
  /** Set when the request was authenticated via a `stk_` scoped token. */
  scopedTokenJti?: string;
  /** Parent token jti, if this token was minted from a delegation chain. */
  parentTokenJti?: string;
```

If `AuthInfo` already has a `scopes?: string[]` field, that's reused for the token's scopes. If not, add it.

- [ ] **Step 3: Create the scoped-token middleware**

Create `apps/api/src/middleware/scoped-token.ts`:

```ts
/**
 * Resolves a `Bearer stk_*` token to an AuthInfo principal.
 *
 * Steps:
 *   1. Verify the JWT signature against the issuing agent's public key.
 *   2. Check the `revoked_tokens` denylist for the jti.
 *   3. Confirm the persisted ScopedToken row exists (defense in depth —
 *      a JWT signed by the right key but with a jti we never issued is
 *      probably an attack).
 *   4. Return an AuthInfo carrying the agent's org/agent ids plus the
 *      token's scope set.
 */

import {
  decodeScopedToken,
  isScopedToken,
  verifyScopedToken,
} from "@anima/agent-identity";

import type { AuthInfo } from "../context";
import type { PrismaClient } from "../encrypted-prisma";

const EXPECTED_AUDIENCE = "api.useanima.sh";

export async function resolveScopedTokenAuth(
  rawToken: string,
  db: PrismaClient,
): Promise<AuthInfo | undefined> {
  if (!isScopedToken(rawToken)) return undefined;

  const claimsView = decodeScopedToken(rawToken);
  if (!claimsView) return undefined;

  // The `sub` claim is the agent id — use it to fetch the verifying key.
  const agent = await db.agent.findUnique({
    where: { id: claimsView.sub },
    select: {
      id: true,
      orgId: true,
      publicKey: true,
      did: true,
    },
  });

  if (!agent || !agent.publicKey) return undefined;

  let publicKeyJwk: JsonWebKey;
  try {
    publicKeyJwk = JSON.parse(agent.publicKey) as JsonWebKey;
  } catch {
    return undefined;
  }

  const verification = verifyScopedToken({
    token: rawToken,
    publicKeyJwk,
    expectedAudience: EXPECTED_AUDIENCE,
    expectedIssuer: agent.did ?? undefined,
  });

  if (!verification.valid) return undefined;

  const { payload } = verification;

  // Denylist check — JWTs are stateless, so we keep an explicit revocation list.
  const revoked = await db.revokedToken.findUnique({
    where: { jti: payload.jti },
  });
  if (revoked) return undefined;

  // Defense in depth: ensure we actually issued this token.
  const stored = await db.scopedToken.findUnique({
    where: { jti: payload.jti },
    select: { id: true, revokedAt: true, parentJti: true },
  });
  if (!stored || stored.revokedAt) return undefined;

  return {
    orgId: agent.orgId,
    agentId: agent.id,
    keyType: "agent",
    authMethod: "scoped_token",
    scopes: payload.scope,
    scopedTokenJti: payload.jti,
    parentTokenJti: stored.parentJti ?? undefined,
  };
}
```

- [ ] **Step 4: Wire into resolveAuth**

Edit `apps/api/src/middleware/auth.ts:316-341` — in `resolveAuth`, before the API-key prefix check, add:

```ts
  if (key.startsWith("stk_")) {
    return resolveScopedTokenAuth(key, db);
  }
```

Add the import at the top of the file:

```ts
import { resolveScopedTokenAuth } from "./scoped-token";
```

You will also need to widen the `AuthInfo.authMethod` union to include `"scoped_token"`. Open `apps/api/src/context.ts` and in the `AuthInfo` type alias / interface, change `authMethod: "api_key" | "clerk"` to `authMethod: "api_key" | "clerk" | "scoped_token"`. If the file uses a different shape, follow the existing pattern.

- [ ] **Step 5: Typecheck**

```bash
cd anima/apps/api && bun run typecheck
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add anima/apps/api/src/middleware/scoped-token.ts anima/apps/api/src/middleware/auth.ts anima/apps/api/src/context.ts
git commit -m "feat(api): verify scoped tokens in auth middleware"
```

---

## Task A6: Issue / List / Revoke handlers

**Files:**
- Create: `apps/api/src/routes/handlers/scoped-tokens.ts`
- Modify: `apps/api/src/routes/router-utils.ts`
- Modify: `apps/api/src/router.ts`

- [ ] **Step 1: Read router-utils to understand the handler pattern**

```bash
grep -n "createWebhookHandlers\|webhook:" anima/apps/api/src/routes/router-utils.ts | head
```

Note the conventions for `mapXToOutput` helpers and how `os` is constructed.

- [ ] **Step 2: Write the handlers**

Create `apps/api/src/routes/handlers/scoped-tokens.ts`:

```ts
import { issueScopedToken } from "@anima/agent-identity";
import type { Prisma } from "@anima/db";
import { AppError, ForbiddenError } from "@anima/shared";

import { requireAuth } from "../../middleware/auth";
import { os } from "../router-utils";

const EXPECTED_AUDIENCE = "api.useanima.sh";

function mapScopedTokenToOutput(record: {
  id: string;
  jti: string;
  agentId: string;
  orgId: string;
  scopes: string[];
  audience: string;
  parentJti: string | null;
  expiresAt: Date;
  revokedAt: Date | null;
  createdAt: Date;
}) {
  return {
    id: record.id,
    jti: record.jti,
    agentId: record.agentId,
    orgId: record.orgId,
    scopes: record.scopes,
    audience: record.audience,
    parentJti: record.parentJti,
    expiresAt: record.expiresAt.toISOString(),
    revokedAt: record.revokedAt?.toISOString() ?? null,
    createdAt: record.createdAt.toISOString(),
  };
}

export function createScopedTokensHandlers() {
  return {
    issue: os.scopedTokens.issue.handler(async ({ input, context }) => {
      const auth = requireAuth(context.auth);
      if (!auth.agentId) {
        throw new ForbiddenError(
          "Scoped tokens can only be issued from an agent-scoped principal (sk_/ak_/scoped-token).",
        );
      }

      const agent = await context.db.agent.findFirst({
        where: { id: auth.agentId, orgId: auth.orgId },
        select: { id: true, did: true, privateKeyEnc: true },
      });
      if (!agent || !agent.did || !agent.privateKeyEnc) {
        throw new AppError(
          "FAILED_PRECONDITION",
          "Agent has no DID key — call identity.rotateKeys first.",
          412,
        );
      }

      // privateKeyEnc is JSON-stringified JWK in the existing identity flow.
      let privateKeyJwk: JsonWebKey;
      try {
        privateKeyJwk = JSON.parse(agent.privateKeyEnc) as JsonWebKey;
      } catch {
        throw new AppError("INTERNAL", "Agent private key malformed", 500);
      }

      const { token, payload } = issueScopedToken({
        privateKeyJwk,
        issuer: agent.did,
        subject: agent.id,
        audience: input.audience || EXPECTED_AUDIENCE,
        scopes: input.scopes,
        ttlSeconds: input.ttlSeconds ?? 300,
        parentJti: input.parentJti,
      });

      const record = await context.db.scopedToken.create({
        data: {
          jti: payload.jti,
          agentId: agent.id,
          orgId: auth.orgId,
          scopes: payload.scope,
          audience: payload.aud,
          parentJti: payload.parent_jti ?? null,
          expiresAt: new Date(payload.exp * 1000),
          metadata: (input.metadata ?? {}) as Prisma.InputJsonValue,
        },
      });

      return { token, record: mapScopedTokenToOutput(record) };
    }),

    list: os.scopedTokens.list.handler(async ({ input, context }) => {
      const auth = requireAuth(context.auth);
      const limit = input.limit;

      const where: Prisma.ScopedTokenWhereInput = { orgId: auth.orgId };
      if (input.agentId) where.agentId = input.agentId;
      if (!input.includeExpired) where.expiresAt = { gt: new Date() };

      const records = await context.db.scopedToken.findMany({
        where,
        orderBy: { id: "asc" },
        take: limit + 1,
        ...(input.cursor ? { cursor: { id: input.cursor }, skip: 1 } : {}),
      });

      const hasMore = records.length > limit;
      const items = records.slice(0, limit);

      return {
        items: items.map(mapScopedTokenToOutput),
        pagination: {
          nextCursor: hasMore ? (items[items.length - 1]?.id ?? null) : null,
          hasMore,
        },
      };
    }),

    revoke: os.scopedTokens.revoke.handler(async ({ input, context }) => {
      const auth = requireAuth(context.auth);
      const record = await context.db.scopedToken.findUnique({
        where: { jti: input.jti },
      });
      if (!record || record.orgId !== auth.orgId) {
        throw new AppError("NOT_FOUND", "Scoped token not found", 404);
      }

      await context.db.scopedToken.update({
        where: { jti: input.jti },
        data: { revokedAt: new Date() },
      });
      await context.db.revokedToken.upsert({
        where: { jti: input.jti },
        create: {
          jti: input.jti,
          expiresAt: record.expiresAt,
          reason: input.reason ?? null,
        },
        update: { reason: input.reason ?? null },
      });

      return { success: true as const, jti: input.jti };
    }),
  };
}
```

- [ ] **Step 3: Register the handlers in router**

Read `apps/api/src/router.ts` to see how handlers are wired:

```bash
grep -n "createWebhookHandlers\|webhook:" anima/apps/api/src/router.ts
```

Add the same pattern for `scopedTokens`:

```ts
import { createScopedTokensHandlers } from "./routes/handlers/scoped-tokens";

// inside the router builder:
scopedTokens: createScopedTokensHandlers(),
```

- [ ] **Step 4: Typecheck**

```bash
cd anima/apps/api && bun run typecheck
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add anima/apps/api/src/routes/handlers/scoped-tokens.ts anima/apps/api/src/router.ts anima/apps/api/src/routes/router-utils.ts
git commit -m "feat(api): scoped-tokens issue/list/revoke handlers"
```

---

## Task A7: Cleanup worker

**Files:**
- Create: `apps/api/src/workers/scoped-token-cleanup-worker.ts`
- Modify: `apps/api/src/workers/index.ts`

- [ ] **Step 1: Read an existing timer-based worker for reference**

```bash
sed -n '1,40p' anima/apps/api/src/workers/connect-link-cleanup-worker.ts
```

Note the export shape: `export function startConnectLinkCleanupWorker(prisma): () => void`.

- [ ] **Step 2: Write the worker**

Create `apps/api/src/workers/scoped-token-cleanup-worker.ts`:

```ts
/**
 * Scoped Token Cleanup Worker
 *
 * Every 5 minutes:
 *   1. Hard-delete `scoped_tokens` rows whose `expires_at` is in the past.
 *      Expired tokens cannot be redeemed (the JWT exp claim takes care of
 *      the verify-time check), so the row is just dead weight.
 *   2. Hard-delete `revoked_tokens` rows whose `expires_at` is in the past.
 *      A revoked token whose JWT has already expired cannot be replayed —
 *      the verify call would reject on `expired` before we reach the
 *      denylist lookup. Pruning these keeps the denylist small.
 */

import type { PrismaClient } from "@anima/db";

const INTERVAL_MS = 5 * 60 * 1000;

export function startScopedTokenCleanupWorker(db: PrismaClient): () => void {
  const tick = async () => {
    const now = new Date();
    try {
      const [expired, revokedExpired] = await Promise.all([
        db.scopedToken.deleteMany({
          where: { expiresAt: { lt: now } },
        }),
        db.revokedToken.deleteMany({
          where: { expiresAt: { lt: now } },
        }),
      ]);
      if (expired.count > 0 || revokedExpired.count > 0) {
        console.log(
          "[scoped-token-cleanup]",
          JSON.stringify({
            component: "scoped-token-cleanup",
            expiredScopedTokens: expired.count,
            expiredRevokedTokens: revokedExpired.count,
            timestamp: now.toISOString(),
          }),
        );
      }
    } catch (error) {
      console.error("[scoped-token-cleanup] failed:", error);
    }
  };

  // First run after a short delay so server start isn't slow.
  const initial = setTimeout(tick, 30_000);
  const interval = setInterval(tick, INTERVAL_MS);

  return () => {
    clearTimeout(initial);
    clearInterval(interval);
  };
}
```

- [ ] **Step 3: Register the worker**

Edit `apps/api/src/workers/index.ts:80` (after the `connectLinkCleanup` block, before the BullMQ section):

```ts
  try {
    const stopScopedTokenCleanup = startScopedTokenCleanupWorker(prisma);
    cleanups.push({ name: "scoped-token-cleanup", stop: stopScopedTokenCleanup });
    console.log("[workers] ✓ scoped-token-cleanup-worker started (5 min interval)");
  } catch (error) {
    console.error("[workers] ✗ scoped-token-cleanup-worker failed to start:", error);
  }
```

Add the import at the top:
```ts
import { startScopedTokenCleanupWorker } from "./scoped-token-cleanup-worker";
```

- [ ] **Step 4: Typecheck**

```bash
cd anima/apps/api && bun run typecheck
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add anima/apps/api/src/workers/scoped-token-cleanup-worker.ts anima/apps/api/src/workers/index.ts
git commit -m "feat(api): add scoped-token cleanup worker (5-min interval)"
```

---

## Task A8: Integration test

**Files:**
- Create: `apps/api/src/__tests__/integration/scoped-tokens-crud.test.ts`

- [ ] **Step 1: Read setup.ts for test fixtures**

```bash
sed -n '1,80p' anima/apps/api/src/__tests__/integration/setup.ts
```

- [ ] **Step 2: Write the integration test**

Create `apps/api/src/__tests__/integration/scoped-tokens-crud.test.ts`:

```ts
import { afterAll, beforeAll, describe, expect, it } from "bun:test";
import { generateKeyPair } from "@anima/agent-identity";

import { setupTestApp, teardownTestApp, type TestContext } from "./setup";

describe("scoped-tokens CRUD", () => {
  let ctx: TestContext;

  beforeAll(async () => {
    ctx = await setupTestApp();
  });

  afterAll(async () => {
    await teardownTestApp(ctx);
  });

  it("issues, lists, redeems, and revokes a scoped token", async () => {
    // 1. The test fixture provides a master key and an agent. We need the
    //    agent to have a DID + key. Use the existing rotateKeys procedure
    //    (no need to duplicate logic here) — or seed the keys directly.
    const { publicKeyJwk, privateKeyJwk } = generateKeyPair("Ed25519");
    await ctx.db.agent.update({
      where: { id: ctx.agentId },
      data: {
        did: `did:web:test.useanima.sh:${ctx.agentId}`,
        publicKey: JSON.stringify(publicKeyJwk),
        privateKeyEnc: JSON.stringify(privateKeyJwk),
      },
    });

    // 2. Issue a token via the contract
    const issueRes = await ctx.client.scopedTokens.issue({
      audience: "api.useanima.sh",
      scopes: ["email:send"],
      ttlSeconds: 60,
    });
    expect(issueRes.token.startsWith("stk_")).toBe(true);
    expect(issueRes.record.scopes).toEqual(["email:send"]);

    // 3. Use the token as Authorization header to call a cheap procedure
    const tokenAuthClient = ctx.makeClient(issueRes.token);
    const me = await tokenAuthClient.scopedTokens.list({});
    expect(me.items.length).toBeGreaterThanOrEqual(1);

    // 4. Revoke
    const revokeRes = await ctx.client.scopedTokens.revoke({
      jti: issueRes.record.jti,
    });
    expect(revokeRes.success).toBe(true);

    // 5. After revoke the token must NOT authenticate
    await expect(tokenAuthClient.scopedTokens.list({})).rejects.toThrow();
  });

  it("rejects a tampered token", async () => {
    const { publicKeyJwk, privateKeyJwk } = generateKeyPair("Ed25519");
    await ctx.db.agent.update({
      where: { id: ctx.agentId },
      data: {
        did: `did:web:test.useanima.sh:${ctx.agentId}`,
        publicKey: JSON.stringify(publicKeyJwk),
        privateKeyEnc: JSON.stringify(privateKeyJwk),
      },
    });

    const issueRes = await ctx.client.scopedTokens.issue({
      audience: "api.useanima.sh",
      scopes: ["email:send"],
      ttlSeconds: 60,
    });
    const tampered = `${issueRes.token.slice(0, -4)}AAAA`;
    const tamperedClient = ctx.makeClient(tampered);
    await expect(tamperedClient.scopedTokens.list({})).rejects.toThrow();
  });
});
```

- [ ] **Step 3: Run the test**

```bash
cd anima/apps/api && bun test src/__tests__/integration/scoped-tokens-crud.test.ts
```
Expected: PASS (2 cases).

> **NOTE:** If `setup.ts` does not yet expose `makeClient(token)`, add a small helper that returns a client built with that token in the Authorization header — the existing tests use this pattern; mirror them.

- [ ] **Step 4: Commit**

```bash
git add anima/apps/api/src/__tests__/integration/scoped-tokens-crud.test.ts
git commit -m "test(api): scoped-tokens CRUD integration test"
```

---

## Task A9: Public docs page

**Files:**
- Create: `docs/scoped-tokens.md`

- [ ] **Step 1: Write the docs**

Create `docs/scoped-tokens.md`:

```markdown
# Scoped Tokens

Scoped tokens (`stk_*`) are short-lived JWTs that grant a narrow slice of an
agent's authority to a downstream caller — a sub-agent, a tool, a third-party
service. They generalize the existing single-purpose vault tokens (`vtk_*`).

## Why

API keys (`sk_*`) carry the full set of scopes granted at key creation time.
That's right for a long-lived integration but wrong for a one-shot delegation
("let this tool send one email on my behalf for the next 60 seconds"). Scoped
tokens fill that gap.

## Lifecycle

1. **Issue** — `POST /scoped-tokens` with `{ audience, scopes, ttlSeconds, parentJti? }`.
   The API signs a JWT with the issuing agent's DID key (Ed25519) and persists
   the metadata. The raw `stk_<jwt>` is returned **once** — store it.
2. **Use** — Pass `Authorization: Bearer stk_<jwt>` to any API endpoint. The
   token is verified statelessly (signature + expiry) plus checked against
   the revocation denylist.
3. **Revoke** (optional) — `POST /scoped-tokens/revoke` with `{ jti }`. The
   jti is added to the denylist; subsequent use rejects.
4. **Expire** — Tokens self-expire via the JWT `exp` claim. A 5-minute worker
   prunes expired records and denylist entries.

## Token format

```
stk_<base64url(header)>.<base64url(payload)>.<base64url(signature)>
```

Decoded payload:

```json
{
  "iss": "did:web:useanima.sh:agent_xxx",
  "sub": "agent_xxx",
  "aud": "api.useanima.sh",
  "scope": ["email:send"],
  "iat": 1745000000,
  "exp": 1745000300,
  "jti": "deadbeef...",
  "parent_jti": "..."
}
```

## Scope grammar (v1)

`resource:action` strings drawn from the same `SCOPE_CATALOGUE` used by API
keys (e.g. `email:send`, `vault:read`). The wildcard `*` grants everything.

Resource-instance binding (e.g. `email:send:agent_xyz`) is a v2 feature.

## Delegation chains

The optional `parent_jti` claim references a parent token's jti, so an audit
log can reconstruct the chain (root agent → sub-agent → tool). v1 records
the chain but does not enforce scope subset between parent and child — that
check is FEATURE_DELEGATION_ENABLED (Track 2 T2.2).

## Limits

- Max TTL: 1 hour
- Min scope set: 1 scope (no empty-scope tokens)
- Tokens are bound to the issuing agent — only that agent's keys can verify.
```

- [ ] **Step 2: Commit**

```bash
git add docs/scoped-tokens.md
git commit -m "docs: scoped-tokens overview & lifecycle"
```

---

# PART B — Item 2: Webhook DLQ + glob filtering

## Task B1: WebhookDelivery DLQ columns + status enum

**Files:**
- Modify: `packages/db/prisma/schema.prisma:1242-1261`
- Create: `packages/db/prisma/migrations/20260501110000_add_webhook_dlq/migration.sql`

- [ ] **Step 1: Add status enum + columns to schema**

Edit `packages/db/prisma/schema.prisma` — at the bottom of the file (with the other enums), add:

```prisma
enum WebhookDeliveryStatus {
  PENDING       // initial state, awaiting first attempt
  IN_FLIGHT     // worker is currently delivering
  SUCCEEDED     // delivered with 2xx
  RETRYING      // last attempt failed but max not yet reached
  DEAD_LETTERED // exhausted retries, on the DLQ
}
```

Update the `WebhookDelivery` model (lines 1242-1261) to add:

```prisma
  status        WebhookDeliveryStatus @default(PENDING) @map("status")
  lastError     String?               @map("last_error") @db.Text
  deadLetteredAt DateTime?            @map("dead_lettered_at")
```

Place these fields after `completedAt`, before `createdAt`.

- [ ] **Step 2: Write the migration**

Create `packages/db/prisma/migrations/20260501110000_add_webhook_dlq/migration.sql`:

```sql
-- Webhook delivery status enum
CREATE TYPE "WebhookDeliveryStatus" AS ENUM (
  'PENDING',
  'IN_FLIGHT',
  'SUCCEEDED',
  'RETRYING',
  'DEAD_LETTERED'
);

-- Add status / last_error / dead_lettered_at to webhook_deliveries
ALTER TABLE "webhook_deliveries"
  ADD COLUMN "status" "WebhookDeliveryStatus" NOT NULL DEFAULT 'PENDING',
  ADD COLUMN "last_error" TEXT,
  ADD COLUMN "dead_lettered_at" TIMESTAMP(3);

-- Backfill: rows that already finished get SUCCEEDED, the rest stay PENDING.
-- (`completed_at IS NOT NULL` is the existing "delivered" signal.)
UPDATE "webhook_deliveries"
  SET "status" = 'SUCCEEDED'
  WHERE "completed_at" IS NOT NULL;

-- Index for DLQ console queries
CREATE INDEX "webhook_deliveries_status_idx" ON "webhook_deliveries"("status");
```

- [ ] **Step 3: Generate Prisma client and apply**

```bash
cd anima && bun run db:generate
bun run db:deploy
```
Expected: `Applying migration '20260501110000_add_webhook_dlq'` then `Database is now in sync`.

- [ ] **Step 4: Commit**

```bash
git add anima/packages/db/prisma/schema.prisma anima/packages/db/prisma/migrations/20260501110000_add_webhook_dlq
git commit -m "feat(db): webhook delivery DLQ columns + status enum"
```

---

## Task B2: Glob event matcher

**Files:**
- Create: `packages/shared/src/webhook-event-matcher.ts`
- Create: `packages/shared/src/__tests__/webhook-event-matcher.test.ts`
- Modify: `packages/shared/src/index.ts`

- [ ] **Step 1: Write the failing tests**

Create `packages/shared/src/__tests__/webhook-event-matcher.test.ts`:

```ts
import { describe, expect, it } from "bun:test";
import { matchesEventPattern, expandPatternToPrefixes } from "../webhook-event-matcher";

describe("matchesEventPattern", () => {
  it("exact match", () => {
    expect(matchesEventPattern("email.received", "email.received")).toBe(true);
    expect(matchesEventPattern("email.received", "email.sent")).toBe(false);
  });

  it("trailing wildcard", () => {
    expect(matchesEventPattern("email.*", "email.received")).toBe(true);
    expect(matchesEventPattern("email.*", "email.sent")).toBe(true);
    expect(matchesEventPattern("email.*", "phone.received")).toBe(false);
  });

  it("middle wildcard", () => {
    expect(matchesEventPattern("phone.*.failed", "phone.call.failed")).toBe(true);
    expect(matchesEventPattern("phone.*.failed", "phone.sms.failed")).toBe(true);
    expect(matchesEventPattern("phone.*.failed", "phone.call.completed")).toBe(false);
  });

  it("global wildcard", () => {
    expect(matchesEventPattern("*", "anything.at.all")).toBe(true);
  });

  it("rejects pattern with multiple consecutive dots", () => {
    expect(matchesEventPattern("a..b", "a.x.b")).toBe(false);
  });

  it("does not match across dot boundaries with single segment wildcard", () => {
    expect(matchesEventPattern("email.*", "email.transaction.declined")).toBe(false);
  });

  it("matches across boundaries with double wildcard", () => {
    expect(matchesEventPattern("email.**", "email.transaction.declined")).toBe(true);
    expect(matchesEventPattern("**", "anything.at.all")).toBe(true);
  });
});

describe("expandPatternToPrefixes", () => {
  it("returns the pattern itself when no wildcard", () => {
    expect(expandPatternToPrefixes("email.received")).toEqual(["email.received"]);
  });

  it("returns the prefix before the first wildcard", () => {
    expect(expandPatternToPrefixes("email.*")).toEqual(["email."]);
    expect(expandPatternToPrefixes("phone.*.failed")).toEqual(["phone."]);
  });

  it("returns empty for global wildcard (means scan everything)", () => {
    expect(expandPatternToPrefixes("*")).toEqual([]);
    expect(expandPatternToPrefixes("**")).toEqual([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd anima/packages/shared && bun test src/__tests__/webhook-event-matcher.test.ts
```
Expected: FAIL with "Cannot find module '../webhook-event-matcher'".

- [ ] **Step 3: Write the implementation**

Create `packages/shared/src/webhook-event-matcher.ts`:

```ts
/**
 * Webhook event glob matcher.
 *
 * Patterns:
 *   - Exact: "email.received" matches only "email.received"
 *   - Single-segment wildcard: "email.*" matches "email.received" and
 *     "email.sent" but NOT "email.transaction.declined" (the * is a
 *     single dot-separated segment).
 *   - Multi-segment wildcard: "email.**" matches anything under "email.".
 *   - Middle wildcard: "phone.*.failed" matches "phone.call.failed".
 *   - Global wildcard: "*" or "**" matches anything.
 *
 * Implementation note: we transform the pattern into a regex once per call.
 * Callers that need to match many events against the same pattern should
 * cache the regex themselves.
 */

const SEGMENT_RE = "[^.]+"; // one segment (no dots)
const ANY_RE = ".*"; // multi-segment

function patternToRegex(pattern: string): RegExp {
  // Reject patterns with empty segments (e.g. "a..b") — they're almost
  // always typos, and matching them against real events leads to surprises.
  const segments = pattern.split(".");
  if (segments.some((s) => s === "")) {
    return /(?!)/; // never matches
  }

  const parts = segments.map((s) => {
    if (s === "**") return ANY_RE;
    if (s === "*") return SEGMENT_RE;
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  });

  return new RegExp(`^${parts.join("\\.")}$`);
}

export function matchesEventPattern(pattern: string, event: string): boolean {
  return patternToRegex(pattern).test(event);
}

/**
 * Returns Postgres-friendly LIKE prefixes for a glob pattern, used to
 * narrow `events: { has: <prefix> }` queries before in-process matching.
 *
 * - "email.received"  -> ["email.received"]   (exact: no glob match needed)
 * - "email.*"         -> ["email."]
 * - "phone.*.failed" -> ["phone."]
 * - "*" / "**"        -> []                    (global: must scan all rows)
 */
export function expandPatternToPrefixes(pattern: string): string[] {
  const wildcardIdx = pattern.search(/\*/);
  if (wildcardIdx === -1) return [pattern];
  if (wildcardIdx === 0) return [];
  return [pattern.slice(0, wildcardIdx)];
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd anima/packages/shared && bun test src/__tests__/webhook-event-matcher.test.ts
```
Expected: PASS (10 cases).

- [ ] **Step 5: Export from package index**

Edit `packages/shared/src/index.ts` — append:

```ts
export * from "./webhook-event-matcher";
```

- [ ] **Step 6: Commit**

```bash
git add anima/packages/shared/src/webhook-event-matcher.ts anima/packages/shared/src/__tests__/webhook-event-matcher.test.ts anima/packages/shared/src/index.ts
git commit -m "feat(shared): glob event matcher for webhook patterns"
```

---

## Task B3: Use glob matcher when fanning out events

**Files:**
- Modify: `apps/api/src/routes/router-utils.ts:1531-1567`

- [ ] **Step 1: Update createWebhookDeliveriesForEvent**

In `apps/api/src/routes/router-utils.ts`, replace the body of `createWebhookDeliveriesForEvent` (lines 1531-1567):

```ts
import { matchesEventPattern } from "@anima/shared";

export async function createWebhookDeliveriesForEvent(params: {
  context: AppContext;
  orgId: string;
  event: WebhookEventName;
  messageId?: string;
  payload: Record<string, unknown>;
}): Promise<void> {
  // Pull all active webhooks for the org. Postgres `events: { has: x }` only
  // works for exact strings, but our `events` array now contains globs
  // ("email.*", "*", "phone.*.failed") so we can't push the filter down.
  // Org-level webhook counts are tiny in practice (low double digits) — we
  // pull and filter in-process. If this becomes hot, narrow with a prefix
  // pre-filter using `expandPatternToPrefixes`.
  const webhooks = await params.context.db.webhook.findMany({
    where: {
      orgId: params.orgId,
      active: true,
    },
  });

  const matching = webhooks.filter((w) =>
    w.events.some((pattern) => matchesEventPattern(pattern, params.event)),
  );

  if (matching.length === 0) return;

  const queue = createWebhookDeliveryQueue();
  for (const webhook of matching) {
    const delivery = await params.context.db.webhookDelivery.create({
      data: {
        webhookId: webhook.id,
        messageId: params.messageId ?? null,
        event: params.event,
        payload: params.payload as Prisma.InputJsonValue,
        attempts: 0,
        maxAttempts: 3,
        status: "PENDING",
      },
    });

    if (queue) {
      await queue.add("deliver", { deliveryId: delivery.id });
    }
  }
}
```

- [ ] **Step 2: Update the inbound-email worker filter**

`apps/api/src/workers/inbound-email.ts:52` currently uses `events: { has: "message.received" }`. Replace it with the same fan-out pattern. Since this worker already has the org id and event name, refactor to call `createWebhookDeliveriesForEvent` if not already, or inline the same `findMany + filter` pattern.

```bash
grep -n "events: { has:" anima/apps/api/src/workers/inbound-email.ts
```

Update each call site identified.

- [ ] **Step 3: Typecheck**

```bash
cd anima && bun run typecheck
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add anima/apps/api/src/routes/router-utils.ts anima/apps/api/src/workers/inbound-email.ts
git commit -m "feat(webhooks): glob event filtering across fan-out call sites"
```

---

## Task B4: Loosen WebhookEventSchema to accept globs

**Files:**
- Modify: `packages/contracts/src/schemas/webhook.ts:1-22`

- [ ] **Step 1: Replace the enum with a glob-aware schema**

In `packages/contracts/src/schemas/webhook.ts`, replace `WebhookEventSchema`:

```ts
const KNOWN_EVENT_NAMES = [
  "message.received",
  "message.sent",
  "message.failed",
  "message.bounced",
  "agent.created",
  "agent.updated",
  "agent.deleted",
  "phone.provisioned",
  "phone.released",
  "call.summary.ready",
  "call.score.ready",
  "call.security.alert",
  "call.security.scan.ready",
  "call.started",
  "call.ended",
] as const;

export const KnownWebhookEventName = z.enum(KNOWN_EVENT_NAMES);
export type WebhookEventName = z.infer<typeof KnownWebhookEventName>;

/**
 * Accepts either a known event name or a glob pattern (`email.*`,
 * `phone.*.failed`, `*`). Validation only checks shape — semantic
 * matching happens at delivery fan-out time.
 */
export const WebhookEventSchema = z
  .string()
  .min(1)
  .max(100)
  .regex(
    /^[a-z0-9*]+(\.[a-z0-9*]+)*$/,
    "Must be a dot-separated event name or glob pattern (lowercase, digits, dots, *)",
  )
  .describe(
    "Event name or glob pattern. Examples: 'email.received', 'email.*', 'phone.*.failed', '*'.",
  );
```

Anywhere else in this file (or the whole package) that imports `WebhookEventSchema` and consumes it as an enum needs updating to use `KnownWebhookEventName` if it specifically wants the closed set.

- [ ] **Step 2: Add status / lastError / deadLetteredAt to WebhookDeliveryOutput**

In the same file, update `WebhookDeliveryOutput` (around line 104):

```ts
  status: z
    .enum(["PENDING", "IN_FLIGHT", "SUCCEEDED", "RETRYING", "DEAD_LETTERED"])
    .describe("Lifecycle status of this delivery attempt"),
  lastError: z
    .string()
    .nullable()
    .describe("Last error message if the delivery is retrying or dead-lettered"),
  deadLetteredAt: z
    .string()
    .datetime()
    .nullable()
    .describe("When the delivery moved to the DLQ (null if still in flight or succeeded)"),
```

- [ ] **Step 3: Add ReplayWebhookDeliveryInput / Output**

Append at the end of the file:

```ts
export const ReplayWebhookDeliveryInput = z
  .object({
    deliveryId: z.string().cuid2().describe("Delivery to re-enqueue"),
  })
  .describe("Replay a dead-lettered webhook delivery");

export const ReplayWebhookDeliveryOutput = z
  .object({
    success: z.literal(true),
    deliveryId: z.string().cuid2(),
  })
  .describe("Replay confirmation");
```

- [ ] **Step 4: Update mapping helper**

`apps/api/src/routes/router-utils.ts` has `mapWebhookDeliveryToOutput`. Find it and update so it returns the new fields:

```bash
grep -n "mapWebhookDeliveryToOutput" anima/apps/api/src/routes/router-utils.ts
```

Inside the function, add:

```ts
    status: delivery.status,
    lastError: delivery.lastError,
    deadLetteredAt: delivery.deadLetteredAt?.toISOString() ?? null,
```

- [ ] **Step 5: Typecheck**

```bash
cd anima && bun run typecheck
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add anima/packages/contracts/src/schemas/webhook.ts anima/apps/api/src/routes/router-utils.ts
git commit -m "feat(contracts): webhook event globs + DLQ fields on delivery output"
```

---

## Task B5: Update delivery worker to set status + dead-letter

**Files:**
- Modify: `apps/api/src/workers/webhook-delivery.ts`

- [ ] **Step 1: Define the DLQ queue name**

Near the top of `apps/api/src/workers/webhook-delivery.ts` (line 7-13), add:

```ts
const WEBHOOK_DEAD_LETTER_QUEUE = "webhook-dead-letter";
```

Then add a queue factory (mirroring `createWebhookDeliveryQueue`):

```ts
export function createWebhookDeadLetterQueue(): Queue<WebhookDeliveryJobData> | null {
  const connection = getRedisConnection();
  if (!connection) return null;
  return new Queue<WebhookDeliveryJobData>(WEBHOOK_DEAD_LETTER_QUEUE, { connection });
}
```

- [ ] **Step 2: Add status updates on every transition**

Modify `executeDelivery` (lines 202-380):

- On the `if (response.ok)` success branch (around line 237-247), add `status: "SUCCEEDED"` to the update.
- On the retry branch (around line 263-275), set `status: "RETRYING"` and `lastError: response.statusCode ? \`HTTP ${response.statusCode}\` : null`.
- On the exhausted branch (around line 289-298), set `status: "DEAD_LETTERED"`, `deadLetteredAt: new Date()`, `lastError: <truncated body>`.

Specifically, the exhausted update should also enqueue to the DLQ:

```ts
      const dlq = createWebhookDeadLetterQueue();
      await db.webhookDelivery.update({
        where: { id: delivery.id },
        data: {
          attempts: nextAttempts,
          statusCode: response.status,
          responseBody,
          nextAttemptAt: null,
          completedAt: null,
          status: "DEAD_LETTERED",
          deadLetteredAt: new Date(),
          lastError: responseBody,
        },
      });
      if (dlq) {
        await dlq.add("dead_letter", { deliveryId: delivery.id });
      }
```

The catch-block (network failure) exhausted branch around line 349-358 needs the same treatment.

- [ ] **Step 3: Set IN_FLIGHT at the start of executeDelivery**

After the `findUnique` (around line 210), before the fetch, add:

```ts
  await db.webhookDelivery.update({
    where: { id: deliveryId },
    data: { status: "IN_FLIGHT" },
  });
```

- [ ] **Step 4: Typecheck**

```bash
cd anima/apps/api && bun run typecheck
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add anima/apps/api/src/workers/webhook-delivery.ts
git commit -m "feat(webhooks): track delivery status + push exhausted to DLQ"
```

---

## Task B6: Dead-letter worker

**Files:**
- Create: `apps/api/src/workers/webhook-dead-letter.ts`
- Modify: `apps/api/src/workers/index.ts`

- [ ] **Step 1: Write the worker**

Create `apps/api/src/workers/webhook-dead-letter.ts`:

```ts
/**
 * Webhook Dead-Letter Worker
 *
 * Consumes the `webhook-dead-letter` queue. The worker does NOT retry —
 * its purpose is to record / observe / alert on permanently failed
 * deliveries. Replay is an explicit user action via the console UI
 * (see webhook.replayDelivery handler).
 *
 * Today the worker just logs and counts. We can later wire this into
 * Slack/email/PagerDuty alerts without changing the queue contract.
 */

import type { PrismaClient } from "@anima/db";
import { Queue, Worker } from "bullmq";

const WEBHOOK_DEAD_LETTER_QUEUE = "webhook-dead-letter";

export interface WebhookDeadLetterJobData {
  deliveryId: string;
}

function getRedisConnection(): { url: string } | null {
  const redisUrl = process.env.REDIS_URL;
  if (!redisUrl) return null;
  return { url: redisUrl };
}

export function createWebhookDeadLetterWorker(
  db: PrismaClient,
): Worker<WebhookDeadLetterJobData> {
  const connection = getRedisConnection();
  if (!connection) {
    throw new Error("REDIS_URL is required to create webhook dead-letter worker");
  }

  return new Worker<WebhookDeadLetterJobData>(
    WEBHOOK_DEAD_LETTER_QUEUE,
    async (job) => {
      const delivery = await db.webhookDelivery.findUnique({
        where: { id: job.data.deliveryId },
        include: { webhook: { select: { id: true, url: true, orgId: true } } },
      });
      if (!delivery) return;

      console.warn(
        "[webhook-dead-letter]",
        JSON.stringify({
          component: "webhook-dead-letter",
          deliveryId: delivery.id,
          webhookId: delivery.webhookId,
          orgId: delivery.webhook.orgId,
          url: delivery.webhook.url,
          event: delivery.event,
          attempts: delivery.attempts,
          lastError: delivery.lastError,
          deadLetteredAt: delivery.deadLetteredAt?.toISOString(),
          timestamp: new Date().toISOString(),
        }),
      );
    },
    { connection },
  );
}
```

- [ ] **Step 2: Register in workers/index.ts**

After `createWebhookDeliveryWorker` (line 100), add:

```ts
  try {
    const worker = createWebhookDeadLetterWorker(prisma);
    cleanups.push({ name: "webhook-dead-letter", stop: () => worker.close() });
    console.log("[workers] ✓ webhook-dead-letter-worker started");
  } catch (error) {
    console.error("[workers] ✗ webhook-dead-letter-worker failed to start:", error);
  }
```

Add the import:

```ts
import { createWebhookDeadLetterWorker } from "./webhook-dead-letter";
```

- [ ] **Step 3: Commit**

```bash
git add anima/apps/api/src/workers/webhook-dead-letter.ts anima/apps/api/src/workers/index.ts
git commit -m "feat(webhooks): dead-letter worker for exhausted deliveries"
```

---

## Task B7: Replay handler + console UI

**Files:**
- Modify: `packages/contracts/src/contracts/webhook.ts`
- Modify: `packages/contracts/src/scopes.ts`
- Modify: `apps/api/src/routes/handlers/webhook.ts`
- Modify: `apps/console/src/components/webhooks/webhook-delivery-log.tsx`

- [ ] **Step 1: Add replay procedure to the contract**

Append to `packages/contracts/src/contracts/webhook.ts` inside the router (before the closing `})`):

```ts
import { ReplayWebhookDeliveryInput, ReplayWebhookDeliveryOutput } from "../schemas/webhook";

// ...

  replayDelivery: oc
    .route({ method: "POST", path: "/webhooks/deliveries/{deliveryId}/replay" })
    .input(ReplayWebhookDeliveryInput)
    .output(ReplayWebhookDeliveryOutput),
```

- [ ] **Step 2: Register scope**

Edit `packages/contracts/src/scopes.ts` — in the Webhooks section of `PROCEDURE_SCOPE_MAP`:

```ts
  "webhook.replayDelivery": ["webhooks:write"],
```

- [ ] **Step 3: Add the handler**

In `apps/api/src/routes/handlers/webhook.ts`, after the `stats` handler (line 273-301), add:

```ts
    replayDelivery: os.webhook.replayDelivery.handler(async ({ input, context }) => {
      const auth = requireMaster(context.auth);
      const delivery = await context.db.webhookDelivery.findFirst({
        where: { id: input.deliveryId },
        include: { webhook: { select: { orgId: true } } },
      });
      if (!delivery || delivery.webhook.orgId !== auth.orgId) {
        throw new AppError("NOT_FOUND", "Delivery not found", 404);
      }
      if (delivery.status !== "DEAD_LETTERED") {
        throw new AppError(
          "BAD_REQUEST",
          "Only dead-lettered deliveries can be replayed",
          400,
        );
      }

      // Reset to PENDING with a fresh attempt budget. We do NOT clear the
      // historical attempts/lastError fields — they're audit data — instead
      // we reset the counters on the row that gets re-delivered.
      await context.db.webhookDelivery.update({
        where: { id: delivery.id },
        data: {
          status: "PENDING",
          attempts: 0,
          completedAt: null,
          deadLetteredAt: null,
          nextAttemptAt: null,
        },
      });

      const queue = createWebhookDeliveryQueue();
      if (queue) {
        await queue.add("deliver", { deliveryId: delivery.id });
      }

      return { success: true as const, deliveryId: delivery.id };
    }),
```

- [ ] **Step 4: Add the Replay button to the console**

Read the existing delivery log component:

```bash
sed -n '1,60p' anima/apps/console/src/components/webhooks/webhook-delivery-log.tsx
```

Note the row rendering pattern. Add (a) a status badge column showing `delivery.status` with appropriate color (green for SUCCEEDED, red for DEAD_LETTERED, yellow for RETRYING, gray for PENDING/IN_FLIGHT), and (b) a "Replay" button on rows where `delivery.status === "DEAD_LETTERED"`.

The mutation:

```tsx
const replayDelivery = useMutation({
  ...orpc.webhook.replayDelivery.mutationOptions(),
  onSuccess: () => {
    toast.success("Delivery re-enqueued");
    queryClient.invalidateQueries({ queryKey: orpc.webhook.listDeliveries.key() });
  },
  onError: (error) => toast.error(`Replay failed: ${error.message}`),
});
```

The button:

```tsx
{delivery.status === "DEAD_LETTERED" && (
  <button
    type="button"
    onClick={() => replayDelivery.mutate({ deliveryId: delivery.id })}
    disabled={replayDelivery.isPending}
    className="px-2 py-1 text-xs font-mono bg-accent text-bg hover:bg-accent-hover"
  >
    Replay
  </button>
)}
```

- [ ] **Step 5: Typecheck**

```bash
cd anima && bun run typecheck
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add anima/packages/contracts/src/contracts/webhook.ts anima/packages/contracts/src/scopes.ts anima/apps/api/src/routes/handlers/webhook.ts anima/apps/console/src/components/webhooks/webhook-delivery-log.tsx
git commit -m "feat(webhooks): replay dead-lettered deliveries from console"
```

---

## Task B8: Webhook DLQ integration test

**Files:**
- Create: `apps/api/src/__tests__/integration/webhook-dlq.test.ts`

- [ ] **Step 1: Write the integration test**

Create `apps/api/src/__tests__/integration/webhook-dlq.test.ts`:

```ts
import { afterAll, beforeAll, describe, expect, it } from "bun:test";

import { setupTestApp, teardownTestApp, type TestContext } from "./setup";

describe("webhook DLQ + glob filtering", () => {
  let ctx: TestContext;

  beforeAll(async () => {
    ctx = await setupTestApp();
  });

  afterAll(async () => {
    await teardownTestApp(ctx);
  });

  it("creates a webhook with a glob pattern", async () => {
    const result = await ctx.client.webhook.create({
      url: "https://example.invalid/hook",
      events: ["email.*"],
    });
    expect(result.events).toEqual(["email.*"]);
  });

  it("rejects malformed glob patterns", async () => {
    await expect(
      ctx.client.webhook.create({
        url: "https://example.invalid/hook",
        events: ["EMAIL.received"], // uppercase rejected
      }),
    ).rejects.toThrow();
  });

  it("replay rejects non-dead-lettered deliveries", async () => {
    const webhook = await ctx.client.webhook.create({
      url: "https://example.invalid/hook",
      events: ["message.received"],
    });

    // Seed a SUCCEEDED delivery directly
    const delivery = await ctx.db.webhookDelivery.create({
      data: {
        webhookId: webhook.id,
        event: "message.received",
        payload: {},
        attempts: 1,
        maxAttempts: 3,
        status: "SUCCEEDED",
        completedAt: new Date(),
      },
    });

    await expect(
      ctx.client.webhook.replayDelivery({ deliveryId: delivery.id }),
    ).rejects.toThrow(/dead-lettered/i);
  });

  it("replay re-enqueues a dead-lettered delivery", async () => {
    const webhook = await ctx.client.webhook.create({
      url: "https://example.invalid/hook",
      events: ["message.received"],
    });
    const delivery = await ctx.db.webhookDelivery.create({
      data: {
        webhookId: webhook.id,
        event: "message.received",
        payload: {},
        attempts: 3,
        maxAttempts: 3,
        status: "DEAD_LETTERED",
        deadLetteredAt: new Date(),
        lastError: "boom",
      },
    });

    const result = await ctx.client.webhook.replayDelivery({
      deliveryId: delivery.id,
    });
    expect(result.success).toBe(true);

    const reloaded = await ctx.db.webhookDelivery.findUnique({
      where: { id: delivery.id },
    });
    expect(reloaded?.status).toBe("PENDING");
    expect(reloaded?.attempts).toBe(0);
    expect(reloaded?.deadLetteredAt).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test**

```bash
cd anima/apps/api && bun test src/__tests__/integration/webhook-dlq.test.ts
```
Expected: PASS (4 cases).

- [ ] **Step 3: Commit**

```bash
git add anima/apps/api/src/__tests__/integration/webhook-dlq.test.ts
git commit -m "test(api): webhook DLQ + glob filtering integration tests"
```

---

## Self-Review Checklist (run before declaring complete)

- [ ] **Run the full test suite**: `cd anima && bun test` — every `bun test` in the new tasks must pass.
- [ ] **Lint**: `cd anima && bun run lint` — biome must be clean.
- [ ] **Typecheck the whole repo**: `cd anima && bun run typecheck` — no errors.
- [ ] **Manual smoke**: Start the API + console (`bun run dev:api`, `bun run dev:console`), create a webhook with `email.*`, send a test event, verify a delivery appears with status PENDING → SUCCEEDED in the UI. Manually mark a delivery as DEAD_LETTERED in the DB and verify the Replay button works.
- [ ] **Migrations applied cleanly**: Drop & recreate the test DB, run `bun run db:deploy`, verify both new migrations apply without error.

## Out of scope (intentional v2 work)

- Resource-instance binding in scopes (`email:send:agent_xyz`) — keeps v1 shippable.
- Parent/child scope subset enforcement — gated behind `FEATURE_DELEGATION_ENABLED`.
- DLQ alerting (Slack/PagerDuty hooks on dead-lettered events) — worker just logs today.
- Per-route configurable max retries (currently hard-coded to 3 at create time).
- DLQ metrics / Grafana dashboard.
