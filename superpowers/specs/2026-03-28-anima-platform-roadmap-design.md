# Anima Platform Roadmap — Design Specification

**Date:** 2026-03-28
**Author:** Diyan Bogdanov + Claude
**Status:** Draft
**Approach:** Parallel tracks (Phase A + Phase C design in parallel, then B/D layer on)

---

## Executive Summary

Anima is a unified agent identity infrastructure platform combining email, phone, virtual cards, credential vault, and agent identity under one API. This spec defines the complete roadmap from launch readiness to enterprise compliance across 4 phases with 21 top-level work items (B2 merged into A7; C4 and D4 each have sub-phases).

**Strategic thesis:** Competitors (Agentmail, Agentphone, Agentcard) each solve one slice. Anima is the only platform offering all operational capabilities unified under an open agent identity protocol. The identity protocol (Phase C) is the moat — it turns Anima from a product into a standard.

**Sequencing:** Approach B (parallel tracks). Phase A ships launch readiness while Phase C identity protocol design runs concurrently. Phase B (developer experience) and Phase D (enterprise) layer on after Phase A core.

---

## Current State Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| API (Hono/oRPC) | 95% | All core endpoints implemented |
| TypeScript SDK | 95% | Published @anima-labs/sdk, all 10 resources |
| Python SDK | 95% code, 5% packaging | Fully implemented but README says "Coming soon" |
| Go SDK | 0% | Placeholder only |
| CLI | 85% | ~40+ commands, 11 groups (admin, auth, card, config, email, extension, identity, init, phone, setup-mcp, vault), substantially built |
| MCP Server | 90% | 77+ tools, stdio + HTTP modes |
| Console | 40% | 24 pages exist, mostly mocked data |
| Documentation | 30% | MDX files exist in anima/docs/, no public docs site |
| Email | 95% | Multi-region SES, semantic search, custom domains |
| Phone | 90% | Telnyx + Twilio, SMS/voice |
| Cards | 90% | Stripe Issuing, policies, approvals, AML |
| Vault | 85% | Bitwarden backend, 4 credential types |
| Agent Identity | 40% | In-memory manager, reputation, no DID/VC |
| Protocols | 80% | Visa TAP, AP2, Mastercard VI, x402 built but not surfaced |
| Security | 70% | PII/injection scanning, rate limiting, event logging |
| Browser Extension | 60% | Checkout detection, Stripe/Braintree/Adyen adapters |
| Skills | 70% | Exist in skill/ and skills/, need completeness audit |
| Toolkit | 70% | Vercel AI, LangChain, OpenAI — email-heavy, missing card/phone/vault |
| Examples | 60% | 4 examples, don't showcase unified platform |

---

## Phase A — Launch Readiness

**Goal:** Make Anima shippable as a competitive product that matches or exceeds Agentmail/Agentphone/Agentcard individually.
**Priority:** Highest. Runs first.
**Dependency:** None.

---

### A1. Fix Python SDK Packaging & README

**Current state:** Full implementation exists at `python/src/anima/` with all 10 resources (Agents, Cards, Domains, Emails, Messages, Organizations, Phones, Security, Vault, Webhooks), both sync and async clients. README incorrectly says "Coming soon." `pyproject.toml` uses hatchling build system targeting Python 3.9+.

**What to build:**

1. **Update README.md** with:
   - Installation: `pip install anima-labs`
   - Quick start code example (create org, create agent, send email)
   - Full resource reference table
   - Async usage example
   - Webhook verification example
   - Link to docs site

2. **Verify PyPI publishing:**
   - Confirm package name availability (`anima-labs` or `anima`)
   - Update `pyproject.toml` metadata (description, keywords, classifiers, URLs)
   - Verify `py.typed` marker is included in package build (file already exists)
   - Test `pip install` from local build
   - Test `pip install` from TestPyPI before production publish

3. **CI/CD pipeline:**
   - Extend existing `cli-python-release.yml` or create `sdk-python-release.yml`
   - Trigger on git tag `python-v*`
   - Build with hatchling, publish to PyPI
   - Run tests before publish

4. **Feature parity verification:**
   - Cross-reference every method in Node SDK against Python SDK
   - Document any gaps in a tracking table
   - Ensure error classes match (APIError, AuthError, NotFoundError, RateLimitError, ValidationError)

**Ready criteria:**
- `pip install anima-labs` works from PyPI
- README has accurate installation, quickstart, and API reference
- CI publishes on tag push
- All methods from Node SDK exist in Python SDK

**Testing criteria:**
- Existing test suite passes
- Install-from-PyPI smoke test in CI
- Type checking passes (mypy or pyright)

**Business justification:** Python is the #1 language for AI/ML development. Most agent frameworks (LangChain, CrewAI, AutoGen, OpenAI Agents) are Python-first. A non-functional Python SDK loses the majority of the target market. Agentmail's Python SDK has 45 GitHub stars and is actively maintained — this is table stakes.

---

### A2. Wire Console to Real APIs

**Current state:** 24 pages exist in `anima/apps/console/`. Webhooks page and API keys page are fully wired using `orpc.*` + `useSuspenseQuery`. Other pages use mixed real/mock data. A production readiness plan exists at `anima/docs/superpowers/plans/2026-03-27-anima-console-production-readiness.md`.

**What to build:**

1. **Wire existing pages (follow webhooks page pattern):**
   - Cards list page → `cards.list` endpoint
   - Card detail page → `cards.get` + `cards.listTransactions` + `cards.listPolicies` + `cards.listApprovals`
   - Vault list page → `vault.listCredentials` endpoint (may need new `vault.listIdentities` contract)
   - Vault detail page → `vault.getCredential` with CRUD operations
   - Phone list page → `phones.list` endpoint
   - Phone detail page → `phones.get` with SMS history
   - Email/Messages list page → `messages.list` endpoint
   - Email detail page → `messages.get` with thread view
   - Settings page → `organizations.get` + `organizations.update`
   - Billing page → Real Stripe billing integration
   - Agents list page → `agents.list` (verify this is wired, not mocked)
   - Agent detail page → `agents.get` with all associated resources

2. **Build missing pages:**
   - Phone number provisioning form — area code search, number selection, agent assignment
   - Vault credential create/edit forms — support all 4 types (login, secure_note, card, identity)
   - Email forwarding rules configuration
   - Card policy builder — visual UI for spending limits, merchant filters, time windows
   - Approval workflow UI — pending approvals list, approve/decline actions, history

3. **Pattern to follow:**
   - Reference: `apps/console/src/app/(dashboard)/webhooks/page.tsx`
   - Reference: `apps/console/src/app/(dashboard)/api-keys/page.tsx`
   - Use `orpc.*` for API calls
   - Use `useSuspenseQuery` for data fetching with React Suspense
   - Use `useMutation` for create/update/delete operations
   - TanStack Query for cache management
   - Optimistic updates where appropriate

4. **End-to-end user flows:**
   - Onboarding: Sign up → Create org → Create first agent → Send test email
   - Card management: Create card → Set policies → View transactions → Freeze/unfreeze
   - Vault: Provision vault → Store credential → Retrieve credential
   - Phone: Provision number → Send test SMS → View conversation

**Ready criteria:**
- Every console page fetches real data from the API (zero mocked data)
- All CRUD operations work (create, read, update, delete)
- Error states handled (loading, empty, error, unauthorized)
- All missing pages built and functional

**Testing criteria:**
- Manual E2E walkthrough of each user flow
- Console builds without errors (`bun run build`)
- No TypeScript errors
- Responsive on desktop (mobile is nice-to-have)

**Business justification:** A mocked console is a demo, not a product. Users who sign up and see fake data will churn immediately. Agentmail's console is fully functional. The console is the first thing enterprise evaluators see after signing up.

---

### A3. Complete CLI Gaps

**Current state:** CLI at `cli/` has ~40+ commands across 11 groups (admin, auth, card, config, email, extension, identity, init, phone, setup-mcp, vault). Built with proper subcommand structure, output formatting, and auth handling.

**What to build:**

1. **Audit each command group for completeness:**
   - Verify every command is fully wired to the API (not just scaffolded)
   - Test each command with real API calls
   - Document any commands that error or return placeholder data

2. **Add missing webhook commands:**
   - `am webhook create` — create webhook subscription
   - `am webhook list` — list webhooks
   - `am webhook get <id>` — get webhook details
   - `am webhook delete <id>` — delete webhook
   - `am webhook test <id>` — send test event
   - `am webhook deliveries <id>` — list delivery attempts

3. **Add missing security commands:**
   - `am security events` — list security events
   - `am security scan <content>` — scan content for PII/injection

4. **Output formatting consistency:**
   - Every command supports `--output json|table|yaml`
   - Table output is the default for list commands
   - JSON output is the default for get/create commands
   - Add `--quiet` flag for scriptable output (IDs only)

5. **Shell completions:**
   - Bash completion script
   - Zsh completion script
   - Fish completion script
   - Installation instructions in README

6. **Homebrew verification:**
   - Verify `homebrew-tap/` formula works for current version
   - Test `brew install anima-labs/tap/anima`
   - Add to CLI README

7. **Global flags:**
   - `--profile <name>` — switch between API key profiles
   - `--api-url <url>` — override API URL
   - `--verbose` — debug output
   - `--no-color` — disable colored output

**Ready criteria:**
- Every command in every group is functional (not just scaffolded)
- `--output` flag works consistently across all commands
- Shell completions install and work
- Homebrew installation works
- `am --help` shows complete command tree

**Testing criteria:**
- CLI test suite passes
- Manual test of each command against live API
- Shell completion tests (tab completion works)
- Homebrew formula installs cleanly on macOS

**Business justification:** CLIs are how power users and CI/CD pipelines interact with infrastructure. Agentmail's CLI has full inbox/message CRUD. Agentcard's CLI has full card/cardholder management. A CLI with gaps signals an immature product.

---

### A4. Ship Documentation

**Current state:** MDX files exist in `anima/docs/` covering getting-started, custom-domains, encryption, kyb, mcp, sdks, security, webhooks, faq, cards/, and protocols/. No interactive API reference. No publicly accessible OpenAPI spec. No docs site deployed.

**What to build:**

