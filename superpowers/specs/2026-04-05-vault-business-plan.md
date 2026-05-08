# Vault Identity Platform — Business Plan

> **Date:** April 5, 2026
> **Author:** Diyan Bogdanov
> **Status:** Active

---

## 1. Market Opportunity

### 1.1 The Problem

AI agents are being given static API keys, long-lived passwords, and hardcoded credentials to operate in production. This creates three critical risks:

1. **LLM exposure** — Secrets passed to an agent enter the LLM's context window, where they can be leaked via prompt injection, logged in traces, or extracted by adversarial inputs
2. **Credential sprawl** — 29 million new hardcoded secrets were found on public GitHub in 2025 (34% YoY increase). 24,008 unique secrets found in MCP config files alone
3. **Zero audit trail** — When an agent uses a shared credential, there's no way to know which agent accessed what, when, or why

### 1.2 Market Size

- Password management market: ~$2B+ (growing with agent adoption)
- Secrets management market: ~$3.5B by 2028
- AI agent infrastructure market: ~$47.5B by 2028
- Non-human identity security: fastest-growing IAM subcategory (29% CAGR)

### 1.3 Market Timing

The market is at an inflection point:
- **$100M+ in disclosed funding** to agent vault/identity startups since early 2025
- Keycard raised $38M (a16z) for agent identity tokens alone
- Akeyless launched SecretlessAI and Agentic Runtime Authority in 2025-2026
- 1Password launched Secure Agentic Autofill (October 2025)
- Bitwarden released open-source Agent Access SDK (2026)
- HashiCorp published validated patterns for AI agent identity with Vault
- AWS Bedrock AgentCore ships a native token vault
- Every major identity vendor (Okta, CyberArk, Descope) is adding agent features

**Window of opportunity:** 12-18 months before the market consolidates around 2-3 winners

---

## 2. Competitive Landscape

### 2.1 Direct Competitors (Agent-Native Identity)

| Competitor | Funding | Core Approach | Threat Level | Where Anima Wins |
|-----------|---------|--------------|--------------|------------------|
| **Keycard** | $38M (a16z) | Secure Token Service, ephemeral identity-bound tokens | **High** | Keycard is identity tokens only — no vault, no email, no phone, no browser autofill |
| **Astrix** | Undisclosed | NHI security + AI Agent Control Plane | Medium-High | Broader NHI focus, less deep on agent-specific vault |
| **Oasis** | Series B | Agentic Access Management | Medium | Governance-heavy, not developer-centric |

### 2.2 Agent Auth Platforms (Adjacent)

| Competitor | Funding | Core Approach | Threat Level | Where Anima Wins |
|-----------|---------|--------------|--------------|------------------|
| **Descope** | $88M | Agentic Identity Hub + MCP Auth | Medium-High | Auth-focused, no vault storage, no cross-channel identity |
| **Scalekit** | — | Token vault for agents | Medium | OAuth-only focus, narrow credential types |
| **Composio** | Series A | AgentAuth for 500+ apps | Medium | Tooling platform, not identity infrastructure |
| **Runlayer** | $11M | MCP Control Plane | Medium | Depends on 1Password for vault; no standalone secrets |
| **Natoma** | — | Enterprise MCP Gateway | Medium | Gateway adds latency; tied to 1Password |

### 2.3 Password Managers Pivoting to Agents

| Competitor | Approach | Threat Level | Where Anima Wins |
|-----------|---------|--------------|------------------|
| **1Password** | Secure Agentic Autofill (Browserbase) | **High** | Massive user base BUT not agent-native, browser autofill limited to Browserbase partnership, no cross-channel identity |
| **Bitwarden** | Open-source Agent Access SDK | Medium | Early alpha (27 GitHub stars), limited integrations |

### 2.4 Enterprise Incumbents

| Competitor | Approach | Threat Level | Where Anima Wins |
|-----------|---------|--------------|------------------|
| **HashiCorp Vault** | Dynamic secrets + validated AI agent patterns | Medium | Complex to operate, no native agent identity, enterprise-heavy |
| **Akeyless** | SecretlessAI + Agentic Runtime Authority | **High** | Most aggressive agent features BUT closed-source, vendor lock-in, no cross-channel |
| **CyberArk** | PAM for AI agents + MCP server | Medium | Heavy, expensive, not developer-friendly |
| **AWS AgentCore** | Native token vault in Bedrock | Medium | AWS lock-in, only works within Bedrock ecosystem |

### 2.5 Adjacent (Not Competitors, Potential Partners)

| Company | Why Relevant | Partnership Opportunity |
|---------|-------------|----------------------|
| **Teleport** | Secure MCP proxy, device attestation, SPIFFE | Infra access layer, complementary to vault |
| **Strata.io** | Identity orchestration for agents | Enterprise IAM bridge |
| **Onyx Security** | AI behavioral governance, Guardian Agent | Security monitoring layer |

### 2.6 Competitive Positioning Matrix

```
                    Agent-Specific ←──────────────→ General-Purpose
                         │                                │
    Identity-Complete    │  ★ ANIMA                       │
    (email+phone+vault)  │  (vault + identity +           │
                         │   all channels)                │
                         │                                │
                         │                                │
    Identity-Partial     │  Keycard (tokens only)         │  HashiCorp Vault
    (auth/tokens only)   │  Descope (auth only)           │  Akeyless
                         │  Scalekit (OAuth only)         │  CyberArk
                         │                                │
                         │                                │
    No Identity          │  1Password (vault only)        │  AWS Secrets Manager
    (vault/secrets only) │  Bitwarden (vault only)        │
                         │  Composio (tooling)            │
                         │                                │
```

**Anima's unique position:** Only platform combining vault + email + phone + browser autofill under one agent identity. Every competitor solves a subset.

