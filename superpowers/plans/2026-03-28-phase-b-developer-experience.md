# Phase B — Developer Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate DX to best-in-class. Make it frictionless for any developer using any AI framework. Real-time events, first-class addresses, framework integrations, registry discoverability.

**Architecture:** Multi-repo at `/Users/diyanbogdanov/projects/agenticmail/`. Platform at `anima/`, SDKs at `python/` and `node/`, toolkit at `toolkit/`, skill at `skill/`, MCP at `mcp/`, CLI at `cli/`, docs at `docs/`.

**Tech Stack:** TypeScript (Bun), Python, Hono, oRPC, Prisma, WebSockets, Commander.js

**Spec:** `docs/superpowers/specs/2026-03-28-anima-platform-roadmap-design.md` (Phase B section)

**Depends on:** Phase A complete (verified)

---

## Task 1: WebSocket Server Endpoint (B1 — Part 1)

**Files:**
- Create: `anima/packages/contracts/src/contracts/events.ts`
- Create: `anima/packages/contracts/src/schemas/events.ts`
- Modify: `anima/packages/contracts/src/contracts/index.ts`
- Modify: `anima/apps/api/src/server.ts`
- Create: `anima/apps/api/src/ws/event-hub.ts`
- Create: `anima/apps/api/src/ws/channel-matcher.ts`

- [ ] **Step 1: Define event schemas and types**

Create `anima/packages/contracts/src/schemas/events.ts` with:
- Event type enum: `email.received`, `email.sent`, `email.delivered`, `email.bounced`, `sms.received`, `sms.sent`, `vault.credential.accessed`, `vault.credential.created`, `approval.requested`, `approval.decided`, `security.pii_detected`, `security.injection_detected`
- Event payload schema (Zod): `{ id: string, type: EventType, agentId: string, orgId: string, timestamp: string, data: Record<string, unknown> }`
- Subscription request: `{ channels: string[] }` — supports wildcards like `email.*`, `*`
- Last-Event-ID for reconnection recovery

- [ ] **Step 2: Create channel matcher utility**

Create `anima/apps/api/src/ws/channel-matcher.ts`:
- `matchChannel(pattern: string, eventType: string): boolean`
- Support patterns: `*` (all), `email.*` (namespace wildcard), `email.received` (exact), `agent:<id>:email.*` (agent-scoped)
- Unit-testable pure function

- [ ] **Step 3: Create EventHub class**

Create `anima/apps/api/src/ws/event-hub.ts`:
- Singleton EventHub that manages all WebSocket connections
- `subscribe(ws, channels, orgId, lastEventId?)` — register a connection with channel subscriptions
- `unsubscribe(ws)` — clean up on disconnect
- `publish(event)` — fan out event to matching subscriptions
- In-memory event buffer (last 1000 events per org) for missed event recovery
- When a client connects with `lastEventId`, replay missed events before streaming live

- [ ] **Step 4: Add WebSocket endpoint to API server**

Modify `anima/apps/api/src/server.ts`:
- Add Hono WebSocket upgrade at `/ws` path
- On connection: authenticate via API key (query param `?apiKey=` or first message)
- On message: parse subscription requests, add/remove channel subscriptions
- On close: clean up subscription
- On error: log and clean up
- Reference: Hono WebSocket docs for Bun runtime

- [ ] **Step 5: Wire event publishing into existing services**

Add `eventHub.publish()` calls in the relevant API handlers. For each operation that already fires webhooks, also publish to the EventHub:
- Email send/receive handlers → `email.sent`, `email.received`
- Vault access handlers → `vault.credential.accessed`
- Security event handlers → `security.*`

Pattern: find existing webhook dispatch code and add parallel EventHub publish.

- [ ] **Step 6: Tests**

Create `anima/apps/api/src/__tests__/unit/event-hub.test.ts`:
- Channel matching tests (exact, wildcard, agent-scoped)
- Subscribe/unsubscribe lifecycle
- Event fanout to matching subscriptions
- Missed event recovery (connect with lastEventId)
- Authentication required before receiving events

---

## Task 2: WebSocket SDK Support (B1 — Part 2)

**Files:**
- Create: `node/src/resources/events.ts`
- Modify: `node/src/index.ts`
- Create: `python/src/anima/resources/events.py`
- Modify: `python/src/anima/__init__.py`

- [ ] **Step 1: TypeScript SDK — events resource**

