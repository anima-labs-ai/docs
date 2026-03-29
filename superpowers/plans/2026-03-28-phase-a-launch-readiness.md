# Phase A — Launch Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Anima shippable as a competitive product — fix SDK packaging, wire console to real APIs, complete CLI, ship docs, add examples, ensure MCP/Skills parity.

**Architecture:** Monorepo at `/Users/diyanbogdanov/projects/agenticmail/` with main platform at `anima/` (Bun/Hono/Next.js/Prisma), SDKs at `python/` and `node/`, CLI at `cli/`, MCP at `mcp/`, Skills at `skill/`. All API operations defined via oRPC contracts at `anima/packages/contracts/src/contracts/`. Console uses `orpc.*` + `useSuspenseQuery` pattern.

**Tech Stack:** TypeScript, Python, Bun, Hono, Next.js 15, React 19, Prisma, oRPC, TanStack Query, Commander.js, MCP SDK

**Spec:** `docs/superpowers/specs/2026-03-28-anima-platform-roadmap-design.md`

---

## Task 1: Fix Python SDK README & Packaging (A1)

**Files:**
- Modify: `python/README.md`
- Modify: `python/pyproject.toml`
- Verify: `python/src/anima/__init__.py`
- Verify: `python/src/anima/py.typed`

- [ ] **Step 1: Read current Python SDK exports to document accurately**

Read `python/src/anima/__init__.py` and list all exported classes and functions. Read `python/src/anima/resources/` to catalog every resource module and its methods.

- [ ] **Step 2: Read current pyproject.toml and verify metadata**

Read `python/pyproject.toml`. Verify:
- `name` is set to a valid PyPI name (e.g., `anima-labs`)
- `description` is accurate
- `keywords` include: ai, agent, email, phone, cards, vault, identity
- `classifiers` include Python 3.9-3.13
- `urls` point to docs.useanima.sh and github
- `py.typed` is included in package data

- [ ] **Step 3: Update pyproject.toml metadata**

Update `python/pyproject.toml` with:
```toml
[project]
name = "anima-labs"
version = "0.1.0"
description = "Anima SDK for Python — unified agent identity infrastructure (email, phone, cards, vault)"
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
keywords = ["ai", "agent", "email", "phone", "cards", "vault", "identity", "mcp", "llm"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries",
]

[project.urls]
Homepage = "https://useanima.sh"
Documentation = "https://docs.useanima.sh"
Repository = "https://github.com/anima-labs/anima-python"
```

- [ ] **Step 4: Write comprehensive README.md**

Replace `python/README.md` with full documentation including:
- Installation: `pip install anima-labs`
- Quick start (create client, send email, create card)
- All 10 resources with method signatures
- Async usage example
- Webhook verification example
- Error handling example
- Link to full docs

The README should follow the pattern of well-known Python SDKs (stripe, openai) with clear sections.

- [ ] **Step 5: Verify package builds locally**

Run:
```bash
cd python && pip install -e ".[dev]" && python -c "from anima import Anima; print('OK')"
```
Expected: OK (no import errors)

- [ ] **Step 6: Commit**

```bash
git add python/README.md python/pyproject.toml
git commit -m "fix(python-sdk): update README and pyproject.toml metadata — SDK is fully implemented, not 'coming soon'"
```

---

## Task 2: Node SDK Audit & Parity (A6)

**Files:**
- Modify: `node/README.md`
- Verify: `node/src/index.ts`
- Verify: `node/src/resources/`
- Verify: `node/package.json`

- [ ] **Step 1: Create SDK parity matrix**

Read both SDKs and create a comparison:
- Read `python/src/anima/resources/` — list every method in every resource file
- Read `node/src/resources/` — list every method in every resource file
- Create markdown table comparing method-by-method

- [ ] **Step 2: Identify and fix gaps**

For any method that exists in Python but not Node (or vice versa), implement the missing method following the existing pattern in the target SDK.

