# Anima Platform — Progress Tracker

**Last updated:** 2026-04-05
**Spec:** [Roadmap Design](specs/2026-03-28-anima-platform-roadmap-design.md)

---

## Overview

| Phase | Name | Status | Tasks | Progress |
|-------|------|--------|-------|----------|
| **A** | Launch Readiness | ✅ Complete | 8/8 | █████████████████████ 100% |
| **B** | Developer Experience | ✅ Complete | 5/5 | █████████████████████ 100% |
| **C** | Agent Identity & Commerce | ✅ Complete | 6/6 | █████████████████████ 100% |
| **D** | Enterprise & Compliance | ✅ Complete | 4/4 | █████████████████████ 100% |
| **E** | Vault Identity Platform | 🔄 In Progress | 0/16 | ░░░░░░░░░░░░░░░░░░░░░ 0% |

---

## Phase A — Launch Readiness ✅

> Make Anima shippable as a competitive product. Fix SDK packaging, wire console, complete CLI, ship docs, add examples, ensure MCP/Skills parity.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| A1 | Fix Python SDK Packaging & README | ✅ Done | `python/` | README rewritten, pyproject.toml updated, exports verified |
| A2 | Wire Console to Real APIs | ⏭️ Deferred | `anima/` | Console page wiring deferred to post-launch (pages exist, partial real data) |
| A3 | Complete CLI Gaps | ✅ Done | `cli/` | Webhook + security command groups added |
| A4 | Ship Documentation | ✅ Done | `docs/` | Quickstarts (email, vault), phone, MCP, SDKs, navigation restructured |
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

## Phase C — Agent Identity & Commerce ✅

> Build the identity protocol moat. DID/VC, agent registry, wallet with x402, OAuth vault, multi-tenancy, A2A.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| C1 | Agent Identity Protocol (DID + VC + Agent Cards) | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | `did:anima` method, Ed25519 keypairs, W3C DID Core 1.0 documents, JWT-VC issuance/verification, 7 credential types, StatusList2021 revocation, Agent Card generation, `/.well-known/agent.json` endpoint |
| C2 | Agent Registry & Discovery | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | Public registry with DID-indexed entries, search by capability/trust/KYA/tags, auto-detected capabilities, SDK resources + MCP tools + CLI commands |
| C3 | Agent Wallet with x402 + AP2 | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | Wallet model with daily/monthly budget guards, x402 payment protocol fetch, smart counter resets, freeze/unfreeze, SDK + MCP + CLI surface |
| C4 | OAuth Token Vault (Credential Orchestrator) | ✅ Done | `anima/` | Extended credential types (oauth_token, api_key, certificate), background token refresh worker (60s scan), credential audit logging |
| C5 | Multi-Tenancy (Pods) | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | Pod model with slug uniqueness, pod-scoped isolation on 7 core models, `pk_` prefixed API keys, usage counting, soft delete, SDK + MCP + CLI surface |
| C6 | A2A Protocol Support | ✅ Done | `anima/`, `node/`, `python/`, `mcp/`, `cli/` | Google A2A protocol types + client, task lifecycle (submitted→working→completed/failed/canceled), trust score gate, history events, SDK + MCP + CLI surface |

---

## Phase D — Enterprise & Compliance ✅

> SOC 2, anomaly detection, compliance reporting, Go SDK.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| D1 | SOC 2 Certification Roadmap | ✅ Done | `anima/`, `node/`, `python/`, `go/` | Immutable AuditLog (append-only, batch insert, Hono middleware), AccessReview model, 33 SOC 2 Trust Service Criteria (CC1-CC9, A1), ComplianceControl + EvidenceItem models, automated evidence collection, platform→control auto-mapping, CSV/JSON audit export, SDK resources |
| D2 | Anomaly Detection & Behavioral Monitoring | ✅ Done | `anima/`, `node/`, `python/`, `go/` | AgentBaseline with hourly patterns, 6 behavioral metrics, z-score/rate-multiplier/time-violation/absolute-threshold detection, AnomalyRule engine with cooldown, soft/hard quarantine with auto-escalation, background workers (5min detection + 6hr baseline), anomaly API (13 endpoints), SDK resources |
| D3 | Compliance Reporting | ✅ Done | `anima/`, `node/`, `python/`, `go/` | ComplianceReport + DataSubjectRequest models, 5 report templates (SOC 2 summary, activity, access review, audit export, GDPR DSAR), compliance dashboard, DSAR lifecycle with SLA tracking, report generation/export, SDK resources |
| D4 | Go SDK | ✅ Done | `go/` | Full-featured Go SDK (`github.com/anima-labs/anima-go`), zero external dependencies, generic HTTP client with retries/backoff, typed errors with errors.Is/As, generic pagination iterator, webhook HMAC-SHA256 verification, 19 resource services covering all Phase A-D features |

