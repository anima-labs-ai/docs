# Phase D — Enterprise & Compliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Anima enterprise-sellable. SOC 2 certification infrastructure, ML-based anomaly detection, automated compliance reporting, and a full-featured Go SDK. Transform Anima from a developer tool into an enterprise platform.

**Architecture:** Multi-repo at `/Users/diyanbogdanov/projects/agenticmail/`. Core platform at `anima/` (packages: `security`, `contracts`, `db`, `agent-identity`). SDKs at `python/`, `node/`, and `go/` (new). Docs at `docs/`.

**Tech Stack:** TypeScript (Bun), Go 1.21+, Hono, oRPC, Prisma, Redis (baselines/time-series), Zod

**Spec:** `docs/superpowers/specs/2026-03-28-anima-platform-roadmap-design.md` (Phase D section)

**Depends on:** Phase A complete (stable product to audit). D3 depends on D1. D4b depends on Phase C.

---

## Task 1: SOC 2 Control Mapping & Immutable Audit Log (D1 — Part 1)

**Files:**
- Modify: `anima/packages/db/prisma/schema.prisma` (AuditLog model, AccessReview model)
- Create: `anima/packages/security/src/audit-logger.ts`
- Create: `anima/packages/security/src/types/audit.ts`
- Modify: `anima/packages/security/src/index.ts` (export audit-logger)
- Create: `anima/packages/contracts/src/schemas/audit.ts`
- Create: `anima/packages/contracts/src/contracts/audit.ts`
- Modify: `anima/packages/contracts/src/contracts/index.ts` (add audit contract)
- Modify: `anima/apps/api/src/router.ts` (add audit routes)

- [ ] **Step 1: Create immutable AuditLog Prisma model**

Add `AuditLog` and `AccessReview` models to schema.prisma. AuditLog is append-only with indexes on orgId+createdAt, actorId+createdAt, resourceType+resourceId, and action. Fields: id, orgId, actorType (api_key/user/system/agent), actorId, action, resourceType, resourceId, result (success/failure/denied), ipAddress, userAgent, metadata (Json), createdAt.

AccessReview model: id, orgId, reviewerId, reviewType (quarterly/ad_hoc/offboarding), status (pending/in_progress/completed), findings (Json), completedAt, createdAt, updatedAt.

- [ ] **Step 2: Create audit logger service**

Create `anima/packages/security/src/audit-logger.ts`:
- `logAuditEvent(event: AuditEvent)` — writes to AuditLog table
- Batch insert support (queue + flush every 100ms or 50 events)
- `createAuditMiddleware()` — Hono middleware that auto-logs every API request
- Extracts actor info from auth context, action from HTTP method+path, result from response status

Create `anima/packages/security/src/types/audit.ts` with typed enums.

- [ ] **Step 3: Wire audit middleware into API router**

Add `createAuditMiddleware()` as global middleware in `router.ts`. Exclude health check and public DID resolution routes.

- [ ] **Step 4: Create audit query contracts and API routes**

Contracts: `listAuditLogs`, `getAuditLog`, `exportAuditLogs` (CSV/JSON), `createAccessReview`, `listAccessReviews`, `completeAccessReview`.

---

## Task 2: SOC 2 Evidence Collection & Control Framework (D1 — Part 2)

**Files:**
- Create: `anima/packages/security/src/soc2-controls.ts`
- Create: `anima/packages/security/src/evidence-collector.ts`
- Modify: `anima/packages/db/prisma/schema.prisma` (ComplianceControl, EvidenceItem models)
- Create: `anima/packages/contracts/src/schemas/compliance-controls.ts`
- Create: `anima/packages/contracts/src/contracts/compliance-controls.ts`
- Modify: `anima/apps/api/src/router.ts`

- [ ] **Step 1: Create ComplianceControl and EvidenceItem Prisma models**

ComplianceControl: id, orgId, framework (SOC2/GDPR/PCI), controlId (CC1.1 etc.), title, description, category (CC1-CC9, A1, PI1, C1, P1), status (not_started/in_progress/implemented/verified/failed), owner, lastTestedAt, nextReviewAt. Unique on [orgId, framework, controlId].