- [ ] **Step 3: Verify error class consistency**

Compare:
- `python/src/anima/_exceptions.py` error classes
- `node/src/errors.ts` error classes
Ensure same set: APIError, AuthError, NotFoundError, RateLimitError, ValidationError

- [ ] **Step 4: Update Node README.md**

Update `node/README.md` to match Python SDK README quality:
- Installation: `npm install @anima-labs/sdk`
- Quick start with TypeScript examples
- All resources with method signatures
- Webhook verification example
- Error handling example

- [ ] **Step 5: Verify npm package.json is correct**

Check `node/package.json`:
- `name`: `@anima-labs/sdk`
- `description`: accurate
- `keywords`: ai, agent, email, phone, cards, vault, identity
- `types` field points to correct declaration file
- `exports` field is correct

- [ ] **Step 6: Commit**

```bash
git add node/
git commit -m "feat(node-sdk): audit parity with Python SDK, update README"
```

---

## Task 3: CLI Completeness Audit (A3)

**Files:**
- Modify: `cli/src/cli.ts`
- Create: `cli/src/commands/webhook/` (create.ts, list.ts, get.ts, delete.ts, test.ts, deliveries.ts)
- Create: `cli/src/commands/security/` (events.ts, scan.ts)
- Modify: `cli/README.md`

- [ ] **Step 1: Audit all 11 command groups**

Read every command file in `cli/src/commands/` and verify each is wired to the API client (not just a stub with placeholder output). List any commands that are scaffolded but not functional.

Groups to audit: admin, auth, card, config, email, extension, identity, init, phone, setup-mcp, vault

- [ ] **Step 2: Add webhook command group**

Create `cli/src/commands/webhook/` with commands following the existing pattern from `cli/src/commands/card/`:

Files to create:
- `cli/src/commands/webhook/index.ts` — register all subcommands
- `cli/src/commands/webhook/create.ts` — create webhook subscription
- `cli/src/commands/webhook/list.ts` — list webhooks
- `cli/src/commands/webhook/get.ts` — get webhook by ID
- `cli/src/commands/webhook/delete.ts` — delete webhook
- `cli/src/commands/webhook/test.ts` — send test event
- `cli/src/commands/webhook/deliveries.ts` — list delivery attempts

Register in `cli/src/cli.ts`:
```typescript
import { webhookCommands } from "./commands/webhook";
program.addCommand(webhookCommands());
```

- [ ] **Step 3: Add security command group**

Create `cli/src/commands/security/` with:
- `cli/src/commands/security/index.ts` — register subcommands
- `cli/src/commands/security/events.ts` — list security events
- `cli/src/commands/security/scan.ts` — scan content for PII/injection

Register in `cli/src/cli.ts`:
```typescript
import { securityCommands } from "./commands/security";
program.addCommand(securityCommands());
```

- [ ] **Step 4: Verify output formatting consistency**

Check that every command supports `--output json|table|yaml` via the shared output formatter at `cli/src/lib/output.ts`. Fix any commands that don't use it.

- [ ] **Step 5: Update CLI README**

Update `cli/README.md` with:
- Full command reference (all 11+ groups)
- Installation via npm and Homebrew
- Configuration (profiles, API URL override)
- Output formatting options
- Shell completion instructions

- [ ] **Step 6: Run CLI tests**