Create `node/src/resources/events.ts`:
```ts
// Usage: anima.events.subscribe(['email.*'], (event) => { ... })
// Returns unsubscribe function
// Auto-reconnects with lastEventId on disconnect
```

Key implementation:
- Uses native WebSocket (Node 18+) or `ws` package
- Takes `channels: string[]` and `callback: (event) => void`
- Handles auth, reconnection with exponential backoff, lastEventId
- Returns `{ unsubscribe(): void }`

- [ ] **Step 2: Python SDK — events resource**

Create `python/src/anima/resources/events.py`:
```python
# Sync: for event in anima.events.subscribe(['email.*']):
# Async: async for event in anima.events.subscribe(['email.*']):
```

Key implementation:
- Uses `websockets` library
- Async iterator pattern for `AsyncAnima`
- Threaded iterator pattern for sync `Anima`
- Auto-reconnection with lastEventId

- [ ] **Step 3: Add MCP tools for event management**

Add to `mcp/src/tools/`:
- `subscribe_events` tool — returns a session-scoped event stream
- `list_event_types` tool — returns all available event types
- Note: MCP tool can't keep a persistent stream, so this tool would return recent events or wait for next event with timeout

- [ ] **Step 4: Tests**

- Node: `node/src/__tests__/events.test.ts` — mock WebSocket, test subscribe/unsubscribe/reconnect
- Python: `python/tests/test_events.py` — mock WebSocket, test iterator patterns

---

## Task 3: Agent Address — Database & API (B3 — Part 1)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma`
- Create: `anima/packages/contracts/src/schemas/address.ts`
- Create: `anima/packages/contracts/src/contracts/address.ts`
- Modify: `anima/packages/contracts/src/contracts/index.ts`
- Create: `anima/apps/api/src/routes/address.ts`

- [ ] **Step 1: Prisma schema — AddressIdentity model**

Add to `anima/packages/db/prisma/schema.prisma`:
```prisma
enum AddressType {
  BILLING
  SHIPPING
  MAILING
  REGISTERED
}

model AddressIdentity {
  id          String      @id @default(cuid())
  agentId     String
  agent       Agent       @relation(fields: [agentId], references: [id], onDelete: Cascade)
  orgId       String
  org         Organization @relation(fields: [orgId], references: [id])
  type        AddressType
  label       String?
  street1     String
  street2     String?
  city        String
  state       String
  postalCode  String
  country     String      @db.Char(2) // ISO 3166-1 alpha-2
  validated   Boolean     @default(false)
  validatedAt DateTime?
  provider    String?     // USPS, GOOGLE, SMARTY
  metadata    Json?
  primary     Boolean     @default(false)
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt

  @@unique([agentId, type, primary], name: "one_primary_per_type")
  @@index([orgId])
  @@index([agentId])
}
```

Add relation to Agent model: `addresses AddressIdentity[]`
Add relation to Organization model: `addresses AddressIdentity[]`

- [ ] **Step 2: Run migration**

```bash
cd anima && bunx prisma migrate dev --name add-address-identity
```

- [ ] **Step 3: oRPC contract and schemas**

Create `anima/packages/contracts/src/schemas/address.ts` with Zod schemas:
- `CreateAddressInput`: agentId, type, label?, street1, street2?, city, state, postalCode, country
- `UpdateAddressInput`: all optional except id
- `AddressOutput`: full address with validation fields
- `ListAddressesInput`: agentId, type?
- `ValidateAddressInput`: agentId, addressId

Create `anima/packages/contracts/src/contracts/address.ts`:
- `create`: POST /v1/agents/:agentId/addresses
- `list`: GET /v1/agents/:agentId/addresses
- `get`: GET /v1/agents/:agentId/addresses/:id
- `update`: PUT /v1/agents/:agentId/addresses/:id
- `delete`: DELETE /v1/agents/:agentId/addresses/:id
- `validate`: POST /v1/agents/:agentId/addresses/:id/validate

Add to contracts index.

- [ ] **Step 4: API route handlers**

Create `anima/apps/api/src/routes/address.ts`:
- Standard CRUD following existing patterns (see agent.ts, vault.ts)
- Enforce one primary per type per agent
- Address creation normalizes country to uppercase ISO 3166-1
- Validate endpoint calls validation provider and updates validated/validatedAt

- [ ] **Step 5: Address validation service**