1. **OpenAPI 3.1 specification:**
   - Generate from oRPC contracts or maintain manually
   - Cover all endpoints across all domains (agents, emails, phones, cards, vault, webhooks, security, domains, organizations)
   - Include request/response schemas, error codes, authentication
   - Publish at `https://api.anima.email/openapi.json`
   - Version the spec (v1)

2. **Documentation site:**
   - Framework: Fumadocs (Next.js-based, fits your stack) or Mintlify
   - Deploy at `https://docs.anima.email`
   - Sections:
     - **Getting Started** — API key, first request, quickstart per language
     - **Concepts** — Agents, Organizations, Identity, Vault, Wallet
     - **Guides** — Send email, Provision phone, Create card, Store credentials, Set up webhooks, Custom domains, KYB onboarding
     - **API Reference** — Interactive, generated from OpenAPI spec, try-it-now for each endpoint
     - **SDKs** — TypeScript, Python, Go installation and usage
     - **MCP** — Setup for Claude Desktop, Cursor, Windsurf, hosted endpoint
     - **CLI** — Full command reference
     - **Skills** — Claude Code / Cursor skill installation and usage
     - **Integrations** — Framework toolkit guides (LangChain, OpenAI, Vercel AI, CrewAI, etc.)
     - **Security** — Encryption, PII detection, rate limiting, incident response
     - **Protocols** — Visa TAP, AP2, Mastercard VI, x402 documentation
     - **Changelog** — Version history

3. **LLM-friendly documentation:**
   - `llms.txt` file at root of docs site (Agentcard has this)
   - `llms-full.txt` with comprehensive context for AI consumption
   - Ensure docs are crawlable by Context7 and similar services

4. **Interactive API playground:**
   - Embedded in docs site
   - Authenticated with user's API key
   - Try-it-now for every endpoint
   - Code snippet generation (curl, Python, TypeScript, Go)

5. **Integration guides:**
   - Step-by-step for each supported framework
   - Copy-paste code that works
   - Video walkthroughs (optional, high impact)

**Ready criteria:**
- Docs site is live at docs.anima.email
- OpenAPI spec is published and accessible
- Every endpoint is documented with request/response examples
- Interactive playground works
- `llms.txt` is accessible
- All SDK installation instructions work

**Testing criteria:**
- Docs site builds and deploys without errors
- All code snippets in docs are tested and work
- OpenAPI spec validates with OpenAPI linter
- Navigation covers all product areas
- Search works across all docs

**Business justification:** Agentmail has 70+ documented endpoints with interactive reference. Documentation is the #1 factor developers use to evaluate infrastructure tools (Source: StackOverflow developer surveys). Poor docs = no adoption, regardless of product quality. `llms.txt` is critical because AI agents (your customers) will read your docs to learn how to use your API.

---

### A5. Compelling Examples

**Current state:** 4 examples exist: email-agent (Python), card-provisioning (TypeScript), vercel-ai-agent (TypeScript), openai-terminal (Python). They demonstrate individual features but don't showcase the unified platform.

**What to build:**

1. **E-commerce purchasing agent** (Python):
   - Uses cards to make a purchase
   - Uses vault to store/retrieve merchant login credentials
   - Uses email to receive order confirmation and receipts
   - Uses address for shipping
   - Demonstrates the full agent lifecycle: authenticate → browse → purchase → confirm
   - Shows policy enforcement (spending limit, merchant filter)

2. **Customer support agent** (TypeScript):
   - Uses phone to receive inbound calls
   - Uses email to send follow-up summaries
   - Uses identity for caller verification
   - Uses vault to access CRM credentials
   - Demonstrates multi-channel agent operation

3. **Travel booking agent** (Python):
   - Uses cards to book flights/hotels
   - Uses phone to call hotels for special requests
   - Uses email to receive booking confirmations
   - Uses address for billing/shipping
   - Uses vault for airline loyalty credentials
   - Demonstrates complex multi-step workflow with multiple Anima services

4. **Multi-agent collaboration** (TypeScript) — **Deferred to C6 (A2A Protocol) as deliverable:**
   - Two agents collaborating via A2A
   - Agent A discovers Agent B via registry
   - Agent A delegates a card with spending limit to Agent B
   - Agent B completes a task and reports back
   - Demonstrates agent-to-agent trust and delegation

5. **Update existing examples:**
   - Ensure all examples use latest SDK version
   - Add README with architecture diagram to each
   - Add `.env.example` with required variables
   - Add `docker-compose.yml` where applicable for local dependencies

**Ready criteria:**
- At least 3 new examples (e-commerce, support, travel) work end-to-end
- Each example has a comprehensive README
- Each example runs with `pip install -r requirements.txt && python main.py` or `bun install && bun run start`
- Examples demonstrate multiple Anima services working together

**Testing criteria:**
- Each example runs successfully against the live API
- Each example handles errors gracefully (missing API key, network failure)
- README instructions are accurate and complete

**Business justification:** Examples are how developers evaluate whether a product fits their use case. Agentmail has purpose-built examples (sales agent, auto-reply agent). Single-service examples don't differentiate Anima from competitors — unified examples demonstrate why Anima exists.

---

### A6. Node SDK Audit & Parity

**Current state:** Published as `@anima-labs/sdk` at `node/`. Has all 10 resources with full CRUD operations. Tests exist at `node/__tests__/`.

**What to build:**

1. **Method-level parity audit:**
   - Create a comparison matrix: every Python SDK method → corresponding Node SDK method
   - Identify any gaps in either direction
   - Python has: `upload_attachment`, `get_attachment_url`, `scan_content`, `list_events` — verify Node equivalents exist
   - Verify parameter names and types are consistent across SDKs

2. **Error class consistency:**
   - Python errors: APIError, AuthError, NotFoundError, RateLimitError, ValidationError
   - Node errors: verify same set exists with same semantics
   - Ensure error messages are consistent

3. **Webhook utility parity:**
   - Python: `_webhooks.py` — verify Node: `webhooks.ts` matches
   - Signature verification algorithm must be identical
   - Event construction helpers must match

4. **README update:**
   - Match Python SDK README quality
   - Installation, quickstart, full resource reference
   - Webhook verification example
   - TypeScript type examples

5. **Publishing pipeline:**
   - Verify npm publish works on tag
   - Add CI/CD if missing

**Ready criteria:**
- 1:1 method parity between Python and Node SDKs (documented in matrix)
- READMEs are comprehensive and consistent
- Both publish successfully to their registries
- Error handling is consistent

**Testing criteria:**
- Node test suite passes
- Parity matrix has zero gaps
- Type checking passes (tsc --noEmit)

**Business justification:** SDK inconsistency erodes trust. If a developer starts with the Python SDK and their colleague uses the Node SDK, they expect identical behavior. Inconsistencies create support burden and confusion.

---

### A7. MCP Server Completeness

**Current state:** MCP server at `mcp/` with 13 tool categories, ~77+ tools. Supports stdio and HTTP modes. Auth via API key prefixes. Has x402 and browser payment tools.

**What to build:**

1. **Tool coverage audit:**
   - Create matrix: every SDK method → corresponding MCP tool
   - Identify missing tools
   - Priority gaps: any SDK operation an AI agent would commonly use that's missing from MCP

2. **Missing tools to add:**
   - Any operations found missing in the audit against *current* SDK methods
   - Note: Address MCP tools will be added as part of B3 scope; Wallet MCP tools as part of C3 scope. A7 covers only currently existing SDK operations.

3. **Selective tool loading:**
   - Add `--tools` flag: `npx @anima-labs/mcp --tools email,cards,vault`
   - Useful for agents that only need a subset of capabilities
   - Reduces tool surface for simpler agent configurations
   - Agentmail MCP has this feature

4. **Tool description quality:**
   - Review every tool description for LLM-friendliness
   - Descriptions should clearly state: what the tool does, required parameters, what it returns
   - Add examples in descriptions where helpful
   - Test with Claude/GPT to verify tools are selected correctly from natural language

5. **Hosted MCP endpoint:**
   - Deploy at `https://mcp.anima.email/mcp`
   - Streamable HTTP transport
   - API key auth via header
   - Auto-scaling
   - Health check endpoint
   - Zero-install experience for users

6. **Registry listings:**
   - Submit to Smithery with proper metadata and icon
   - Submit to Glama MCP registry
   - Create `mcp.json` for MCP Registry standard
   - Add to awesome-mcp-servers GitHub lists

7. **Configuration templates:**
   - Claude Desktop `claude_desktop_config.json` snippet
   - Cursor `.cursor/mcp.json` snippet
   - Windsurf configuration snippet
   - All in docs and README

**Ready criteria:**
- Every *current* SDK method has a corresponding MCP tool (future resources like Address and Wallet add their own MCP tools in their respective phases)
- `--tools` flag works for selective loading
- Hosted endpoint is live at mcp.anima.email/mcp
- Listed on at least Smithery and Glama
- Configuration templates work for Claude Desktop, Cursor, Windsurf

**Testing criteria:**
- MCP test suite passes
- Each tool executes successfully when invoked by an AI agent
- Hosted endpoint responds correctly
- Selective loading correctly filters tools
- Registry listings are live and discoverable

**Business justification:** MCP is how AI agents connect to external tools. It's the distribution channel. Both Agentphone and Agentcard have hosted MCP endpoints — without one, users must install and run your MCP server locally, which loses casual adopters. Registry listings are free distribution. Selective tool loading reduces confusion for agents that don't need 77+ tools.

---

### A8. Skills Completeness

**Current state:** Skills exist in `skill/` (main Anima skill) and `skills/` (collection of specialized skills). Need audit against full API surface.

**What to build:**

1. **Skill coverage audit:**
   - Map every SDK operation to skill trigger patterns
   - Identify operations that can't be invoked via natural language skills
   - Verify skill descriptions accurately trigger on relevant user intents

2. **Missing skill coverage:**
   - Card management skills (create card, set spending limit, freeze/unfreeze, view transactions)
   - Phone skills (provision number, send SMS, view conversations)
   - Vault skills (store credential, retrieve credential, generate password)
   - Address skills (once B3 builds the service)
   - Wallet skills (once C3 builds the service)
   - Security skills (scan content, view security events)

3. **Skill quality:**
   - Each skill should have clear trigger description
   - Natural language examples in skill metadata
   - Proper parameter extraction from user intent
   - Error handling with user-friendly messages