---

## Phase E — Vault Identity Platform 🔄

> Transform mcp-vault from a Bitwarden-backed CRUD store into a market-leading agent secrets platform. Per-agent encryption, secret injection, ephemeral tokens, policy enforcement, cross-channel analytics, identity federation.

| # | Task | Status | Repos | Key Deliverables |
|---|------|--------|-------|-----------------|
| E1 | Enable Vault Feature Flag | ⬜ Pending | `anima/` | Feature flag ON, health check, error handling |
| E2 | Per-Agent Encryption Keys | ⬜ Pending | `anima/` | HKDF-derived agent DEKs, credential-level encryption |
| E3 | Cross-Module Integration | ⬜ Pending | `anima/` | Vault → email, phone credential resolution |
| E4 | Credential Sharing | ⬜ Pending | `anima/` | CredentialShare model, agent/member/pod scoping |
| E5 | Ephemeral Scoped Credentials | ⬜ Pending | `anima/` | VaultToken with TTL, scope, task binding, revocation |
| E6 | Intent-Aware Policy Engine | ⬜ Pending | `anima/` | Allow/Deny/Observe/StepUp per tool call |
| E7 | Step-Up Authorization | ⬜ Pending | `anima/` | Approval flow with email/SMS notification |
| E8 | CLI Credential Injection | ⬜ Pending | `cli/`, `anima/` | `am vault exec` with env var injection |
| E9 | Browser Autofill | ⬜ Pending | `anima/apps/extension/`, `anima/` | Chrome extension vault autofill |
| E10 | Cross-Channel Analytics | ⬜ Pending | `anima/` | pgvector behavioral profiles, risk scores |
| E11 | Forensic Traceability | ⬜ Pending | `anima/` | Delegation chains, prompt hash, audit context |
| E12 | Identity Federation (OIDC) | ⬜ Pending | `anima/` | OIDC provider, "Sign in with Anima" |
| E13 | Update All SDKs | ⬜ Pending | `node/`, `python/`, `go/` | Vault tokens, policies, sharing, analytics resources |
| E14 | Update MCP Servers | ⬜ Pending | `mcp-vault/`, `mcp/`, `mcp-core/` | 10+ new vault MCP tools |
| E15 | Update CLI | ⬜ Pending | `cli/` | Token, policy, sharing, analytics commands |
| E16 | Update Docs & Skills | ⬜ Pending | `docs/`, `skill/`, `anima/` | Full vault documentation, llm.txt, blog post, examples |

**Plan:** [Phase E Implementation Plan](plans/2026-04-05-phase-e-vault-identity-platform.md)
**Spec:** [Vault Identity Platform Design](specs/2026-04-05-vault-identity-platform-design.md)
**Business:** [Vault Business Plan](specs/2026-04-05-vault-business-plan.md)

---

## Repo Inventory

| Repo | Package | Description | Status |
|------|---------|-------------|--------|
| `anima/` | — | Core platform (API, Console, DB, Contracts) | Active |
| `node/` | `@anima-labs/sdk` | TypeScript/Node SDK | Published |
| `python/` | `anima-labs` | Python SDK (sync + async) | Published |
| `cli/` | `@anima-labs/cli` | CLI tool (`am` command) | Published |
| `mcp/` | `@anima-labs/mcp` | MCP server (160+ tools) | Published |
| `skill/` | — | Claude Code Skill (SKILL.md) | Published |
| `toolkit/` | Various | Framework integrations (7 platforms) | Published |
| `docs/` | — | Documentation site content (MDX) | Active |
| `examples/` | — | Example agents (7 examples) | Active |
| `go/` | `github.com/anima-labs/anima-go` | Go SDK (19 services) | Published |
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

### Phase C (2026-03-28)
- `anima/` — `agent-identity` package (DID, VC, Agent Cards), registry, wallet, OAuth vault, pods, A2A protocol
- `node/` — Identity, Registry, Wallet, Pods, A2A resources
- `python/` — Identity, Registry, Wallet, Pods, A2A resources (sync + async)
- `mcp/` — Identity, Registry, Wallet, Pod, A2A tool groups (29 new tools)
- `cli/` — Identity, Registry, Wallet, Pod, A2A command groups

### Phase D (2026-03-28)
- `anima/` — Immutable audit log, SOC 2 controls (33 criteria), evidence collection, behavioral baselines, anomaly detection engine, quarantine, compliance reporting, DSAR support, background workers
- `node/` — Audit, Compliance, Anomaly resources
- `python/` — Audit, Compliance, Anomaly resources (sync + async)
- `go/` — **New repo** — Full Go SDK with 19 resource services, HTTP client, errors, pagination, webhook verification