Create `anima/packages/core/src/services/address-validation.ts`:
- Abstract `AddressValidator` interface: `validate(address): Promise<ValidationResult>`
- `SmartyValidator` implementation (US addresses)
- `NoopValidator` fallback (marks as unvalidated, for dev/testing)
- Return: `{ valid: boolean, standardized: Address, confidence: number, suggestions: Address[] }`
- Config: `ADDRESS_VALIDATION_PROVIDER` env var, default `noop`

---

## Task 4: Agent Address — SDK, MCP, CLI (B3 — Part 2)

**Files:**
- Create: `node/src/resources/addresses.ts`
- Modify: `node/src/index.ts`
- Create: `python/src/anima/resources/addresses.py`
- Modify: `python/src/anima/__init__.py`
- Create: `mcp/src/tools/address/index.ts`
- Modify: `mcp/src/index.ts`
- Create: `cli/src/commands/address/`

- [ ] **Step 1: Node SDK — addresses resource**

Create `node/src/resources/addresses.ts`:
- `create(params)`, `list(params)`, `get(params)`, `update(params)`, `delete(params)`, `validate(params)`
- Follow existing resource patterns (see vault.ts)
- Export from index.ts as `anima.addresses`

- [ ] **Step 2: Python SDK — addresses resource**

Create `python/src/anima/resources/addresses.py`:
- Same methods as Node SDK
- Both sync and async variants
- Export from __init__.py

- [ ] **Step 3: MCP tools**

Create `mcp/src/tools/address/index.ts`:
- `create_address`, `list_addresses`, `get_address`, `update_address`, `delete_address`, `validate_address`
- Register in `mcp/src/index.ts` tool groups
- Update `--tools` flag to include `address` group

- [ ] **Step 4: CLI commands**

Create `cli/src/commands/address/`:
- `create.ts`, `list.ts`, `get.ts`, `delete.ts`, `validate.ts`
- Follow existing command patterns (see webhook/, security/)
- Register in `cli/src/cli.ts`

- [ ] **Step 5: Console page**

Create address management page at `anima/apps/console/src/app/(dashboard)/addresses/page.tsx`:
- List addresses with type badges, validation status
- Create/edit dialog
- Validate button
- Follow existing console patterns (see vault/page.tsx)

- [ ] **Step 6: Documentation**

Create `docs/docs/quickstart-address.mdx`:
- Quick example of creating and validating an address
- Both Python and Node code samples

Update `docs/docs/meta.json` to add quickstart-address.

---

## Task 5: Framework Integration — LangChain Expansion (B4 — Part 1)

**Files:**
- Modify: `toolkit/langchain/`
- Focus: Expand from email-only to full unified surface

- [ ] **Step 1: Audit existing LangChain tools**

Read `toolkit/langchain/` — document which tools exist and what they cover.

- [ ] **Step 2: Add missing tool definitions**

Add tools for the full surface:
- Vault: `StoreCredentialTool`, `GetCredentialTool`, `ListCredentialsTool`, `GeneratePasswordTool`
- Phone: `ProvisionPhoneTool`, `SendSmsTool`, `ListPhonesTool`
- Address: `CreateAddressTool`, `ListAddressesTool`, `ValidateAddressTool`

Each tool should follow LangChain `BaseTool` pattern with `name`, `description`, `args_schema`, `_run()`.

- [ ] **Step 3: Update package and publish**

Update `pyproject.toml` or `setup.py`:
- Package name: `anima-toolkit-langchain`
- Add new dependencies if needed
- Bump version

- [ ] **Step 4: Tests and docs**

Add tests for new tools. Update README with full tool reference.

---

## Task 6: Framework Integration — Claude Code Skill (B4 — Part 2)

**Files:**
- Modify: `skill/SKILL.md`

- [ ] **Step 1: Audit skill for address coverage**

Read `skill/SKILL.md`. Verify it covers: email, phone, vault, x402.
Check if address tools are missing (they should be, since address is new in B3).

- [ ] **Step 2: Add address section to SKILL.md**

Add address management tools section:
- `create_address`, `list_addresses`, `get_address`, `update_address`, `delete_address`, `validate_address`
- Include workflow examples: "Create address → use across email and phone"

- [ ] **Step 3: Update package version and tests**

Bump version in `skill/package.json`. Update test file to verify address tools are documented.

---

## Task 7: Framework Integration — OpenClaw Plugin (B4 — Part 3)