```bash
cd cli && bun test
```
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add cli/
git commit -m "feat(cli): add webhook and security commands, audit all command groups"
```

---

## Task 4: MCP Server Completeness (A7)

**Files:**
- Modify: `mcp/src/index.ts`
- Modify: `mcp/src/tools/` (various tool files)
- Modify: `mcp/package.json`
- Modify: `mcp/README.md`

- [ ] **Step 1: Create MCP tool coverage matrix**

Read all tool registration files in `mcp/src/tools/` and list every tool name.
Cross-reference against SDK methods from `node/src/resources/` and `python/src/anima/resources/`.
Identify any SDK operations that don't have MCP tools.

- [ ] **Step 2: Add missing MCP tools**

For each gap found in Step 1, add the tool following the registration pattern used in existing tool files. Each tool needs:
- Tool name (snake_case)
- Description (LLM-friendly, explains what it does and when to use it)
- Input schema (Zod)
- Handler function calling the API client

- [ ] **Step 3: Add selective tool loading (`--tools` flag)**

Modify `mcp/src/index.ts` to support `--tools` CLI flag:
```typescript
// Parse --tools flag
const toolsFilter = args.tools?.split(',').map(t => t.trim());

// In createConfiguredServer, conditionally register tool groups
if (!toolsFilter || toolsFilter.includes('email')) {
  registerEmailTools(context);
}
if (!toolsFilter || toolsFilter.includes('cards')) {
  registerCardTools(context);
}
// ... etc for each group
```

Usage: `npx @anima-labs/mcp --tools email,cards,vault`

- [ ] **Step 4: Review all tool descriptions for LLM-friendliness**

Read every tool description. Ensure each:
- Clearly states what the tool does in 1-2 sentences
- Lists required vs optional parameters
- Describes what the tool returns
- Includes usage hints (e.g., "Use this to send an email from an agent's inbox")

- [ ] **Step 5: Add Claude Desktop, Cursor, Windsurf config templates**

Add to `mcp/README.md`:

Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "anima": {
      "command": "npx",
      "args": ["-y", "@anima-labs/mcp"],
      "env": { "ANIMA_API_KEY": "ak_..." }
    }
  }
}
```

Cursor config (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "anima": {
      "command": "npx",
      "args": ["-y", "@anima-labs/mcp"],
      "env": { "ANIMA_API_KEY": "ak_..." }
    }
  }
}
```

- [ ] **Step 6: Update MCP README with full tool reference**

Update `mcp/README.md` with:
- Installation (npx, npm global, Homebrew)
- All tool categories with tool names and descriptions
- Selective loading documentation
- HTTP mode usage
- Config templates for all major clients

- [ ] **Step 7: Run MCP tests**

```bash
cd mcp && bun test
```
Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
git add mcp/
git commit -m "feat(mcp): add missing tools, selective loading, config templates"
```

---

## Task 5: Skills Completeness (A8)

**Files:**
- Modify: `skill/SKILL.md`
- Verify: `skills/` directory

- [ ] **Step 1: Audit skill coverage against MCP tools**

Read `skill/SKILL.md` and all files in `skills/`. Compare against MCP tool list from Task 4. Identify MCP tools/operations that aren't represented in skills.

- [ ] **Step 2: Update SKILL.md with complete tool reference**

Ensure SKILL.md documents all tool categories:
- Organization tools
- Agent tools
- Email tools
- Domain tools
- Phone tools
- Vault tools
- Card tools
- Message tools
- Webhook tools
- Security tools
- Funding tools
- Invoice tools
- Browser payment tools
- X402 tools

Each category should have a table with tool name, description, and key parameters.

- [ ] **Step 3: Add workflow recipes for unified operations**

Add skill recipes that demonstrate multi-service workflows:
- "Provision a complete agent identity" (create agent + inbox + phone + card + vault)
- "Send email with attachment" (upload attachment + send email)
- "Create card with spending policy" (create card + create policy + set auto-approve rules)

- [ ] **Step 4: Verify skill triggers work**

Test that the skill correctly activates on relevant natural language patterns in Claude Code.

- [ ] **Step 5: Commit**

```bash
git add skill/ skills/
git commit -m "feat(skills): complete skill coverage, add workflow recipes"
```

---

## Task 6: Wire Console Cards Pages (A2 — Part 1)