---

## 3. Strategic Thesis

### 3.1 Core Thesis

The winning agent identity platform will be the one that **owns the full identity surface** — not just auth tokens or secrets, but the complete operational identity (email, phone, credentials). Vault is the final piece that completes this surface and creates the "Sign in with Anima" federation opportunity.

### 3.2 Why Vault Completes the Moat

| Without Vault | With Vault |
|---------------|------------|
| Email + phone = communication channels | Email + phone + vault = **complete agent identity** |
| Agents need external secrets manager | Agents get secrets management built-in |
| No cross-channel risk correlation | **Cross-channel analytics**: email + phone + vault anomaly detection |
| Agents manage their own credentials | Platform manages credentials, agents just use them |
| No federation opportunity | **"Sign in with Anima"** — become the identity provider for agents |

### 3.3 Revenue Impact

Vault adds three new revenue streams:

| Stream | Mechanism | Projected Impact |
|--------|-----------|-----------------|
| **Vault subscriptions** | Per-org vault access (included in Pro+Enterprise tiers) | Increases Pro/Enterprise conversion by reducing need for external vault |
| **Credential usage fees** | Per-credential-access metering above free tier | $0.001/access × millions of accesses = meaningful at scale |
| **Federation licensing** | "Sign in with Anima" per-authentication fee for external frameworks | Auth0 model: $0.05-0.10 per agent authentication |

### 3.4 Vault Pricing (Integrated into Existing Tiers)

| Feature | Free | Pro ($19/mo) | Enterprise ($99/mo) |
|---------|------|-------------|---------------------|
| Stored credentials | 10 | 500 | Unlimited |
| Credential accesses/month | 100 | 10,000 | Unlimited |
| Ephemeral tokens | 5 active | 100 active | Unlimited |
| Policies | 1 (default) | 10 | Unlimited |
| Credential sharing | No | Within org | Cross-org |
| Browser autofill | No | Yes | Yes |
| CLI injection | Yes | Yes | Yes |
| Cross-channel analytics | No | Basic risk score | Full analytics + anomaly alerts |
| Step-up authorization | No | Email only | Email + SMS + push |
| Audit retention | 7 days | 90 days | 1 year |
| Identity Federation | No | No | Yes |

---

## 4. Go-to-Market Strategy

### 4.1 Launch Messaging

**Primary:** "Your AI agent's vault. Secrets it can use but never see."

**Supporting messages:**
- "Credentials injected into CLI, browser, and API calls — the LLM never touches them"
- "One identity for email, phone, and secrets — cross-channel anomaly detection included"
- "Stop hardcoding API keys in your agent's config. Start using Anima Vault."

### 4.2 Launch Sequence

1. **Week 1-2:** Ship vault with feature flag ON. Blog post: "Introducing Anima Vault"
2. **Week 3-4:** Ship CLI injection (`am vault exec`). Blog post: "Your Agent's Secrets, Never in Context"
3. **Week 5-6:** Ship browser autofill. Blog post: "Agent Browser Automation Without Credential Exposure"
4. **Week 7-8:** Ship ephemeral tokens. Blog post: "Ephemeral Credentials for AI Agents"
5. **Week 9-10:** Ship cross-channel analytics. Blog post: "See Your Agent's Risk Score Across All Channels"
6. **Week 12+:** Ship identity federation. Blog post: "Sign in with Anima: Identity for Every Agent"

### 4.3 Competitive Content Plan

Priority comparison pages:
- Anima Vault vs 1Password for Agents
- Anima Vault vs HashiCorp Vault for AI
- Anima Vault vs Keycard (identity breadth + vault)
- Anima vs Akeyless (developer-first + cross-channel)
- Why vault-only solutions aren't enough for agent identity

### 4.4 Developer Distribution

- Update all 6 MCP servers with vault injection tools
- Update Node.js, Python, Go SDKs with vault client
- Update CLI with `am vault` commands
- Publish to MCP registries (Smithery, MCP Registry)
- Framework integration plugins (LangChain, CrewAI, Vercel AI)
- Example agents using vault (API integration, browser automation)

---

## 5. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Keycard wins agent identity market** | Medium | High | Ship vault + federation faster; emphasize cross-channel moat they can't replicate |
| **1Password dominates browser autofill** | Medium-High | Medium | Build native autofill in existing Chrome extension; don't depend on Browserbase |
| **Enterprise customers require Vault/Akeyless** | Medium | Medium | Offer Vault/Akeyless as alternative backends via provider abstraction |
| **Vaultwarden scaling limits** | Low-Medium | Medium | Provider interface is already abstracted; can swap to custom storage |
| **Browser extension review delays** | Medium | Low | Extension already exists; vault is incremental |
| **Credential breach / security incident** | Low | Critical | Per-agent encryption, audit trail, instant revocation, bug bounty program |

---

## 6. Success Metrics

### 6.1 Launch Metrics (Month 1-3)
- 500+ agents with provisioned vaults
- 10,000+ stored credentials
- 100+ orgs using vault
- Zero security incidents
- 50+ CLI injection users

### 6.2 Growth Metrics (Month 3-6)
- 5,000+ agents with vaults
- 100,000+ stored credentials
- 1,000+ orgs
- Browser autofill: 500+ active users
- Cross-channel analytics: measurable anomaly detection accuracy
- Pro/Enterprise conversion lift: 20%+ from vault inclusion

### 6.3 Platform Metrics (Month 6-12)
- Identity federation: 10+ external frameworks integrated
- "Sign in with Anima" authentications: 10,000+/month
- Vault revenue contribution: 15%+ of total platform revenue
- Cross-channel anomaly detection preventing 100+ credential abuse incidents

---

*Document created: April 5, 2026*