**Files:**
- Create: `toolkit/openclaw/`

- [ ] **Step 1: Research OpenClaw plugin format**

Check https://github.com/openclaw/openclaw for plugin structure. Determine:
- Plugin manifest format
- How tools/capabilities are registered
- Authentication pattern
- Multi-channel support requirements

- [ ] **Step 2: Create Anima plugin for OpenClaw**

Create `toolkit/openclaw/`:
- Plugin manifest (JSON or YAML per OpenClaw spec)
- Tool definitions covering full Anima surface: email, phone, vault, address
- Configuration: API key injection via OpenClaw config
- Agent identity provisioning: when an OpenClaw agent connects Anima, it auto-creates an Anima agent

- [ ] **Step 3: Documentation**

Create `toolkit/openclaw/README.md`:
- Installation and configuration
- "Give your OpenClaw agents real-world identity with Anima"
- Example: OpenClaw agent that receives a message on Telegram → uses Anima vault credentials and SMS

---

## Task 8: Framework Integration — Codex, OpenCode (B4 — Part 4)

**Files:**
- Create: `toolkit/codex/`
- Modify: `opencode/` (if exists)

- [ ] **Step 1: Codex tool definitions**

Create `toolkit/codex/`:
- `package.json`: `@anima-labs/toolkit-codex`
- Tool definitions in Codex-compatible function calling format
- Full surface: email, phone, vault, address
- Each tool: name, description, parameters (JSON Schema), implementation

- [ ] **Step 2: OpenCode integration**

Audit `opencode/` directory. Expand integration to cover full unified surface.
Add address tools alongside existing capabilities.

- [ ] **Step 3: Documentation and README for each**

---

## Task 9: Framework Integration — Claude Cowork (B4 — Part 5)

**Files:**
- Create: `toolkit/cowork/` or integration docs

- [ ] **Step 1: Research Cowork integration surface**

Check if Claude Cowork (https://claude.ai/cowork) has a public API or integration surface.
If not yet public: create documentation and config templates that will be ready when it launches.

- [ ] **Step 2: Create integration**

If API is available:
- MCP server connection config for Cowork workspaces
- Documentation: "How to give your Cowork agents real-world identity"
- Example: Multi-agent Cowork session for purchasing

If API is not yet available:
- Create `toolkit/cowork/README.md` with planned integration
- Create MCP config template ready to use
- Defer implementation

---

## Task 10: Smithery & Registry Listings (B5)

**Files:**
- Create: `mcp/smithery.yaml` or `mcp/smithery.json`
- Create: `mcp/mcp.json`
- Modify: `mcp/README.md`

- [ ] **Step 1: Create Smithery manifest**

Create `mcp/smithery.yaml`:
- Name, description, icon, categories
- Tool listing with descriptions
- Authentication requirements
- Installation command

- [ ] **Step 2: Create MCP Registry manifest**

Create `mcp/mcp.json` following MCP Registry spec:
- Server metadata, tool definitions, transport modes
- Host at well-known URL or in repo root

- [ ] **Step 3: Submit to registries**

- Submit to Smithery
- Submit to Glama
- Submit PR to awesome-mcp-servers

- [ ] **Step 4: GitHub discoverability**

Ensure all repos have proper GitHub topics set.
Update MCP README with badges and quick demo section.

---

## Execution Order & Dependencies

```
Task 1 (WS Server) ────────── no deps, start immediately
Task 2 (WS SDKs) ─────────── after Task 1
Task 3 (Address DB/API) ───── no deps, start immediately (parallel with Task 1)
Task 4 (Address SDK/MCP/CLI) ─ after Task 3
Task 5 (LangChain) ────────── after Task 4 (needs address API)
Task 6 (Claude Code Skill) ── after Task 4
Task 7 (OpenClaw) ─────────── after Task 4
Task 8 (Codex/OpenCode) ───── after Task 4
Task 9 (Cowork) ───────────── independent (research-first, may defer)
Task 10 (Registries) ──────── after Task 6 (needs final tool list)
```

**Parallelizable groups:**
- Group 1 (immediate): Tasks 1, 3
- Group 2 (after Group 1): Tasks 2, 4
- Group 3 (after Group 2): Tasks 5, 6, 7, 8, 9
- Group 4 (final): Task 10

**Estimated effort:** 8-10 weeks total (with parallelism: ~5-6 weeks)