**Files:**
- Modify: `anima/apps/console/src/app/(dashboard)/cards/page.tsx`
- Modify: `anima/apps/console/src/app/(dashboard)/cards/[id]/page.tsx` (or create if doesn't exist)
- Reference: `anima/apps/console/src/app/(dashboard)/webhooks/page.tsx` (pattern)
- Reference: `anima/packages/contracts/src/contracts/cards.ts` (API contract)

- [ ] **Step 1: Read the reference webhook page pattern**

Read `anima/apps/console/src/app/(dashboard)/webhooks/page.tsx` completely. Note:
- How `orpc` client is imported
- How `useSuspenseQuery` is used for data fetching
- How `useMutation` is used for create/update/delete
- How loading, error, empty states are handled
- Component structure and UI patterns

- [ ] **Step 2: Read the cards contract**

Read `anima/packages/contracts/src/contracts/cards.ts` to understand available endpoints:
- `cards.list` — list all cards
- `cards.get` — get card by ID
- `cards.create` — create new card
- `cards.update` — update card
- `cards.delete` — delete card
- `cards.listTransactions` — list transactions for a card
- `cards.listPolicies` — list policies for a card
- `cards.listApprovals` — list pending approvals
- `cards.decideApproval` — approve/decline
- `cards.freeze` / `cards.unfreeze` — freeze/unfreeze card
- `cards.killSwitch` — emergency kill switch

- [ ] **Step 3: Read current cards page**

Read `anima/apps/console/src/app/(dashboard)/cards/page.tsx`. Identify what's mocked vs real.

- [ ] **Step 4: Wire cards list page to real API**

Replace mocked data with:
```typescript
const { data: cards } = useSuspenseQuery(
  orpc.cards.list.queryOptions({ input: { agentId } })
);
```

Wire create card dialog to `useMutation(orpc.cards.create.mutationOptions())`.
Wire delete action to `useMutation(orpc.cards.delete.mutationOptions())`.

- [ ] **Step 5: Wire card detail page**

Create or modify `cards/[id]/page.tsx` with:
- Card details: `useSuspenseQuery(orpc.cards.get.queryOptions({ input: { cardId } }))`
- Transactions tab: `useSuspenseQuery(orpc.cards.listTransactions.queryOptions({ input: { cardId } }))`
- Policies tab: `useSuspenseQuery(orpc.cards.listPolicies.queryOptions({ input: { cardId } }))`
- Approvals tab: `useSuspenseQuery(orpc.cards.listApprovals.queryOptions({ input: { cardId } }))`
- Freeze/unfreeze actions: `useMutation(orpc.cards.freeze.mutationOptions())`
- Kill switch action: `useMutation(orpc.cards.killSwitch.mutationOptions())`

- [ ] **Step 6: Test cards pages**

Run console dev server:
```bash
cd anima/apps/console && bun run dev
```
Navigate to cards pages, verify:
- List page shows real cards (or empty state if none)
- Create dialog works
- Detail page loads with tabs
- Freeze/unfreeze toggles correctly

- [ ] **Step 7: Commit**

```bash
git add anima/apps/console/src/app/\(dashboard\)/cards/
git commit -m "feat(console): wire cards pages to real API"
```

---

## Task 7: Wire Console Vault Pages (A2 — Part 2)

**Files:**
- Modify: `anima/apps/console/src/app/(dashboard)/vault/page.tsx`
- Modify/Create: `anima/apps/console/src/app/(dashboard)/vault/[agentId]/page.tsx`
- Reference: `anima/packages/contracts/src/contracts/vault.ts`

- [ ] **Step 1: Read vault contract**

Read `anima/packages/contracts/src/contracts/vault.ts` to understand available endpoints.

- [ ] **Step 2: Read current vault pages**

Read current vault page files, identify mocked vs real data.

- [ ] **Step 3: Wire vault list page**

Replace mocked data with real API calls for listing vault identities/credentials per agent.

- [ ] **Step 4: Wire vault detail page**

Wire credential CRUD operations:
- List credentials for an agent's vault
- View credential details
- Create new credential (login, secure_note, card, identity types)
- Update credential
- Delete credential
- Generate password

- [ ] **Step 5: Test vault pages**

Verify CRUD operations work against real API.

- [ ] **Step 6: Commit**

```bash
git add anima/apps/console/src/app/\(dashboard\)/vault/
git commit -m "feat(console): wire vault pages to real API"
```

---

## Task 8: Wire Console Phone Pages (A2 — Part 3)

**Files:**
- Modify: `anima/apps/console/src/app/(dashboard)/phone/page.tsx`
- Create: `anima/apps/console/src/app/(dashboard)/phone/[id]/page.tsx`
- Reference: `anima/packages/contracts/src/contracts/phone.ts`

- [ ] **Step 1: Read phone contract**

Read `anima/packages/contracts/src/contracts/phone.ts`.

- [ ] **Step 2: Read current phone page**

Identify mocked vs real data.

- [ ] **Step 3: Wire phone list page**

Wire to `phones.list` endpoint. Add phone provisioning dialog.

- [ ] **Step 4: Wire phone detail page**

Wire phone number detail with:
- Number info and status
- SMS/voice message history
- Configuration updates
- Release number action

- [ ] **Step 5: Test phone pages**

Verify list, provision, detail, and release work.

- [ ] **Step 6: Commit**

```bash
git add anima/apps/console/src/app/\(dashboard\)/phone/
git commit -m "feat(console): wire phone pages to real API"
```

---

## Task 9: Wire Console Messages/Email Pages (A2 — Part 4)

**Files:**
- Modify: `anima/apps/console/src/app/(dashboard)/messages/page.tsx`
- Create: `anima/apps/console/src/app/(dashboard)/messages/[id]/page.tsx`
- Reference: `anima/packages/contracts/src/contracts/message.ts`
- Reference: `anima/packages/contracts/src/contracts/email.ts`

- [ ] **Step 1: Read message and email contracts**

Read both contract files to understand available endpoints.

- [ ] **Step 2: Wire messages list page**

Wire to `messages.list` with:
- Inbox filtering
- Channel filtering (email, SMS)
- Direction filtering (inbound, outbound)
- Search functionality

- [ ] **Step 3: Wire message detail page**

Wire individual message view with:
- Full message content (HTML/text)
- Attachments list
- Thread view
- Reply/forward actions
- Mark as read/archive/spam actions

- [ ] **Step 4: Wire send email functionality**

Wire the compose/send email UI to the send email endpoint.

- [ ] **Step 5: Test message pages**

Verify list, detail, search, and send work.

- [ ] **Step 6: Commit**

```bash
git add anima/apps/console/src/app/\(dashboard\)/messages/
git commit -m "feat(console): wire messages/email pages to real API"
```

---

## Task 10: Wire Console Settings, Billing, Agents Pages (A2 — Part 5)

**Files:**
- Modify: `anima/apps/console/src/app/(dashboard)/settings/`
- Modify: `anima/apps/console/src/app/(dashboard)/billing/`
- Modify: `anima/apps/console/src/app/(dashboard)/agents/`

- [ ] **Step 1: Wire settings page**

Wire to `organizations.get` and `organizations.update` for:
- Organization name and metadata
- KYB status display
- Notification preferences

- [ ] **Step 2: Wire billing page**

Wire to billing/Stripe endpoints for:
- Current plan and tier
- Usage summary
- Payment method management
- Invoice history

- [ ] **Step 3: Wire agents pages**

Verify agents list and detail pages use real API:
- `agents.list` for list page
- `agents.get` for detail page with all associated resources (inboxes, phones, cards, vault)
- `agents.create`, `agents.update`, `agents.delete` for CRUD

- [ ] **Step 4: Test all wired pages**

Run console, navigate through all pages, verify no mocked data remains.

- [ ] **Step 5: Commit**

```bash
git add anima/apps/console/
git commit -m "feat(console): wire settings, billing, and agents pages to real API"
```

---

## Task 11: Documentation Site Setup (A4 — Part 1)

**Files:**
- Create: `docs/site/` (docs site project)
- Reference: `anima/docs/` (existing MDX content)

- [ ] **Step 1: Initialize docs site project**

Set up a documentation site using Fumadocs (Next.js-based, matches the existing stack):
```bash
cd docs && bunx create-fumadocs-app site
```

Or alternatively use Mintlify or Nextra if Fumadocs doesn't fit. The key requirement is MDX support and API reference generation.

- [ ] **Step 2: Migrate existing MDX content**

Copy and organize existing MDX files from `anima/docs/` into the docs site structure:
- `docs/site/content/getting-started.mdx`
- `docs/site/content/custom-domains.mdx`
- `docs/site/content/encryption.mdx`
- `docs/site/content/kyb.mdx`
- `docs/site/content/mcp.mdx`
- `docs/site/content/sdks.mdx`
- `docs/site/content/security.mdx`
- `docs/site/content/webhooks.mdx`
- `docs/site/content/faq.mdx`
- `docs/site/content/cards/` (card-specific docs)
- `docs/site/content/protocols/` (protocol docs)

- [ ] **Step 3: Add navigation structure**

Configure sidebar navigation:
- Getting Started
- Concepts (Agents, Organizations, Identity)
- Guides (Email, Phone, Cards, Vault, Webhooks, Domains)
- API Reference
- SDKs (TypeScript, Python, Go)
- MCP
- CLI
- Skills
- Integrations
- Security
- Protocols
- Changelog
- FAQ

- [ ] **Step 4: Verify docs site builds**

```bash
cd docs/site && bun run build
```
Expected: Build succeeds, site is navigable

- [ ] **Step 5: Commit**

```bash
git add docs/site/
git commit -m "feat(docs): initialize documentation site with migrated MDX content"
```

---

## Task 12: OpenAPI Spec & API Reference (A4 — Part 2)

**Files:**
- Create: `docs/openapi.json` (or `openapi.yaml`)
- Reference: `anima/packages/contracts/src/` (source of truth)

- [ ] **Step 1: Generate or write OpenAPI 3.1 spec**

Option A: Generate from oRPC contracts using oRPC's OpenAPI plugin if available.
Option B: Write manually based on contract files.

The spec must cover all endpoint groups:
- Organizations, Agents, Messages, Emails, Domains
- Cards, Phones, Vault, Webhooks, Security
- Funding, Invoice, Billing, API Keys

Each endpoint needs: path, method, request body schema, response schema, auth requirements, error codes.

- [ ] **Step 2: Validate OpenAPI spec**

```bash
npx @redocly/cli lint docs/openapi.json
```
Expected: No errors

- [ ] **Step 3: Add interactive API playground to docs site**

Integrate the OpenAPI spec with the docs site for interactive API reference:
- Try-it-now for each endpoint
- Code snippet generation (curl, Python, TypeScript)
- Authentication with user's API key

- [ ] **Step 4: Create llms.txt**

Create `docs/site/public/llms.txt` with a concise summary of Anima's API for LLM consumption:
```
# Anima API
> Unified agent identity infrastructure — email, phone, cards, vault

## API Base
https://api.useanima.sh/v1

## Authentication
Bearer token: `Authorization: Bearer ak_...`

## Resources
- Organizations: /v1/orgs
- Agents: /v1/agents
- Messages: /v1/messages (email, SMS)
- Cards: /v1/cards (virtual Visa/Mastercard)
- Phones: /v1/phones
- Vault: /v1/vault (credential storage)
- Webhooks: /v1/webhooks
- Domains: /v1/domains
- Security: /v1/security
```

- [ ] **Step 5: Commit**

```bash
git add docs/
git commit -m "feat(docs): add OpenAPI spec, API playground, and llms.txt"
```

---

## Task 13: SDK & Integration Quickstart Guides (A4 — Part 3)

**Files:**
- Create: `docs/site/content/quickstart-python.mdx`
- Create: `docs/site/content/quickstart-typescript.mdx`
- Create: `docs/site/content/quickstart-mcp.mdx`
- Create: `docs/site/content/quickstart-cli.mdx`
- Create: `docs/site/content/integrations/` (framework guides)

- [ ] **Step 1: Write Python quickstart**

"Send your first email in 5 minutes" guide:
```python
from anima import Anima

client = Anima(api_key="ak_...")
agent = client.agents.create(name="My Agent")
client.messages.send_email(
    agent_id=agent.id,
    to="user@example.com",
    subject="Hello from Anima",
    body="Sent by an AI agent!"
)
```

- [ ] **Step 2: Write TypeScript quickstart**

Same flow in TypeScript:
```typescript
import { Anima } from '@anima-labs/sdk';

const anima = new Anima({ apiKey: 'ak_...' });
const agent = await anima.agents.create({ name: 'My Agent' });
await anima.messages.sendEmail({
    agentId: agent.id,
    to: 'user@example.com',
    subject: 'Hello from Anima',
    body: 'Sent by an AI agent!'
});
```

- [ ] **Step 3: Write MCP quickstart**

"Connect Anima to Claude Desktop in 2 minutes" guide with config snippets.

- [ ] **Step 4: Write CLI quickstart**

"Manage agents from your terminal" guide:
```bash
am init
am identity create --name "My Agent"
am email send --agent <id> --to user@example.com --subject "Hello"
```

- [ ] **Step 5: Write integration guides**

Create guides for:
- LangChain integration
- OpenAI Agents SDK integration
- Vercel AI SDK integration

- [ ] **Step 6: Commit**

```bash
git add docs/site/content/
git commit -m "feat(docs): add quickstart guides and integration documentation"
```

---

## Task 14: Compelling Examples — E-Commerce Agent (A5 — Part 1)

**Files:**
- Create: `examples/ecommerce-agent/` (Python)
- Create: `examples/ecommerce-agent/main.py`
- Create: `examples/ecommerce-agent/requirements.txt`
- Create: `examples/ecommerce-agent/README.md`
- Create: `examples/ecommerce-agent/.env.example`

- [ ] **Step 1: Create example directory and requirements**

```
examples/ecommerce-agent/
  main.py
  requirements.txt
  README.md
  .env.example
```

requirements.txt:
```
anima-labs>=0.1.0
openai>=1.0.0
python-dotenv>=1.0.0
```

.env.example:
```
ANIMA_API_KEY=ak_...
OPENAI_API_KEY=sk-...
```

- [ ] **Step 2: Write the e-commerce agent**

`main.py` should demonstrate the unified platform:
1. Create agent with email inbox
2. Store merchant credentials in vault
3. Create a virtual card with spending policy ($100 limit, specific merchant)
4. Use OpenAI to simulate a purchasing decision
5. Process the "purchase" using the card
6. Send confirmation email with receipt
7. Clean up (freeze card after use)

- [ ] **Step 3: Write comprehensive README**

README.md with:
- What this example demonstrates
- Architecture diagram (text-based)
- Prerequisites
- Setup instructions
- How to run
- What to expect
- How it maps to real-world use cases

- [ ] **Step 4: Test the example runs**

```bash
cd examples/ecommerce-agent
pip install -r requirements.txt
python main.py
```
Expected: Runs without errors (may need real API key for full flow)

- [ ] **Step 5: Commit**

```bash
git add examples/ecommerce-agent/
git commit -m "feat(examples): add e-commerce purchasing agent demonstrating unified platform"
```

---

## Task 15: Compelling Examples — Customer Support Agent (A5 — Part 2)

**Files:**
- Create: `examples/customer-support-agent/` (TypeScript)
- Create: `examples/customer-support-agent/src/index.ts`
- Create: `examples/customer-support-agent/package.json`
- Create: `examples/customer-support-agent/README.md`
- Create: `examples/customer-support-agent/.env.example`

- [ ] **Step 1: Create example directory**

TypeScript example demonstrating multi-channel agent:
1. Agent receives inbound email with customer question
2. Agent uses vault to access CRM credentials
3. Agent looks up customer info
4. Agent sends SMS notification to customer that their issue is being handled
5. Agent composes and sends email reply
6. Agent logs interaction

- [ ] **Step 2: Write the agent implementation**

Use Vercel AI SDK or OpenAI for the AI layer. Demonstrate:
- Email receiving (via webhook simulation or polling)
- SMS sending
- Vault credential access
- Multi-channel response

- [ ] **Step 3: Write README**

Same quality as e-commerce example.

- [ ] **Step 4: Test**

```bash
cd examples/customer-support-agent && bun install && bun run start
```

- [ ] **Step 5: Commit**

```bash
git add examples/customer-support-agent/
git commit -m "feat(examples): add customer support agent with phone + email + vault"
```

---

## Task 16: Compelling Examples — Travel Booking Agent (A5 — Part 3)

**Files:**
- Create: `examples/travel-booking-agent/` (Python)

- [ ] **Step 1: Create travel booking agent**

Python example demonstrating the most comprehensive unified workflow:
1. Agent receives travel request via email
2. Agent uses vault credentials to access travel API
3. Agent creates virtual card with budget limit
4. Agent "books" flight/hotel using the card
5. Agent receives confirmation email
6. Agent sends SMS to user confirming booking
7. Agent freezes card after booking

- [ ] **Step 2: Write README with architecture diagram**

- [ ] **Step 3: Test**

- [ ] **Step 4: Commit**

```bash
git add examples/travel-booking-agent/
git commit -m "feat(examples): add travel booking agent demonstrating full agent lifecycle"
```

---

## Task 17: Update Existing Examples (A5 — Part 4)

**Files:**
- Modify: `examples/email-agent/`
- Modify: `examples/card-provisioning/`
- Modify: `examples/vercel-ai-agent/`
- Modify: `examples/openai-terminal/`

- [ ] **Step 1: Update each example**

For each existing example:
- Verify it uses the latest SDK version
- Add `.env.example` if missing
- Update README with consistent format
- Test that it runs

- [ ] **Step 2: Commit**

```bash
git add examples/
git commit -m "chore(examples): update existing examples to latest SDK, consistent format"
```

---

## Execution Order & Dependencies

```
Task 1 (Python SDK) ──────── no deps, start immediately
Task 2 (Node SDK) ─────────── no deps, start immediately
Task 3 (CLI) ──────────────── no deps, start immediately
Task 4 (MCP) ──────────────── no deps, start immediately
Task 5 (Skills) ───────────── after Task 4 (needs MCP tool list)
Task 6 (Console: Cards) ───── no deps
Task 7 (Console: Vault) ───── no deps
Task 8 (Console: Phone) ──── no deps
Task 9 (Console: Messages) ── no deps
Task 10 (Console: Settings) ─ no deps
Task 11 (Docs: Site) ──────── no deps
Task 12 (Docs: OpenAPI) ───── after Task 11
Task 13 (Docs: Guides) ────── after Task 11, Task 1, Task 2
Task 14 (Example: E-commerce) after Task 1 (needs Python SDK)
Task 15 (Example: Support) ── after Task 2 (needs Node SDK)
Task 16 (Example: Travel) ─── after Task 1 (needs Python SDK)
Task 17 (Examples: Update) ── after Task 1, Task 2
```

**Parallelizable groups:**
- Group 1 (immediate): Tasks 1, 2, 3, 4, 6, 7, 8, 9, 10, 11
- Group 2 (after Group 1): Tasks 5, 12, 13, 14, 15, 16, 17
