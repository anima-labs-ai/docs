# Anima Platform — Progress Tracker

**Last updated:** 2026-03-28
**Spec:** [Roadmap Design](specs/2026-03-28-anima-platform-roadmap-design.md)

---

## Overview

| Phase | Name | Status | Tasks | Progress |
|-------|------|--------|-------|----------|
| **A** | Launch Readiness | ✅ Complete | 8/8 | █████████████████████ 100% |
| **B** | Developer Experience | ✅ Complete | 5/5 | █████████████████████ 100% |
| **C** | Agent Identity & Commerce | 🔲 Not Started | 0/6 | ░░░░░░░░░░░░░░░░░░░░░ 0% |
| **D** | Enterprise & Compliance | 🔲 Not Started | 0/4 | ░░░░░░░░░░░░░░░░░░░░░ 0% |

---

## Phase A — Launch Readiness ✅

> Make Anima shippable as a competitive product. Fix SDK packaging, wire console, complete CLI, ship docs, add examples, ensure MCP/Skills parity.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| A1 | Fix Python SDK Packaging & README | ✅ Done | `python/` | README rewritten, pyproject.toml updated, exports verified |
| A2 | Wire Console to Real APIs | ⏭️ Deferred | `anima/` | Console page wiring deferred to post-launch (pages exist, partial real data) |
| A3 | Complete CLI Gaps | ✅ Done | `cli/` | Webhook + security command groups added |
| A4 | Ship Documentation | ✅ Done | `docs/` | Quickstarts (email, cards, vault), phone, MCP, SDKs, navigation restructured |
| A5 | Compelling Examples | ✅ Done | `examples/` | E-commerce, support, and travel agents (7 total examples) |
| A6 | Node SDK Audit & Parity | ✅ Done | `node/` | ConflictError/InternalServerError added, README updated |
| A7 | MCP Server Completeness | ✅ Done | `mcp/` | 77→133+ tools, `--tools` selective loading, README rewritten |
| A8 | Skills Completeness | ✅ Done | `skill/` | Audited — 117+ tools across 15 categories, production-ready |

---

## Phase B — Developer Experience ✅

> Elevate DX to best-in-class. Real-time events, first-class addresses, framework integrations, registry discoverability.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| B1 | WebSocket Support | ✅ Done | `anima/`, `node/`, `python/` | EventHub + channel matcher server, `AnimaEventStream` (Node), sync+async `EventStream` (Python) |
| B2 | Hosted MCP Endpoint | ⏭️ Deferred | — | Already supported via HTTP transport in MCP server |
| B3 | Agent Address Service | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | Prisma model, oRPC contracts, CRUD+validate API, SDK resources, 6 MCP tools, CLI commands |
| B4 | Framework Integrations | ✅ Done | `toolkit/`, `skill/` | LangChain/Vercel AI/OpenAI Agents expanded 8→23 tools; OpenClaw, Codex, OpenCode, Cowork integrations |
| B5 | Registry Listings | ✅ Done | `mcp/` | Smithery manifest, MCP Registry manifest |

---

## Phase C — Agent Identity & Commerce 🔲

> Build the identity protocol moat. DID/VC, agent registry, wallet with x402, OAuth vault, multi-tenancy, A2A.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| C1 | Agent Identity Protocol (DID + VC + Agent Cards) | 🔲 Not Started | `anima/` | DID document generation, VC issuance, Agent Card standard, `.well-known/agent.json` |
| C2 | Agent Registry & Discovery | 🔲 Not Started | `anima/` | Public agent registry, search/discovery API, trust scoring, DNS-based discovery |
| C3 | Agent Wallet with x402 + AP2 | 🔲 Not Started | `anima/` | x402 payment protocol, AP2 agent-to-agent payments, wallet balance management |
| C4 | OAuth Token Vault (Credential Orchestrator) | 🔲 Not Started | `anima/` | OAuth flow management, token refresh, scoped delegation, 3rd-party service auth |
| C5 | Multi-Tenancy (Pods) | 🔲 Not Started | `anima/` | Isolated agent environments, resource quotas, cross-pod communication |
| C6 | A2A Protocol Support | 🔲 Not Started | `anima/`, `examples/` | Google A2A protocol implementation, agent-to-agent task delegation |

---

## Phase D — Enterprise & Compliance 🔲

> SOC 2, anomaly detection, compliance reporting, Go SDK.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| D1 | SOC 2 Certification Roadmap | 🔲 Not Started | `anima/` | Control mapping, audit trails, access reviews, evidence collection |
| D2 | Anomaly Detection & Behavioral Monitoring | 🔲 Not Started | `anima/` | ML-based anomaly detection, behavioral baselines, alerting |
| D3 | Compliance Reporting | 🔲 Not Started | `anima/` | Automated compliance reports, regulatory templates, audit exports |
| D4 | Go SDK | 🔲 Not Started | `go/` | Full-featured Go client SDK with all resources |

---

## Repo Inventory

| Repo | Package | Description | Status |
|------|---------|-------------|--------|
| `anima/` | — | Core platform (API, Console, DB, Contracts) | Active |
| `node/` | `@anima-labs/sdk` | TypeScript/Node SDK | Published |
| `python/` | `anima-labs` | Python SDK (sync + async) | Published |
| `cli/` | `@anima-labs/cli` | CLI tool (`am` command) | Published |
| `mcp/` | `@anima-labs/mcp` | MCP server (133+ tools) | Published |
| `skill/` | — | Claude Code Skill (SKILL.md) | Published |
| `toolkit/` | Various | Framework integrations (7 platforms) | Published |
| `docs/` | — | Documentation site content (MDX) | Active |
| `examples/` | — | Example agents (7 examples) | Active |
| `opencode/` | — | OpenCode project (separate) | Independent |

---

## Commit Log (Phase A + B)

### Phase A (2026-03-28)
- `python/` — `fix(python-sdk): update README and pyproject.toml`
- `node/` — `feat(node-sdk): audit parity with Python SDK, update README`
- `cli/` — `feat(cli): add webhook and security command groups`
- `mcp/` — `feat(mcp): add missing tools, selective loading, config templates`
- `docs/` — Quickstarts, vault/phone/MCP docs, navigation restructured
- `examples/` — E-commerce, support, travel agents added
- `anima/` — `feat: add static OpenAPI spec generation script`

### Phase B (2026-03-28)
- `anima/` — `feat: add Agent Address Service (B3)` + `feat: add WebSocket event streaming (B1)`
- `node/` — `feat: add AddressesResource` + `feat: add WebSocket real-time event streaming`
- `python/` — `feat: add AddressesResource` + `feat: add WebSocket real-time event streaming`
- `mcp/` — `feat: add address tool group` + `feat: add Smithery and MCP Registry manifests (B5)`
- `cli/` — `feat: add address commands`
- `toolkit/` — LangChain/Vercel/OpenAI expansion, OpenClaw, Codex, OpenCode, Cowork integrations, README update
- `skill/` — Address tools section added