EvidenceItem: id, controlId (FK), type (automated/manual/screenshot/document), source (github/aws/clerk/internal/manual), title, description, content (Json), url, collectedAt, expiresAt.

- [ ] **Step 2: Create SOC 2 control mapping**

Create `soc2-controls.ts` with pre-defined Trust Service Criteria (CC1-CC9, A1). `seedSoc2Controls(orgId)` creates all control records. `mapExistingControlsToEvidence(orgId)` auto-maps platform features.

- [ ] **Step 3: Create automated evidence collector**

Create `evidence-collector.ts`: `collectAutomatedEvidence(orgId, controlId)` gathers evidence from platform data. Evidence items auto-expire after 90 days.

- [ ] **Step 4: Create compliance control contracts and API routes**

Contracts: `listControls`, `getControl`, `updateControlStatus`, `seedFramework`, `listEvidence`, `addEvidence`, `collectEvidence`, `getComplianceSummary`.

---

## Task 3: Behavioral Baselines & Metrics Collection (D2 — Part 1)

**Files:**
- Create: `anima/packages/security/src/behavioral-baseline.ts`
- Create: `anima/packages/security/src/metrics-collector.ts`
- Create: `anima/packages/security/src/types/anomaly.ts`
- Modify: `anima/packages/db/prisma/schema.prisma` (AgentBaseline, AnomalyAlert, AnomalyRule models)
- Modify: `anima/packages/security/src/index.ts`

- [ ] **Step 1: Create anomaly-related Prisma models**

AgentBaseline: agentId, orgId, metric (email_send_rate/sms_send_rate/card_txn_count/vault_access_rate/api_call_rate/unique_recipients), period (hourly/daily), mean, stddev, sampleCount, hourlyPattern (Json), windowStart, windowEnd. Unique on [agentId, metric, period].

AnomalyAlert: orgId, agentId, metric, severity (INFO/WARNING/CRITICAL), status (TRIGGERED/ACKNOWLEDGED/RESOLVED/FALSE_POSITIVE), baselineValue, actualValue, zScore, ruleId, details (Json), acknowledgedBy/At, resolvedBy/At.

AnomalyRule: orgId, name, metric, condition (zscore_gt/rate_multiplier_gt/absolute_gt/time_violation), threshold, severity, quarantineAction (NONE/SOFT/HARD), cooldownMinutes, enabled.

Add `quarantineLevel` and `quarantinedAt` to Agent model.

- [ ] **Step 2: Create metrics collector**

Create `metrics-collector.ts`: `collectAgentMetrics(agentId, period)` queries UsageEvent, Message, SecurityEvent tables. `storeMetricSnapshot()` for time-series storage.

- [ ] **Step 3: Create behavioral baseline engine**

Create `behavioral-baseline.ts`: `computeBaseline()`, `updateBaseline()`, `isBaselineReady()`, `getBaselineComparison()` with time-of-day awareness.

---

## Task 4: Anomaly Detection Engine & Alerting (D2 — Part 2)

**Files:**
- Create: `anima/packages/security/src/anomaly-detector.ts`
- Create: `anima/packages/security/src/quarantine.ts`
- Create: `anima/packages/contracts/src/schemas/anomaly.ts`
- Create: `anima/packages/contracts/src/contracts/anomaly.ts`
- Modify: `anima/apps/api/src/router.ts`
- Create: `anima/apps/api/src/workers/anomaly-detection-worker.ts`
- Create: `anima/apps/api/src/workers/baseline-computation-worker.ts`

- [ ] **Step 1: Create anomaly detection engine**

Z-score detection, rate multiplier, time-of-day violation, absolute threshold. Cooldown support. Alert dispatching via webhooks + email.

- [ ] **Step 2: Create quarantine manager**

Soft quarantine (10% rate limit), hard quarantine (suspend access), release. Auto-quarantine on CRITICAL alerts.

- [ ] **Step 3: Create background workers**

Anomaly detection worker (every 5 min), baseline computation worker (every 6 hours).

