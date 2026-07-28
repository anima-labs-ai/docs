# Phone and Voice Docs Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update Anima's Mintlify-served docs and installable skill so the phone path feels demo-ready, the voice flow explains first-call behavior, mail/vault remain visible, and public MCP claims say 53 tools.

**Architecture:** Treat Mintlify docs and the installable Claude skill as separate surfaces. Docs explain capability depth for humans and LLM crawlers; `SKILL.md` gives agents a compact, executable first-run path with SMS as the reliable demo and voice as the conditional follow-up.

**Tech Stack:** Mintlify MDX content, local `meta.json` navigation, Claude skill Markdown, Bun/Vitest skill tests, shell verification with `rg` and `curl`.

---

### Task 1: Confirm Live Docs Source

**Files:**
- Read: `/Users/diyanbogdanov/projects/anima/docs/docs/phone.mdx`
- Read: `/Users/diyanbogdanov/projects/anima/docs/docs/mcp.mdx`
- Read: live `https://docs.useanima.sh/llms-full.txt`

- [ ] **Step 1: Verify served copy appears locally**

Run:

```bash
curl -s https://docs.useanima.sh/llms-full.txt | rg "77\\+ tools|Provision phone numbers and send SMS"
rg -n "77\\+ tools|Provision phone numbers and send SMS" docs
```

Expected: live and local content both contain the stale MCP count and current phone summary.

### Task 2: Rewrite Phone Docs as Phone and Voice Hub

**Files:**
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/phone.mdx`

- [ ] **Step 1: Replace thin phone copy with a complete flow**

Update the page to cover:

- What an agent phone identity is.
- Search and provision a number.
- Send the "text me now" demo SMS.
- Receive inbound SMS through webhooks.
- Make a first outbound voice call when voice is enabled.
- Explain voice modes, transcripts, recordings, and call events at a high level.
- Keep email/vault/DID framing so phone is part of one agent identity, not a point product.

### Task 3: Tighten Voice Quickstart Around First Call Demo

**Files:**
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/quickstart-voice.mdx`

- [ ] **Step 1: Make SMS the reliable preflight and voice the follow-up**

Update the quickstart so the first-run sequence is:

1. Create or choose an agent.
2. Provision a phone number with `voice` and `sms`.
3. Send the human an SMS from the agent.
4. Place an outbound call with a short greeting and system prompt.
5. Poll or stream status/transcript after the call.
6. Register webhooks for inbound calls.

### Task 4: Correct Public MCP Tool Count

**Files:**
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/mcp.mdx`
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/blog/introducing-anima.mdx`
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/blog/anima-vs-agentmail.mdx`
- Modify: `/Users/diyanbogdanov/projects/anima/docs/docs/index.mdx` if present locally or through generated source.

- [ ] **Step 1: Replace stale counts**

Run:

```bash
rg -n "77\\+|130\\+|133\\+|160\\+" docs
```

Expected: public docs stale counts are replaced with `53 tools`.

### Task 5: Strengthen Installable Skill First-Run Path

**Files:**
- Modify: `/Users/diyanbogdanov/projects/anima/skill/SKILL.md`
- Test: `/Users/diyanbogdanov/projects/anima/skill/__tests__/skill.test.ts`

- [ ] **Step 1: Update the skill flow**

Rewrite the core identity flow so agents:

- Prefer MCP, fall back to CLI.
- Create or confirm an identity.
- Send an email to the human.
- Provision a phone number and send a "text me now" SMS.
- Attempt a voice call only when voice is available.
- Provision vault and store secrets only after explicit human intent.

- [ ] **Step 2: Update tests if copy assertions require it**

Run:

```bash
bun test
```

Expected: skill tests pass and still assert mail, phone, voice, vault, and MCP coverage.

### Task 6: Verification

**Files:**
- Verify: `/Users/diyanbogdanov/projects/anima/docs`
- Verify: `/Users/diyanbogdanov/projects/anima/skill`

- [ ] **Step 1: Search for stale public claims**

Run:

```bash
rg -n "77\\+|130\\+|133\\+|160\\+" /Users/diyanbogdanov/projects/anima/docs/docs /Users/diyanbogdanov/projects/anima/skill
```

Expected: no stale public-facing tool-count claims remain.

- [ ] **Step 2: Run docs/skill validation available in each repo**

Run:

```bash
cd /Users/diyanbogdanov/projects/anima/skill && bun test
cd /Users/diyanbogdanov/projects/anima/docs && rg -n "53 tools|text me now|first call" docs
```

Expected: tests pass; updated copy is present in docs.