4. **Publishing:**
   - Publish via `npx skills.sh install anima` (like Agentphone's approach)
   - Verify installation works in Claude Code
   - Verify installation works in Cursor
   - Document installation in main docs

5. **Skill documentation:**
   - Add skills section to docs site
   - List all available skills with descriptions and examples
   - Installation instructions per IDE/tool

**Ready criteria:**
- Every major Anima operation has a corresponding skill
- Skills install correctly via published package
- Skills trigger correctly on natural language input
- Documentation covers all skills

**Testing criteria:**
- Each skill triggers on expected natural language patterns
- Each skill executes the correct API operation
- Installation works in Claude Code and Cursor
- No false triggers on unrelated input

**Business justification:** Skills are the highest-leverage integration point for Claude Code and Cursor users — they turn natural language into API calls without any code. Agentphone's skill plugin is a key differentiator. If Anima skills are incomplete, users fall back to manual SDK usage, which is higher friction.

---

## Phase B — Developer Experience

**Goal:** Elevate DX to best-in-class. Make it frictionless for any developer using any AI framework.
**Priority:** Starts after Phase A core ships. Some items can overlap with late Phase A.
**Dependency:** Phase A (SDKs, docs, MCP must be solid first).

---

### B1. WebSocket Support Across All Events

**Current state:** WebSockets exist only in browser extension (extension <-> backend bridge). Main API uses HTTP webhooks only. Hono server framework supports WebSocket upgrades.

**What to build:**

1. **WebSocket server endpoint:**
   - Add `/ws` endpoint to API server (Hono WebSocket upgrade)
   - Authentication: API key in connection query parameter or first message
   - Connection lifecycle: connect → authenticate → subscribe → receive events → disconnect

2. **Event channel model:**
   - Clients subscribe to event channels: `email.*`, `sms.*`, `card.*`, `vault.*`, `security.*`, `approval.*`
   - Wildcard support: `*` for all events, `email.received` for specific event
   - Per-agent filtering: `agent:<agent-id>:email.*`
   - Per-org filtering (default): all events for the organization

3. **Event types to stream:**
   - Email: received, sent, delivered, bounced, complained, rejected
   - SMS: received, sent, delivered, failed
   - Card: transaction.authorized, transaction.declined, card.frozen, card.unfrozen, card.killed
   - Vault: credential.accessed, credential.created, credential.rotated
   - Approval: requested, approved, declined, expired
   - Security: pii_detected, injection_detected, rate_limited, anomaly_detected

4. **Missed event recovery:**
   - Last-Event-ID header support
   - Server stores last N events per channel (configurable, default 1000)
   - On reconnection, client sends last received event ID, server replays missed events
   - Fallback to webhooks for events older than retention window

5. **SDK integration:**
   - TypeScript: `anima.events.subscribe('email.*', callback)` with auto-reconnection
   - Python: `async for event in anima.events.subscribe('email.*'):` with async iterator
   - Both SDKs handle reconnection, authentication, and error recovery transparently

6. **MCP integration:**
   - Add WebSocket transport option for MCP server (beyond stdio and HTTP)
   - Real-time event notifications within MCP sessions

**Ready criteria:**
- WebSocket endpoint accepts connections and streams events
- Subscription model works with channel patterns
- SDKs support WebSocket event consumption
- Reconnection with missed event recovery works
- Events fire for all major operations across all services

**Testing criteria:**
- Unit tests for WebSocket server
- Integration test: trigger email send → receive WebSocket event
- Reconnection test: disconnect → reconnect → receive missed events
- Load test: 100 concurrent connections receiving events
- SDK tests for TypeScript and Python WebSocket clients

**Business justification:** Agentmail has WebSockets and it's a major advantage — agents react in real-time instead of polling. For autonomous agents, real-time is not a luxury, it's a requirement. An agent monitoring an inbox for replies needs instant notification, not 30-second webhook delivery delays.

---

### B2. Hosted MCP Endpoint

**Note:** Merged into A7. The hosted MCP endpoint at `mcp.anima.email/mcp` is now part of Phase A MCP completeness, as both competitors already offer this and it's table stakes for launch.

---

### B3. Agent Address Service

**Current state:** Vault identity credential type stores address fields (street, city, state, zip, country). Cardholder model has billing address (`billing_street1`, `billing_city`, etc.). But no first-class agent address concept with validation and multi-type support.

**What to build:**

1. **Database model:**
   ```
   AddressIdentity {
     id          String
     agentId     String → Agent
     orgId       String → Organization
     type        AddressType (BILLING, SHIPPING, MAILING, REGISTERED)
     label       String? (e.g., "Office", "Warehouse")
     street1     String
     street2     String?
     city        String
     state       String
     postalCode  String
     country     String (ISO 3166-1 alpha-2)
     validated   Boolean (default false)
     validatedAt DateTime?
     provider    String? (USPS, GOOGLE, SMARTY)
     metadata    Json?
     primary     Boolean (default false, one primary per type per agent)
     createdAt   DateTime
     updatedAt   DateTime
   }
   ```

2. **Address validation:**
   - Integrate validation provider (Smarty is the most cost-effective; Google Address Validation for international)
   - Validate on creation, flag as validated/unvalidated
   - Normalize formatting (USPS standardization for US addresses)
   - Return validation confidence score

3. **API endpoints:**
   - `POST /v1/agents/:agentId/addresses` — create address
   - `GET /v1/agents/:agentId/addresses` — list addresses
   - `GET /v1/agents/:agentId/addresses/:id` — get address
   - `PUT /v1/agents/:agentId/addresses/:id` — update address
   - `DELETE /v1/agents/:agentId/addresses/:id` — delete address
   - `POST /v1/agents/:agentId/addresses/:id/validate` — validate/re-validate address

4. **Integration with existing services:**
   - Card creation auto-populates billing address from agent's primary BILLING address
   - Browser extension auto-fills shipping address during checkout from agent's primary SHIPPING address
   - Vault identity credential type references AddressIdentity instead of storing raw address fields

5. **SDK, MCP, CLI, Skill support:**
   - Add address methods to TypeScript and Python SDKs
   - Add MCP tools: create_address, list_addresses, get_address, update_address, delete_address, validate_address
   - Add CLI commands: `am address create`, `am address list`, `am address get`, `am address delete`, `am address validate`
   - Add skills for natural language address management

**Ready criteria:**
- Address CRUD works through API, SDKs, MCP, CLI
- Validation returns standardized addresses
- Card creation auto-uses billing address
- Extension auto-fills shipping address
- Address types are enforced (one primary per type per agent)

**Testing criteria:**
- Unit tests for address model and validation
- Integration tests: create address → create card (billing auto-populated)
- Validation tests with real addresses (US, international)
- Invalid address handling (returns suggestions)

**Business justification:** Card transactions without valid billing addresses fail AVS (Address Verification System) checks. Agents that shop need shipping addresses. No competitor offers address as a first-class service. This gap blocks real-world agent autonomy — an agent that can't fill in a shipping address can't complete a purchase.

**Relationship to Agent Identity (Phase C):** Address is an attribute of the agent, stored as a child resource (like EmailIdentity, PhoneIdentity). When Phase C implements DIDs, the address becomes a Verifiable Credential claim: "This agent's billing address at 123 Main St is verified by Anima via USPS validation." No conceptual collision — identity wraps address with cryptographic verification.

---

### B4. Framework Integrations Expansion

**Current state:** Toolkit at `toolkit/` covers Vercel AI SDK (Node), LangChain (Python), OpenAI Agents SDK (Python). Each has 8-12 tool definitions, mostly focused on email operations. Missing card, phone, vault, and address tool definitions in most integrations.

**What to build:**

1. **Claude Code** (high priority):
   - Skill at `skill/` already exists — audit for completeness
   - Ensure all operations are covered: email, phone, cards, vault, address
   - Publish via npm/skills registry
   - Test natural language trigger accuracy

2. **Claude Cowork** (highest priority):
   - Reference: Anthropic's multi-agent collaboration product (https://claude.ai/cowork)
   - Anima tools available as shared agent capabilities in Cowork sessions
   - Any agent in a Cowork session can provision emails, cards, phones, store credentials
   - Integration pattern: MCP server connection from Cowork workspace
   - Documentation: "How to give your Cowork agents real-world identity"
   - Example: Multi-agent Cowork session where agents collaborate on a purchasing task
   - Note: If Cowork API/integration surface is not yet public, defer until available. Monitor Anthropic announcements.

3. **OpenClaw** (highest priority):
   - Reference: https://github.com/openclaw/openclaw (open-source personal AI assistant, ~339K GitHub stars)
   - OpenClaw plugin/integration (supports 24+ platforms including WhatsApp, Telegram, Slack, Discord, Signal)
   - Anima as the identity provider for OpenClaw agents
   - Each OpenClaw agent gets: email, phone, card, vault, address via Anima
   - Plugin hooks into OpenClaw's multi-channel communication layer
   - Configuration: add Anima API key to OpenClaw config, agents auto-provision identity
   - Documentation: "Give your OpenClaw agents real-world identity with Anima"

4. **Codex** (OpenAI's coding agent):
   - Tool definitions compatible with Codex's function calling format
   - Cover full surface: email, phone, cards, vault, address
   - Publish as npm package: `@anima-labs/toolkit-codex`

5. **OpenCode:**
   - `opencode/` already exists in repo — tighten integration
   - OpenCode agents use Anima natively for identity operations
   - Shared configuration between OpenCode and Anima

6. **LangChain** (expand existing):
   - Currently email-only tools — expand to full surface
   - Add tools: CreateCardTool, ListTransactionsTool, FreezeCardTool, ProvisionPhoneTool, SendSmsTool, StoreCredentialTool, GetCredentialTool, CreateAddressTool, ValidateAddressTool
   - Publish as `anima-toolkit-langchain` on PyPI

7. **Each integration MUST expose the full unified surface:**
   - Email: send, list, get, search
   - Phone: provision, send SMS, list messages
   - Cards: create, list, transactions, freeze/unfreeze, policies
   - Vault: store, retrieve, list, generate password
   - Address: create, list, validate

**Ready criteria:**
- All 6 integrations implemented and published
- Each integration covers: email, phone, cards, vault, address
- Documentation and examples for each integration
- Published to npm/PyPI as appropriate

**Testing criteria:**
- Each integration's tools execute successfully against live API
- Natural language triggers work (for skills-based integrations)
- Installation instructions work from clean environment
- No import errors or dependency conflicts

**Business justification:** Claude Cowork and OpenClaw are the two largest multi-agent platforms. If Anima is the default identity provider for these platforms, distribution is solved. Developers choose infrastructure that integrates with their stack — every missing framework integration is a lost user. The unified surface (email + phone + cards + vault + address) is what differentiates Anima integrations from Agentmail's email-only toolkit.

---

### B5. Smithery / Registry Listings & Discoverability

**Current state:** `smithery-mcp/` is a placeholder directory. Not listed on any MCP registry. No SEO strategy.

**What to build:**

1. **Smithery submission:**
   - Create proper Smithery manifest with metadata, icon, description
   - Submit MCP server to Smithery registry
   - Categorize under: AI Agent Tools, Email, Payments, Identity

2. **Glama MCP registry:**
   - Submit to Glama with tool descriptions and usage examples
   - Include authentication requirements

3. **MCP Registry standard:**
   - Create `mcp.json` file following MCP Registry spec
   - Host at well-known URL

4. **GitHub discoverability:**
   - Add to `awesome-mcp-servers` and similar curated lists
   - Ensure GitHub topics include: mcp, ai-agent, email-api, virtual-cards, agent-identity
   - Star-worthy README with badges, screenshots, quick demo GIF

5. **Content marketing (ongoing activity, not a gated deliverable):**
   - Blog posts targeting: "AI agent email API", "AI agent virtual card", "agent identity protocol"
   - Comparison pages: "Anima vs Agentmail", "Anima vs Agentcard"
   - Tutorial: "Build an autonomous purchasing agent in 10 minutes"
   - Note: Content marketing is continuous and not part of B5 "done" criteria. Track separately.

**Ready criteria:**
- Listed on Smithery and Glama
- `mcp.json` published
- At least 2 awesome-list PRs submitted

**Testing criteria:**
- Registry listings are live and searchable
- MCP server installs correctly from registry
- Blog posts rank for target keywords (check after 2 weeks)

**Business justification:** Agentmail's MCP server has 36 GitHub stars. Their toolkit has 57 stars. Discoverability is how developer tools grow organically. Registry listings are free distribution with near-zero maintenance.

---

## Phase C — Agent Identity & Commerce

**Goal:** Build the strategic moat. Open agent identity protocol + commerce capabilities.
**Priority:** Protocol design starts in parallel with Phase A. Implementation after Phase A ships.
**Dependency:** Phase A (core platform must be solid before building identity layer on top).

---

### C1. Agent Identity Protocol (DID + Verifiable Credentials + Agent Cards)

**Current state:** `@anima/agent-identity` at `anima/packages/agent-identity/` has: in-memory identity manager, credential lifecycle (generate/verify/rotate/revoke), email/phone identity models, reputation system (0-100 score with delivery/response weighting), webhook secret generation via HMAC-SHA256. Apache-2.0 licensed. No DID, no Verifiable Credentials, no Agent Cards, no interoperability with external systems.

**What to build:**

1. **DID Method (`did:anima`):**
   - DID format: `did:anima:<org-id>:<agent-id>` or `did:anima:<unique-hash>`
   - DID Document (JSON-LD) containing:
     - `id`: the DID
     - `verificationMethod`: Ed25519 or P-256 public key(s)
     - `authentication`: key references for agent authentication
     - `service`: endpoints array — email inbox URL, phone number, webhook URL, MCP endpoint, A2A endpoint
     - `controller`: DID of the owning organization
   - DID resolution endpoint: `GET /v1/identity/did/:did` → returns DID Document
   - DID creation: automatic when agent is created (every agent gets a DID)
   - Key rotation: update DID Document with new keys, maintain history
   - DID deactivation: when agent is deleted, DID is marked deactivated

   - **Spec alignment:** W3C DID Core 1.0 (W3C Recommendation, 2022). DID v1.1 may be in draft — verify current status before finalizing. Register `did:anima` in the DID Spec Registries (follows W3C Note process).

2. **Verifiable Credentials (VCs):**
   - Anima acts as an Issuer — signs VCs attesting to agent properties
   - Issuer DID: `did:anima:issuer` with Anima's signing keys
   - Credential types:
     - `AnimaEmailVerified` — email address is verified (SPF/DKIM passed)
     - `AnimaPhoneVerified` — phone number is verified (carrier confirmed)
     - `AnimaAddressVerified` — address passed validation (USPS/Google)
     - `AnimaKYBCompleted` — owner organization completed KYB via Stripe Connect
     - `AnimaPaymentCapable` — agent has active card(s) and can make payments
     - `AnimaOwnerBound` — agent is bound to a verified human/org identity
     - `AnimaTrustScore` — current trust/reputation score with evidence
   - VC format: W3C VC Data Model 2.0, JWT encoding for compactness
   - VC lifecycle: issue → hold → present → verify → revoke
   - Revocation: maintain a revocation list (StatusList2021)
   - API endpoints:
     - `GET /v1/agents/:agentId/credentials` — list VCs for an agent
     - `POST /v1/agents/:agentId/credentials/verify` — verify a presented VC
     - `GET /v1/identity/verify/:vcId` — public VC verification endpoint

   - **Spec alignment:** W3C VC Data Model 2.0, JWT-VC encoding

3. **A2A Agent Cards:**
   - JSON document describing agent capabilities
   - Format follows Google A2A Agent Card spec:
     ```json
     {
       "name": "Agent Name",
       "description": "What this agent does",
       "url": "https://agent-endpoint.anima.email",
       "did": "did:anima:org123:agent456",
       "capabilities": {
         "email": true,
         "phone": true,
         "cards": true,
         "vault": true,
         "address": true,
         "protocols": ["x402", "ap2", "visa-tap"]
       },
       "verification": {
         "level": "standard",
         "credentials": ["AnimaEmailVerified", "AnimaKYBCompleted"]
       },
       "trust_score": 87,
       "contact": {
         "email": "agent@example.anima.email",
         "phone": "+1234567890"
       }
     }
     ```
   - Discoverable at `/.well-known/agent.json` per agent subdomain
   - Or via registry lookup: `GET /v1/registry/agents/:did/card`
   - Auto-generated from agent configuration — no manual card creation needed

4. **Know Your Agent (KYA):**
   - Human-agent binding: link every agent to a verified owner
   - Leverage existing KYB flow (Stripe Connect hosted onboarding) as verification backbone
   - KYA levels:
     - **Basic:** Email verified (org admin email confirmed via Clerk)
     - **Standard:** Basic + KYB completed (Stripe Connect approved)
     - **Premium:** Standard + additional identity verification (government ID, address proof)
   - Issue `AnimaOwnerBound` VC at Standard+ level
   - Public disclosure: owner chooses what's visible (org name only, full details, or private)
   - Verification endpoint: third parties can verify an agent's KYA level without seeing owner details

5. **Open-source protocol spec:**
   - Publish as independent specification document
   - Apache 2.0 license (consistent with existing `@anima/agent-identity`)
   - Separate GitHub repo: `anima-labs/agent-identity-protocol`
   - Reference implementation in TypeScript (the `@anima/agent-identity` package)
   - Spec covers: DID method, VC types, Agent Card format, KYA levels, trust scoring
   - Invite community review and contribution
   - Submit as IETF Internet-Draft if adoption warrants

6. **SDK, MCP, CLI integration:**
   - SDK: `anima.identity.getDid(agentId)`, `anima.identity.getCredentials(agentId)`, `anima.identity.verifyCredential(vc)`, `anima.identity.getAgentCard(agentId)`
   - MCP tools: get_did, list_credentials, verify_credential, get_agent_card
   - CLI: `am identity did <agentId>`, `am identity credentials <agentId>`, `am identity verify <vc>`, `am identity card <agentId>`
   - Skills: natural language identity queries

**Ready criteria:**
- Every agent has a DID auto-created on agent creation
- DID Documents resolve correctly
- At least 4 VC types are issuable and verifiable
- Agent Cards generate automatically and are discoverable
- KYA levels enforce correctly based on verification status
- Protocol spec is published as open-source document

**Testing criteria:**
- DID creation/resolution unit and integration tests
- VC issuance/verification round-trip tests
- Agent Card generation matches A2A format spec
- KYA level enforcement tests (Basic/Standard/Premium)
- Cross-platform VC verification (verify Anima VCs with third-party VC libraries)
- DID Document conforms to W3C DID Core 1.0 spec (validate with did-resolver libraries)

**Business justification:** The IETF has 5+ active drafts on agent identity (SCIM for AI, Agent Auth, ANS, Trust Scoring, Digital Identity Management). W3C DIDs v1.1 is finalizing. The Linux Foundation AAIF has 146 members. By shipping the first complete implementation combining DIDs + VCs + Agent Cards + KYA, Anima becomes the reference standard. Ping Identity, Strata, and Defakto are enterprise IAM plays — they provide identity governance but not operational capabilities (email, phone, cards). Anima is the only platform that can offer both. The protocol spec, published open-source, positions Anima as the standard setter, not just a vendor.

---

### C2. Agent Registry & Discovery

**Current state:** No registry. Agents are private to their organization. No discovery mechanism.

**What to build:**

1. **Registry database model:**
   ```
   RegistryEntry {
     id          String
     did         String (unique, indexed)
     agentId     String → Agent
     orgId       String → Organization
     public      Boolean (default false)
     name        String
     description String?
     agentCard   Json (A2A Agent Card)
     trustScore  Int (0-100)
     kyaLevel    KYALevel (BASIC, STANDARD, PREMIUM)
     capabilities String[] (email, phone, cards, vault, address)
     tags        String[] (user-defined, searchable)
     verified    Boolean
     verifiedAt  DateTime?
     listedAt    DateTime
     updatedAt   DateTime
   }
   ```

2. **Public registry API:**
   - `POST /v1/registry/agents` — register agent in public registry (opt-in)
   - `GET /v1/registry/agents/:did` — lookup agent by DID
   - `GET /v1/registry/agents/search` — search by capability, trust score, tags, name
   - `DELETE /v1/registry/agents/:did` — unlist from registry
   - `PUT /v1/registry/agents/:did` — update registry entry
   - Search parameters: `capability=email`, `trust_min=80`, `tags=travel,booking`, `kya_level=standard`
   - Pagination, sorting by trust score or listing date

3. **Well-known URL resolution:**
   - Agents with custom domains: `GET https://agent-domain.com/.well-known/agent.json`
   - Anima-hosted agents: `GET https://<agent-slug>.anima.email/.well-known/agent.json`
   - Returns A2A Agent Card format

4. **Verification badges:**
   - Badge levels based on KYA level:
     - Basic (email verified): blue badge
     - Standard (KYB completed): green badge
     - Premium (full verification): gold badge
   - Badge is a Verifiable Credential, independently verifiable
   - Badge displayed on Agent Card and registry listing
   - Badge verification: `GET /v1/registry/verify-badge/:badgeId`

5. **IETF ANS compatibility:**
   - Support agent:// URI scheme: `agent://name.anima.email`
   - DNS TXT record for agent discovery: `_agent.domain.com TXT "did=did:anima:..."`
   - PKI-based identity verification as ANS draft proposes
   - Capability-aware resolution: resolve DID → capabilities → endpoints

6. **Rate limiting and abuse prevention:**
   - Search rate limiting per API key
   - Spam prevention: minimum trust score to list (e.g., trust_score >= 20)
   - Report mechanism for abusive listings
   - Auto-delist agents that are deactivated or suspended

7. **SDK, MCP, CLI integration:**
   - SDK: `anima.registry.register(agentId, options)`, `anima.registry.search(query)`, `anima.registry.lookup(did)`
   - MCP tools: register_agent, search_registry, lookup_agent
   - CLI: `am registry register`, `am registry search`, `am registry lookup <did>`

**Ready criteria:**
- Agents can opt-in to public registry
- Search returns relevant results by capability, trust score, tags
- Well-known URLs resolve correctly
- Verification badges display and verify correctly
- ANS-compatible resolution works

**Testing criteria:**
- Registry CRUD integration tests
- Search relevance tests (query "email agent" returns agents with email capability)
- Well-known URL resolution tests
- Badge verification round-trip tests
- Rate limiting enforcement tests
- Abuse prevention tests (low-trust agents can't list)

**Business justification:** Agent-to-agent commerce requires discovery. If Agent A needs to hire Agent B to book a flight, it needs to find Agent B and verify it's trustworthy. No competitor has an agent registry. This is a platform play — the registry creates network effects. Every agent listed makes the registry more valuable, which attracts more agents.

---

### C3. Agent Wallet with x402 + AP2 Support

**Current state:** `@anima/protocols` has fully implemented adapters for Visa TAP, Google AP2, Mastercard VI, and x402. Protocol router exists with priority-based selection and fallback. Cards exist via Stripe Issuing with policies, approvals, and transaction monitoring. But no "wallet" abstraction ties these together, and protocols are not surfaced through the API/SDK.

**What to build:**

1. **Wallet database model:**
   ```
   Wallet {
     id              String
     agentId         String → Agent
     orgId           String → Organization
     did             String? (linked to agent DID)
     balance         Decimal (real-time tracked)
     currency        String (default "USD")
     dailyLimit      Decimal?
     monthlyLimit    Decimal?
     totalSpent      Decimal
     spentToday      Decimal
     spentThisMonth  Decimal
     status          WalletStatus (ACTIVE, FROZEN, SUSPENDED)
     fundingSources  FundingSource[] (Stripe bank/card)
     cards           CardIdentity[]
     metadata        Json?
     createdAt       DateTime
     updatedAt       DateTime
   }
   ```

2. **Wallet API:**
   - `POST /v1/agents/:agentId/wallet` — create wallet (auto-created with agent optionally)
   - `GET /v1/agents/:agentId/wallet` — get wallet with balance, limits, status
   - `PUT /v1/agents/:agentId/wallet` — update limits, status
   - `GET /v1/agents/:agentId/wallet/transactions` — unified transaction history across all payment methods
   - `POST /v1/agents/:agentId/wallet/pay` — unified payment endpoint (protocol auto-selected)
   - `POST /v1/agents/:agentId/wallet/x402-fetch` — HTTP fetch with x402 payment handling
   - `POST /v1/agents/:agentId/wallet/fund` — add funds from funding source
   - `POST /v1/agents/:agentId/wallet/freeze` — freeze wallet (blocks all payments)
   - `POST /v1/agents/:agentId/wallet/unfreeze` — unfreeze wallet

3. **Unified payment flow:**
   - `wallet.pay(merchant, amount, options)` — single API call
   - Protocol router selects method based on merchant support:
     1. x402 (if merchant supports HTTP 402)
     2. AP2 (if merchant supports Google AP2)
     3. Visa TAP (if merchant supports Visa agent auth)
     4. Mastercard VI (if merchant supports MC Verifiable Intent)
     5. Card (fallback — create single-use virtual card)
   - Budget guards enforced: per-request limit, daily limit, monthly limit
   - Transaction logged regardless of protocol used
   - Approval workflow triggered if amount exceeds auto-approve threshold

4. **x402 integration:**
   - Surface existing x402 adapter through API
   - SDK: `anima.wallet.x402Fetch(url, options)` — drop-in replacement for fetch()
   - Agent encounters HTTP 402 → wallet automatically pays → request succeeds
   - Budget guards: per-request max, session budget, daily budget
   - Settlement via Stripe (existing infrastructure)

5. **AP2 integration:**
   - Surface existing AP2 adapter through API
   - Mandate creation: `anima.wallet.createMandate(merchant, scope, constraints)`
   - Mandate types: cart, intent, payment
   - Delegation chains: Agent A authorizes Agent B to spend up to $X
   - Mandate verification by merchants

6. **SDK, MCP, CLI integration:**
   - SDK: `anima.wallet.getBalance()`, `anima.wallet.pay()`, `anima.wallet.x402Fetch()`, `anima.wallet.createMandate()`, `anima.wallet.getTransactions()`
   - MCP tools: get_wallet_balance, wallet_pay, x402_fetch, create_mandate, list_wallet_transactions
   - CLI: `am wallet balance`, `am wallet pay`, `am wallet transactions`, `am wallet freeze/unfreeze`

**Ready criteria:**
- Wallet CRUD works through API/SDK/MCP/CLI
- Unified pay endpoint selects correct protocol
- x402 fetch works end-to-end
- AP2 mandates create and verify correctly
- Budget guards enforce limits
- Transaction history is unified across all payment methods

**Testing criteria:**
- Wallet creation/management unit tests
- Protocol router selection tests (each protocol path)
- x402 end-to-end test (mock server returning 402 → wallet pays → success)
- AP2 mandate creation/verification tests
- Budget guard enforcement tests (exceed limit → blocked)
- Transaction history aggregation tests

**Business justification:** Skyfire raised $9.5M for agent wallets. Coinbase x402 has AWS/Anthropic/Cloudflare backing. Google AP2 has 60+ partners. The protocol adapters are already built — they just need the wallet abstraction and unified API. This transforms Anima from "card issuer" to "agent financial identity." The unified pay endpoint that auto-selects protocols is something no competitor offers.

---

### C4. OAuth Token Vault (Credential Orchestrator)

**Scope note:** This item is split into three sub-items to manage complexity:
- **C4a:** New credential types + OAuth auto-refresh + audit trail (core)
- **C4b:** Secrets injection proxy + dynamic credentials + delegation (advanced)
- **C4c:** Multi-backend provider support (deferred — future scope beyond this roadmap)

**Current state:** Vault at `@anima/vault` uses Bitwarden backend. Supports 4 credential types: login (username/password/TOTP), secure_note, card, identity. Provider interface for CRUD operations. Password generation with configurable entropy. No OAuth token management, no automatic refresh, no secrets injection.

**What to build:**

#### C4a — Core (New credential types + OAuth refresh + audit)

1. **New credential types:**
   - `oauth_token`:
     ```
     {
       type: "oauth_token",
       provider: "google" | "github" | "slack" | ...,
       accessToken: string (encrypted),
       refreshToken: string (encrypted),
       tokenEndpoint: string,
       clientId: string (encrypted),
       clientSecret: string? (encrypted),
       scopes: string[],
       expiresAt: DateTime,
       autoRefresh: boolean (default true)
     }
     ```
   - `api_key`:
     ```
     {
       type: "api_key",
       provider: "openai" | "anthropic" | "stripe" | ...,
       key: string (encrypted),
       prefix: string? (for display: "sk-...abc"),
       rateLimit: { requests: number, window: string }?,
       expiresAt: DateTime?,
       scopes: string[]?
     }
     ```
   - `certificate`:
     ```
     {
       type: "certificate",
       format: "pem" | "p12" | "jks",
       certificate: string (encrypted),
       privateKey: string (encrypted),
       chain: string[]? (encrypted),
       expiresAt: DateTime
     }
     ```

2. **Automatic OAuth token refresh:**
   - Background job: scan for expiring tokens (within 5 minutes of expiry)
   - Refresh using stored refresh_token + token_endpoint + client credentials
   - Update stored access_token and expiry
   - If refresh fails: flag credential as `needs_reauth`, notify via webhook/WebSocket
   - Support token rotation (new refresh_token replaces old on each refresh)

#### C4b — Advanced (Secrets injection + dynamic credentials + delegation)

3. **Secrets injection pattern:**
   - `POST /v1/vault/proxy` — make HTTP request with credential auto-injected
   - Request body: `{ url, method, credentialId, headers?, body? }`
   - Server injects credential into request (Authorization header, API key header, etc.)
   - Agent never sees the raw secret
   - Response returned to agent without credential exposure
   - `anima.vault.fetch(url, credentialId, options)` — SDK method

4. **Dynamic credential provisioning:**
   - Create credentials with TTL: `{ ttl: "1h" }` — auto-deleted after expiry
   - Scoped credentials: `{ scopes: ["read:emails"] }` — can only be used for specific operations
   - One-time credentials: `{ oneTime: true }` — deleted after first use

5. **Credential delegation:**
   - Agent A grants Agent B temporary access: `anima.vault.delegate(credentialId, targetAgentId, { ttl, scopes })`
   - Creates a scoped, time-limited reference — not a copy
   - Delegation chain tracked for audit
   - Revocable at any time by the granting agent

6. **Audit trail:**
   - Every credential access logged: who accessed, when, from where, what operation
   - Every refresh logged
   - Every delegation logged
   - Queryable via API: `GET /v1/vault/audit?credentialId=X&since=Y`

#### C4c — Multi-backend (Deferred — future scope)

7. **Backend evolution (DEFERRED):**
   - Keep Bitwarden as default backend for this roadmap
   - Future: Add provider interface for HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
   - Future: Provider selection per organization
   - Future: Migration tooling between providers

**Ready criteria:**
- OAuth tokens store, refresh automatically, and inject transparently
- API keys store and inject via proxy endpoint
- TTL and one-time credentials work
- Delegation creates scoped, time-limited access
- Audit trail captures all access
- All new credential types work through API/SDK/MCP/CLI

**Testing criteria:**
- OAuth refresh end-to-end test (store token → expire → auto-refresh → access succeeds)
- Secrets injection test (proxy request → credential injected → response returned → credential not in response)
- TTL expiration test (create with 1s TTL → wait → access fails)
- Delegation test (delegate → access succeeds → revoke → access fails)
- Audit trail completeness test (every operation produces audit entry)

**Business justification:** Alter Vault, Scalekit, 1Password, and HashiCorp are all building credential orchestration for agents. Your vault stores passwords — that's table stakes. The evolution to automatic OAuth refresh, secrets injection, and delegation is what enterprises need. An agent with 50 API integrations that never has secrets in its context is dramatically safer than one with hardcoded keys. This is also a strong revenue driver — credential management is a sticky, high-value feature.

---

### C5. Multi-Tenancy (Pods)

**Current state:** Single-tenant per API key. All agents in an organization share the same namespace. No isolation between end-users of a platform built on Anima.

**What to build:**

1. **Pod database model:**
   ```
   Pod {
     id          String
     orgId       String → Organization
     name        String
     slug        String (unique within org)
     status      PodStatus (ACTIVE, SUSPENDED, DELETED)
     limits      Json? (agent count, email volume, card count, etc.)
     metadata    Json?
     createdAt   DateTime
     updatedAt   DateTime
   }
   ```

2. **Pod scoping:**
   - Add optional `podId` to core models: Agent, Message, CardIdentity, PhoneIdentity, VaultIdentity, AddressIdentity, Webhook, SecurityEvent
   - Pod-scoped queries: all list/get operations filter by podId when present
   - Agents created within a pod can only access resources within that pod
   - Cross-pod access is forbidden (enforced at API layer)

3. **Pod API keys:**
   - `POST /v1/pods/:podId/keys` — generate pod-scoped API key
   - Pod API keys have prefix `pk_` to distinguish from org keys (`ak_`)
   - Pod keys can only access resources within their pod
   - Org-level keys can access all pods (admin access)

4. **Pod webhooks:**
   - Pod-specific webhook subscriptions
   - Events filtered by pod
   - Pod-scoped webhook signing keys

5. **Pod usage tracking:**
   - Usage metering per pod (email count, SMS count, card transactions, vault access)
   - Pod-level billing (for SaaS platforms that want to bill their customers)
   - Usage limits per pod (configurable by org admin)

6. **API surface:**
   - `POST /v1/pods` — create pod
   - `GET /v1/pods` — list pods
   - `GET /v1/pods/:id` — get pod
   - `PUT /v1/pods/:id` — update pod
   - `DELETE /v1/pods/:id` — delete pod (with cascade options)
   - `POST /v1/pods/:id/keys` — create pod-scoped API key
   - `GET /v1/pods/:id/usage` — get pod usage

7. **SDK, MCP, CLI integration:**
   - SDK: `anima.pods.create()`, `anima.pods.list()`, client-level pod selection `new Anima({ apiKey, podId })`
   - MCP: create_pod, list_pods, switch_pod context
   - CLI: `am pod create`, `am pod list`, `am pod use <id>` (sets default pod for subsequent commands)

**Ready criteria:**
- Pods create, list, get, update, delete
- Resources are isolated between pods
- Pod-scoped API keys only access their pod
- Usage tracking per pod works
- All existing operations work within pod context

**Testing criteria:**
- Isolation tests: create resource in Pod A → attempt access from Pod B → forbidden
- API key scoping tests: pod key → only sees pod resources
- Usage tracking tests: actions in pod → usage counters increment for that pod
- Cascade delete tests: delete pod → all pod resources cleaned up
- Backward compatibility: existing non-pod operations continue to work

**Business justification:** Agentmail has Pods and it's a key enterprise selling point. SaaS platforms building on Anima need per-customer isolation. Without multi-tenancy, platforms must manage isolation themselves — most will pick Agentmail instead. Pods also enable per-customer billing, which is a revenue driver for platform customers.

---

### C6. A2A Protocol Support

**Current state:** No A2A implementation. Agents can only communicate within Anima via internal APIs. No discovery, no inter-platform agent communication.

**What to build:**

1. **A2A Server (receiving tasks):**
   - Implement A2A protocol server endpoint
   - Endpoint: `POST /v1/agents/:agentId/a2a/tasks`
   - Task lifecycle: `submitted → working → input_required → completed | failed | canceled`
   - Streaming updates via Server-Sent Events (SSE) for long-running tasks
   - Authentication: verify sender's DID/credentials before accepting tasks
   - Task types: any capability the agent supports (send email, make payment, lookup info)

2. **A2A Client (sending tasks to external agents):**
   - SDK: `anima.a2a.discover(agentUrl)` — fetch Agent Card from remote agent
   - SDK: `anima.a2a.sendTask(agentUrl, task)` — send task to external A2A-compatible agent
   - SDK: `anima.a2a.streamTask(agentUrl, task)` — stream task updates
   - Task request signing with agent's private key (from DID)
   - Response verification (verify remote agent's DID)

3. **Integration with identity (C1):**
   - A2A Agent Cards reference the agent's DID
   - Task requests include sender's DID for verification
   - Trust score check: configurable minimum trust score to accept tasks from unknown agents
   - Capability matching: verify sender is requesting a capability the receiver supports

4. **A2A discovery:**
   - Agents discoverable via well-known URL: `/.well-known/agent.json`
   - Registry integration (C2): search registry for agents with specific capabilities
   - DNS-based discovery: `_a2a._tcp.agent.anima.email SRV`

5. **SDK, MCP, CLI integration:**
   - SDK: `anima.a2a.discover()`, `anima.a2a.sendTask()`, `anima.a2a.streamTask()`, `anima.a2a.listTasks()`, `anima.a2a.getTask()`
   - MCP tools: discover_agent, send_a2a_task, list_a2a_tasks
   - CLI: `am a2a discover <url>`, `am a2a send <url> <task>`, `am a2a tasks`

**Ready criteria:**
- Anima agents can receive A2A tasks from external agents
- Anima agents can send tasks to external A2A-compatible agents
- Task lifecycle works correctly (submit → work → complete/fail)
- DID-based authentication works for inter-agent communication
- Discovery via well-known URLs works

**Testing criteria:**
- A2A server receives and processes tasks
- A2A client sends tasks and receives responses
- DID verification works for sender authentication
- Task streaming works for long-running operations
- Trust score enforcement works (reject tasks from untrusted agents)
- Interoperability test: communicate with a non-Anima A2A agent (if available)

**Business justification:** A2A has 50+ technology partners and is under the Linux Foundation. It's becoming the standard for agent-to-agent communication. Without A2A, Anima agents are isolated islands. With A2A, they participate in the broader agent ecosystem — discovery, delegation, collaboration. This is the "agents operating like humans in our world" vision. Combined with the identity protocol (C1) and registry (C2), A2A makes Anima the platform where agents interact with the real world AND with each other.

---

## Phase D — Enterprise & Compliance

**Goal:** Make Anima enterprise-sellable with compliance certifications and operational tooling.
**Priority:** Starts after Phase A ships. SOC 2 prep should start early (long lead time).
**Dependency:** Phase A (product must be stable before compliance audit).

---

### D1. SOC 2 Certification Roadmap

**Current state:** Security building blocks exist: `@anima/security` has content scanning (PII/credential detection), injection scanning, rate limiting, security event logging. API key rotation exists. HMAC webhook signing exists. Clerk for auth with MFA support. But no formalized controls, no audit process, no compliance documentation.

**What to build:**

1. **Engage compliance automation platform:**
   - Evaluate: Vanta, Drata, Secureframe
   - Connect to infrastructure: GitHub (code changes), AWS (infrastructure), Clerk (access management), Stripe (PCI)
   - Auto-collect evidence for controls

2. **Security controls documentation (mapped to SOC 2 Trust Service Criteria):**
   - **CC1 — Control Environment:** Document security policies, org chart, roles/responsibilities
   - **CC2 — Communication:** Document how security policies are communicated to team
   - **CC3 — Risk Assessment:** Identify and document risks, mitigation strategies
   - **CC4 — Monitoring:** Document monitoring processes (security events, anomaly detection)
   - **CC5 — Control Activities:** Document access controls, change management, encryption
   - **CC6 — Logical & Physical Access:** Document API key management, admin access, MFA enforcement
   - **CC7 — System Operations:** Document incident response, backup/recovery, uptime monitoring
   - **CC8 — Change Management:** Document PR review requirements, CI/CD pipeline, deployment process
   - **CC9 — Risk Mitigation:** Document vendor management, business continuity

3. **Technical requirements to implement:**
   - **Immutable audit log:** Make `SecurityEvent` table append-only (revoke UPDATE/DELETE permissions, use database policies)
   - **Log retention:** Configure 1-year minimum retention for all audit logs
   - **Automated access reviews:** Script that reports all users with admin access, all API keys and their last use
   - **MFA enforcement:** Require MFA for all admin/console access (Clerk supports this)
   - **Encryption key rotation:** Schedule for rotating encryption keys (vault, webhook signing)
   - **Penetration testing:** Annual pen test by third-party firm
   - **Vulnerability scanning:** Automated dependency scanning (Snyk, Dependabot)
   - **Backup verification:** Regular backup restore tests

4. **Type I certification (point-in-time):**
   - Target: 4-8 weeks after controls are documented and implemented
   - Auditor reviews controls at a point in time
   - Deliverable: SOC 2 Type I report

5. **Type II certification (controls over time):**
   - Starts after Type I
   - 3-6 month observation period
   - Auditor reviews evidence that controls operated effectively over time
   - Deliverable: SOC 2 Type II report

**Ready criteria:**
- All security controls documented and implemented
- Compliance automation platform connected and collecting evidence
- Immutable audit log enforced
- MFA required for admin access
- Penetration test completed
- SOC 2 Type I audit passed

**Testing criteria:**
- Audit log immutability verified (attempt UPDATE/DELETE → fails)
- Access review script produces accurate report
- MFA enforcement verified (admin access without MFA → blocked)
- Backup restore test successful
- Vulnerability scan shows no critical/high findings

**Business justification:** Agentmail is SOC 2 Type I and II certified. Enterprise procurement requires it — it's a checkbox that blocks deals. Without SOC 2, Anima is locked out of companies with >100 employees. Vanta/Drata can accelerate the process since many of Anima's controls already exist in code.

---

### D2. Anomaly Detection & Behavioral Monitoring

**Current state:** `@anima/security` has pattern-based PII detection (SSN, credit cards, API keys), injection scanning (score-based with thresholds), rate limiting (in-memory + Redis), and security event logging. No behavioral analysis, no ML, no real-time alerting.

**What to build:**

1. **Behavioral baselines:**
   - Track per-agent metrics: email send rate (hourly/daily), SMS send rate, card transaction count and amounts, vault access frequency, API call frequency, unique recipients contacted
   - Establish baselines during first 7-14 days of agent operation
   - Store baselines in Redis for fast comparison
   - Update baselines on rolling 30-day window

2. **Anomaly detection engine:**
   - **Statistical detection (v1, no ML needed):**
     - Z-score based: flag if metric exceeds 3 standard deviations from baseline
     - Moving average: flag if current rate exceeds 5x the 24-hour moving average
     - Time-of-day awareness: baseline includes time patterns (agent active 9-5 → activity at 3am is anomalous)
   - **Rule-based triggers (configurable per org):**
     - "Alert if card spend exceeds $X in Y hours"
     - "Alert if agent sends email to more than Z unique recipients in one hour"
     - "Alert if agent accesses credentials it's never used before"
     - "Alert if agent makes transactions in a new country"
   - Default rules with sensible thresholds (configurable)

3. **Alert system:**
   - Alert channels: webhook, email to org admin, console notification
   - Optional integrations: Slack, PagerDuty (via webhook)
   - Alert severity: INFO, WARNING, CRITICAL
   - Alert deduplication: don't spam the same alert
   - Alert lifecycle: triggered → acknowledged → resolved

4. **Console dashboard:**
   - Real-time agent activity overview
   - Time-series charts: email volume, SMS volume, card transactions, vault access, API calls
   - Anomaly timeline: when alerts were triggered, for which agents, current status
   - Drill-down: click alert → see specific agent, event timeline, baseline vs actual

5. **Agent quarantine:**
   - **Soft quarantine:** Rate limit agent to 10% of normal baseline (grace period, 1 hour default)
   - **Hard quarantine:** Suspend agent API access completely
   - Automatic progression: anomaly score above WARNING threshold → soft quarantine, above CRITICAL → hard quarantine
   - Manual override: org admin can restore or permanently suspend from console
   - Quarantine notification: email + webhook + console alert to org admin with evidence

6. **API surface:**
   - `GET /v1/security/anomalies` — list anomaly alerts
   - `GET /v1/security/anomalies/:id` — get alert details with evidence
   - `PUT /v1/security/anomalies/:id/acknowledge` — acknowledge alert
   - `PUT /v1/security/anomalies/:id/resolve` — resolve alert
   - `GET /v1/security/baselines/:agentId` — view agent behavioral baseline
   - `PUT /v1/security/rules` — configure anomaly detection rules
   - `POST /v1/security/quarantine/:agentId` — manually quarantine agent
   - `DELETE /v1/security/quarantine/:agentId` — release from quarantine

**Ready criteria:**
- Behavioral baselines establish after 7-14 days of agent activity
- Anomaly detection triggers alerts on deviations
- Alerts deliver via configured channels
- Console dashboard shows real-time activity and anomaly timeline
- Quarantine works (soft and hard)
- Configurable rules per organization

**Testing criteria:**
- Baseline establishment test (14 days of simulated activity → baseline calculated)
- Anomaly trigger test (sudden spike → alert fires)
- Alert delivery test (webhook, email, console notification)
- Quarantine test (critical anomaly → agent access suspended → admin restores)
- False positive test (legitimate burst → no alert if within configured tolerance)
- Rule configuration test (custom rules trigger correctly)

**Business justification:** Strata Identity won "Best Identity Management for AI Agents" for their auditability features. Ping Identity's Agent Detection identifies agents through behavioral signals. Enterprise buyers must prove to compliance teams that agent behavior is monitored. Regulated industries (finance, healthcare, legal) require behavioral monitoring as part of their risk management framework. This is table stakes for enterprise sales.

---

### D3. Compliance Reporting

**Current state:** Usage tracking exists (`UsageEvent`, `UsageSummary` models). Security events logged to database. No compliance-specific reporting, no GDPR tooling, no PCI documentation.

**What to build:**

1. **GDPR/CCPA compliance:**
   - **Data Subject Access Request (DSAR) endpoint:**
     - `POST /v1/compliance/dsar` — initiate DSAR for a person (email or phone)
     - Searches across: emails, SMS messages, card transactions, vault credentials, security events, audit logs
     - Returns: comprehensive data export (JSON + PDF)
     - SLA: 30 days (GDPR requirement)
   - **Right to deletion:**
     - `POST /v1/compliance/delete` — cascade delete all data for a person
     - Verification step before execution (destructive operation)
     - Deletion receipt with timestamp and scope
     - Audit log entry (the deletion itself is logged, but deleted data is gone)
   - **Data retention policies:**
     - Configurable per org: 30 days, 90 days, 1 year, 7 years, indefinite
     - Auto-purge job: delete data older than retention period
     - Retention applies per data type (emails may have different retention than card transactions)
   - **Consent tracking:**
     - Log when/how consent was obtained for data processing
     - Consent type: explicit, legitimate interest, contractual necessity
     - Consent withdrawal endpoint
   - **DPA template:**
     - Data Processing Agreement template for enterprise customers
     - Available for download from console

2. **PCI DSS assessment:**
   - **Scope documentation:**
     - Document that card data flows through Stripe (PCI Level 1 certified)
     - Anima never stores raw PAN in its database (verify this)
     - Vault stores card data encrypted — document encryption method
     - Likely qualifies for SAQ-A (all card processing delegated to Stripe)
   - **Self-assessment questionnaire:**
     - Complete SAQ-A annually
     - Document in compliance dashboard
   - **Verification:**
     - Audit `@anima/cards` and `@anima/vault` for any PAN/CVV in logs
     - Add log scrubbing for card numbers (extend existing PII detection)

3. **Compliance dashboard (console page):**
   - Data retention status per data type
   - Pending DSARs with SLA countdown
   - Audit log completeness indicator
   - Encryption status (at rest, in transit)
   - Last access review date
   - Last penetration test date
   - SOC 2 control status (green/yellow/red)
   - PCI scope documentation link
   - Exportable compliance report (PDF)

4. **Regulatory audit trail:**
   - Every API call logged: timestamp, actor (API key ID), action, resource type, resource ID, IP address, user agent, result (success/failure)
   - **Tamper-evident logging:**
     - Hash chain: each log entry includes hash of previous entry
     - Or: append-only table with database-level protections
   - **Log export:**
     - `GET /v1/compliance/logs/export` — export logs in CEF or JSON format
     - Compatible with SIEM platforms: Splunk, Datadog, Elastic, Sumo Logic
   - **Retention:** Minimum 1 year, configurable up to 7 years for financial regulations

**Ready criteria:**
- DSAR endpoint works (submit request → receive comprehensive data export)
- Right to deletion cascades across all data stores
- Data retention policies auto-purge expired data
- Compliance dashboard shows accurate status
- Audit trail is tamper-evident
- Log export works in standard format

**Testing criteria:**
- DSAR test: create data across all services → submit DSAR → export contains all data
- Deletion test: create data → submit deletion → verify no data remains (including backups/caches)
- Retention test: create data with 1-day retention → wait → auto-purged
- Tamper-evidence test: attempt to modify audit log → detected/blocked
- Log export test: export → import into Splunk/Elastic → data is queryable
- PCI verification: scan all logs/databases for raw PAN → zero results

**Business justification:** GDPR fines can reach 4% of annual revenue or EUR 20M. PCI non-compliance can result in fines up to $100K/month. Any company dealing with EU citizens needs GDPR compliance. Any company handling card data needs PCI documentation. Compliance reporting is the difference between "developer tool" and "enterprise infrastructure" — and it justifies $99+/month enterprise pricing. This is also a trust signal: documented compliance tells enterprises that Anima takes data seriously.

---

### D4. Go SDK

**Current state:** Empty placeholder at `go/` with README saying "Coming soon", LICENSE, and .gitignore. No Go code.

**What to build:**

**Phased approach:**
- **D4a (start after Phase A):** Go SDK v1 with core 10 resources matching current Python/Node SDK parity (agents, cards, domains, emails, messages, organizations, phones, security, vault, webhooks)
- **D4b (start after Phase C):** Go SDK v2 adding identity, wallet, registry, a2a, address resources

1. **SDK architecture (D4a scope):**
   - Module: `github.com/anima-labs/anima-go`
   - Go 1.21+ (for slog, errors.Join, etc.)
   - Package structure (v1 — core resources):
     ```
     anima-go/
       anima.go          (Client struct, constructor)
       option.go         (functional options)
       agents.go         (AgentService)
       cards.go          (CardService)
       domains.go        (DomainService)
       emails.go         (EmailService)
       messages.go       (MessageService)
       organizations.go  (OrganizationService)
       phones.go         (PhoneService)
       security.go       (SecurityService)
       vault.go          (VaultService)
       webhooks.go       (WebhookService)
       errors.go         (Error types)
       http.go           (HTTP client internals)
       webhook_verify.go (Webhook signature verification)
     ```
   - v2 additions (after Phase C): `addresses.go`, `wallet.go`, `registry.go`, `identity.go`, `a2a.go`

2. **Idiomatic Go patterns:**
   - `context.Context` as first parameter on all methods
   - Functional options for client configuration: `anima.NewClient(apiKey, anima.WithBaseURL(...), anima.WithTimeout(...))`
   - Custom error types with `errors.Is/As` support: `*APIError`, `*AuthError`, `*NotFoundError`, `*RateLimitError`, `*ValidationError`
   - Return `(result, error)` — no panics
   - Struct types for all request/response objects
   - Pagination with iterator pattern

3. **HTTP client:**
   - Built on `net/http` with configurable `http.Transport`
   - Automatic retries with exponential backoff (configurable max retries, initial delay)
   - Rate limit handling (respect `Retry-After` header on 429)
   - Request/response logging (optional, via slog)
   - User-Agent header: `anima-go/v0.1.0`

4. **Code generation strategy:**
   - Option A: Generate from OpenAPI spec using `oapi-codegen` or Stainless
   - Option B: Hand-write (more idiomatic but higher maintenance)
   - Recommendation: Generate types and HTTP client, hand-write public API layer for ergonomics
   - Ensure generated code passes `golangci-lint`

5. **Testing:**
   - Unit tests with `httptest.Server` for mock HTTP
   - Integration tests against live API (tagged, opt-in)
   - Test coverage target: 80%+
   - CI pipeline: `go test ./...`, `golangci-lint run`, `go vet ./...`

6. **Documentation:**
   - Comprehensive godoc comments on all exported types and methods
   - README with installation, quickstart, full resource reference
   - Examples in `_examples/` directory
   - Published on pkg.go.dev

7. **Publishing:**
   - Tag releases: `v0.1.0`, `v0.2.0`, etc.
   - Go module proxy caching automatic
   - Add to CI: test → lint → tag → publish

**Ready criteria:**
- `go get github.com/anima-labs/anima-go` works
- All resources implemented (agents, cards, domains, emails, messages, orgs, phones, security, vault, webhooks, addresses, wallet, registry, identity, a2a)
- Webhook signature verification works
- Error types match Python/TypeScript SDKs
- godoc is comprehensive
- README matches Python/TypeScript SDK quality

**Testing criteria:**
- All unit tests pass
- Integration tests pass against live API
- golangci-lint passes with zero issues
- go vet passes
- Type parity verified against Python/TypeScript SDKs
- Webhook verification produces same results across all three SDKs

**Business justification:** Go is the #2 language for backend infrastructure. Kubernetes, Docker, Terraform, Consul — all Go. Infrastructure teams building agent orchestration often work in Go. Agentmail shipped a Go SDK. Without it, Anima loses the infrastructure engineer persona. Lowest priority because Python and TypeScript cover 80%+ of the AI developer market, but important for completeness and credibility.

---

## Effort Estimates & Timeline

**Assumptions:** Solo founder + AI-assisted development. Estimates in person-weeks.

| Item | Effort | Size |
|------|--------|------|
| A1 Python SDK Packaging | 0.5 weeks | S |
| A2 Console Wiring | 3-4 weeks | L |
| A3 CLI Completion | 1-2 weeks | M |
| A4 Documentation Site | 2-3 weeks | L |
| A5 Examples | 1-2 weeks | M |
| A6 Node SDK Parity | 0.5-1 week | S |
| A7 MCP Completeness + Hosted | 2-3 weeks | L |
| A8 Skills Completeness | 1 week | S |
| **Phase A Total** | **~12-16 weeks** | |
| B1 WebSocket Support | 2-3 weeks | L |
| B3 Agent Address Service | 2 weeks | M |
| B4 Framework Integrations | 3-4 weeks | L |
| B5 Registry Listings | 1 week | S |
| **Phase B Total** | **~8-10 weeks** | |
| C1 Identity Protocol (DID/VC) | 4-6 weeks | XL |
| C2 Agent Registry | 2-3 weeks | L |
| C3 Agent Wallet | 3-4 weeks | L |
| C4a OAuth Vault Core | 2-3 weeks | L |
| C4b Secrets Injection + Delegation | 2-3 weeks | L |
| C5 Multi-Tenancy (Pods) | 3-4 weeks | L |
| C6 A2A Protocol | 3-4 weeks | L |
| **Phase C Total** | **~20-28 weeks** | |
| D1 SOC 2 | 2-3 weeks eng + 3-6 months audit | L |
| D2 Anomaly Detection | 3-4 weeks | L |
| D3 Compliance Reporting | 2-3 weeks | L |
| D4a Go SDK v1 (core) | 2-3 weeks | L |
| D4b Go SDK v2 (identity/wallet) | 1-2 weeks | M |
| **Phase D Total** | **~12-16 weeks** (excl. audit wait) | |

**Target timeline (parallel execution, Approach B):**
- Phase A: Weeks 1-16
- Phase C design: Weeks 1-8 (protocol spec in parallel with A)
- Phase B: Weeks 12-22 (overlaps with late A)
- Phase C implementation: Weeks 16-44
- Phase D: Weeks 16-32 (SOC 2 prep starts early)

**Total to full platform: ~44-52 weeks** (roughly 10-12 months)

---

## Cross-Phase Dependencies

```
Phase A (Launch Readiness)
  ├─ A1 Python SDK ──────────────── no deps
  ├─ A2 Console ─────────────────── no deps
  ├─ A3 CLI ─────────────────────── no deps
  ├─ A4 Documentation ───────────── depends on A1, A6 (SDK docs)
  ├─ A5 Examples ────────────────── depends on A1, A6 (uses SDKs)
  ├─ A6 Node SDK ────────────────── no deps
  ├─ A7 MCP Server ──────────────── no deps
  └─ A8 Skills ──────────────────── depends on A7 (MCP tools)

Phase B (Developer Experience) — starts after Phase A core
  ├─ B1 WebSockets ──────────────── depends on A (stable API)
  ├─ B3 Agent Address ───────────── integration layer (SDK/MCP/CLI/Skills) assumes A1, A3, A6, A7 are complete
  ├─ B4 Framework Integrations ──── depends on A1, A6 (SDKs), B3 (address)
  └─ B5 Registry Listings ──────── depends on A7 (MCP complete)

Phase C (Identity & Commerce) — design parallel with A, implement after A
  ├─ C1 Identity Protocol ──────── no deps (new protocol)
  ├─ C2 Agent Registry ─────────── depends on C1 (DIDs, Agent Cards)
  ├─ C3 Agent Wallet ────────────── depends on A (stable cards), C1 (DID for wallet)
  ├─ C4a OAuth Vault Core ────────── no deps (extends existing vault)
  ├─ C4b Secrets Injection ──────── depends on C4a
  ├─ C5 Multi-Tenancy (Pods) ──── depends on A (stable API); should implement before/concurrently with B3, C3, C4 to avoid retrofitting pod scoping
  └─ C6 A2A Protocol ────────────── depends on C1 (DIDs), C2 (discovery)

Phase D (Enterprise) — starts after Phase A
  ├─ D1 SOC 2 ───────────────────── depends on A (stable product to audit)
  ├─ D2 Anomaly Detection ──────── no deps (new system)
  ├─ D3 Compliance Reporting ──── depends on D1 (SOC 2 controls)
  ├─ D4a Go SDK v1 (core) ────────── depends on A (stable API, SDK parity reference)
  └─ D4b Go SDK v2 (identity/wallet) ── depends on C1-C6
```

---

## Success Metrics

| Metric | Phase A Target | Phase B Target | Phase C Target | Phase D Target |
|--------|---------------|---------------|---------------|---------------|
| SDK downloads/month | 1,000 | 5,000 | 10,000 | 15,000 |
| MCP server installs | 500 | 2,000 | 5,000 | 8,000 |
| Registered agents | 100 | 1,000 | 10,000 | 50,000 |
| GitHub stars (total) | 200 | 1,000 | 3,000 | 5,000 |
| Enterprise customers | 0 | 5 | 20 | 50 |
| Monthly revenue | $0 | $5K | $50K | $200K |
| Registered DIDs | — | — | 5,000 | 25,000 |
| Registry listings | — | — | 1,000 | 10,000 |

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| DID method registration rejected | High | Low | Follow W3C process, engage community early |
| SOC 2 audit finds critical gaps | High | Medium | Start compliance prep in Phase A, use automation platform |
| Competitor ships unified platform first | High | Medium | Parallel tracks (Approach B) accelerates identity protocol |
| Stripe Issuing limits block card scaling | Medium | Medium | Evaluate alternative issuers (Marqeta, Lithic) as backup |
| Telnyx shared profile compliance issue | Medium | High | Migrate to per-customer profiles before >50 orgs (documented in BUSINESS_PLAN) |
| Protocol adoption is slow | Medium | Medium | Open-source spec, engage AAIF, submit IETF draft |
| Python SDK name collision on PyPI | Low | Medium | Check availability early, have backup names |
| WebSocket scalability issues | Medium | Low | Start with Redis pub/sub, upgrade to dedicated message broker if needed |

---

## Glossary

- **DID:** Decentralized Identifier — W3C standard for cryptographically verifiable, self-sovereign identifiers
- **VC:** Verifiable Credential — W3C standard for tamper-evident, cryptographically verifiable claims
- **A2A:** Agent-to-Agent protocol — Google-originated standard for agent discovery and communication
- **MCP:** Model Context Protocol — Anthropic-originated standard for agent-tool integration
- **KYA:** Know Your Agent — verification process linking agents to responsible humans/orgs
- **KYB:** Know Your Business — business identity verification (via Stripe Connect in Anima)
- **x402:** HTTP payment protocol using 402 status code — Coinbase/Cloudflare standard
- **AP2:** Agents-to-Payments Protocol — Originally developed by Google, open protocol for agent commerce with 60+ partners (PayPal, Coinbase, Mastercard, etc.). May be contributed to AAIF/Linux Foundation.
- **ANS:** Agent Name Service — IETF draft for DNS-like agent discovery
- **AAIF:** Agentic AI Foundation — Linux Foundation body stewarding MCP, A2A, goose
- **Pod:** Isolated tenant container within an organization (multi-tenancy unit)
- **AVS:** Address Verification System — card network fraud prevention via billing address matching
- **DSAR:** Data Subject Access Request — GDPR right to access personal data
- **SAQ-A:** PCI Self-Assessment Questionnaire type A — for merchants delegating all card processing