- [ ] **Step 4: Create anomaly contracts and API routes**

Contracts: alerts (list/get/acknowledge/resolve/false-positive), rules (CRUD), baselines (get), quarantine (set/release).

---

## Task 5: Compliance Reporting Engine (D3)

**Files:**
- Create: `anima/packages/security/src/compliance-reporter.ts`
- Create: `anima/packages/security/src/report-templates.ts`
- Modify: `anima/packages/db/prisma/schema.prisma` (ComplianceReport, DataSubjectRequest models)
- Create: `anima/packages/contracts/src/schemas/compliance.ts`
- Create: `anima/packages/contracts/src/contracts/compliance.ts`
- Modify: `anima/apps/api/src/router.ts`

- [ ] **Step 1: Create ComplianceReport and DataSubjectRequest Prisma models**
- [ ] **Step 2: Create report templates** (soc2_summary, activity_report, access_review, audit_export, gdpr_dsar)
- [ ] **Step 3: Create compliance reporter service** (generateReport, exportReport, dashboard data)
- [ ] **Step 4: Create compliance contracts and API routes** (reports CRUD, DSAR lifecycle, dashboard)

---

## Task 6: Compliance SDK Surface (Node + Python)

**Files:**
- Create: `node/src/resources/audit.ts`, `compliance.ts`, `anomaly.ts`
- Modify: `node/src/index.ts`, `node/src/types.ts`
- Create: `python/src/anima/resources/audit.py`, `compliance.py`, `anomaly.py`
- Modify: `python/src/anima/_client.py`, `python/src/anima/_types.py`

- [ ] **Step 1: Add audit, compliance, anomaly resources to Node SDK**
- [ ] **Step 2: Add audit, compliance, anomaly resources to Python SDK**

---

## Task 7: Go SDK Core Setup + HTTP Client (D4a — Part 1)

**Files (new `go/` repo):**
- Create: `go/go.mod`, `go/anima.go`, `go/option.go`, `go/http.go`, `go/errors.go`, `go/pagination.go`, `go/webhook_verify.go`
- Create: tests for each

- [ ] **Step 1: Initialize Go module and create client** (`github.com/anima-labs/anima-go`, Go 1.21+)
- [ ] **Step 2: Create HTTP client internals** (retries, backoff, Retry-After, context)
- [ ] **Step 3: Create error types** (APIError, sentinel errors, errors.Is/As support)
- [ ] **Step 4: Create pagination iterator** (generic Page[T], ListIterator[T])
- [ ] **Step 5: Create webhook verification** (HMAC-SHA256)

---

## Task 8: Go SDK Resource Services (D4a — Part 2)

**Files:**
- Create: `go/agents.go`, `go/cards.go`, `go/domains.go`, `go/emails.go`, `go/messages.go`, `go/organizations.go`, `go/phones.go`, `go/security.go`, `go/vault.go`, `go/webhooks.go`
- Create: tests and examples

- [ ] **Step 1: Create Agent and Organization services**
- [ ] **Step 2: Create messaging services** (Email, Messages, Domains)
- [ ] **Step 3: Create Cards, Phones, Vault, Security services**
- [ ] **Step 4: Create Webhook service and examples**
- [ ] **Step 5: CI, linting, README**

---

## Task 9: Go SDK Phase C Resources (D4b)

- [ ] **Step 1: Add identity, registry, wallet services**
- [ ] **Step 2: Add A2A, addresses, pods services**

---

## Task 10: Go SDK Enterprise Resources (D4 + D1-D3)

- [ ] **Step 1: Add audit, compliance, anomaly services to Go SDK**

---

## Execution Strategy

```
Wave 1 — Tasks 1, 3, 7 in parallel (independent)
Wave 2 — Tasks 2, 4, 8 in parallel (each depends on its Wave 1 counterpart)
Wave 3 — Tasks 5, 6 in parallel (depend on Tasks 1-4)
Wave 4 — Task 9 (depends on Task 8 + Phase C)
Wave 5 — Task 10 (depends on Tasks 5-6 + Task 8)
```
