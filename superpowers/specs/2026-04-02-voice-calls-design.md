# Anima Voice Calls — Complete Design Specification

**Date:** 2026-04-02
**Author:** Diyan Bogdanov + Claude
**Status:** Draft
**Scope:** Business plan, technical design, and implementation plan for adding programmable voice calls to the Anima platform

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Plan](#2-business-plan)
3. [Technical Design](#3-technical-design)
4. [Implementation Plan](#4-implementation-plan)

---

## 1. Executive Summary

Anima is the only unified agent identity infrastructure platform combining email, phone (SMS), credential vault, and agent identity. Adding programmable voice calls closes the last major communication gap — agents that can already email and text will now be able to call and be called.

**What we're building:** A two-tier voice call system where AI agents send and receive phone calls using a text-in/text-out WebSocket interface. The agent never touches audio — Anima handles all speech-to-text (STT) and text-to-speech (TTS) conversion.

**Two tiers:**
- **Basic** (~$0.034/min) — Telnyx native STT/TTS, ~1-3s latency. Good for notifications, simple calls.
- **Premium** (~$0.077/min) — Deepgram Nova-3 STT + ElevenLabs TTS via WebSocket audio streaming. ~500ms-1s latency, natural voices.

**Beyond calls:** Voice calls generate rich data. We'll build call intelligence features — recording, transcription, RAG search, scoring, vulnerability detection, and summarization — that make every call a searchable, scorable, auditable asset.

**Competitive edge:** No competitor offers voice calls + email + SMS + vault under one platform. AgentPhone does voice-only. Bland AI, Vapi, and Retell are voice-only platforms. Anima is the unified play, and adding voice is the piece that completes the communication stack.

**Additional scope:** Remove all Twilio code from the phone package (Telnyx-only going forward).

---

## 2. Business Plan

### 2.1. Market Landscape

#### Direct Competitors (Voice for AI Agents)

| Company | Type | Target | Price/min | SDKs | MCP | Call Intelligence |
|---------|------|--------|-----------|------|-----|-------------------|
| **AgentPhone** | Developer platform | Developers | Undisclosed (usage-based) | Python, TS | Yes (26 tools) | Basic (recording, transcripts) |
| **Vapi** | Developer platform | Developers | $0.07-0.15 | Python, Node, React | No | Logs, recordings, transcripts |
| **Retell AI** | Developer platform | Dev + Biz | $0.07-0.15 | Python, Node, React | No | Recordings, transcripts, extraction |
| **Bland AI** | Managed platform | Enterprise | ~$0.09 | Node, Python | No | Recordings, summaries, sentiment |
| **Twilio Voice** | Telecom + AI | Dev + Enterprise | $0.05-0.15 | 7 languages | No | Voice Intelligence (PII, sentiment) |

#### Adjacent Competitors (Infrastructure)

| Company | Type | Notes |
|---------|------|-------|
| **LiveKit** | OSS real-time infra | Agents Framework, WebRTC, SIP telephony |
| **Daily/Pipecat** | OSS voice AI framework | Best OSS pipeline, modular, growing |
| **Vocode** | OSS framework | Development slowed, good for prototyping |
| **ElevenLabs** | TTS + Conversational AI | Premium voices, expanding to full agent |
| **Deepgram** | STT/TTS + Voice Agent API | Lowest latency STT, expanding scope |

#### Non-Competitors (Different Segment)

| Company | Why Not Competing |
|---------|-------------------|
| **Synthflow, Thoughtly** | No-code builders for SMBs, not developer platforms |
| **Air AI, PolyAI** | Managed services / "AI employees", not infrastructure |
| **Hamming AI** | Testing platform for voice agents, complementary |

### 2.2. Competitive Positioning

**Anima's unique position: the only unified agent infrastructure platform.**

Every competitor solves one slice:
- AgentPhone = phone (SMS + voice)
- Vapi/Retell/Bland = voice only
- Agentmail = email only

Anima offers: Email + SMS + Voice + Credential Vault + Agent Identity + Compliance — all under one API key, one SDK, one MCP server.

**Voice-specific differentiators we will build:**

1. **MCP-native voice calls** — AgentPhone has MCP, but no one else does. We already have 350+ MCP tools. Adding voice MCP tools extends our lead.
2. **Two-tier pricing** — No competitor offers tiered voice quality. Vapi lets you pick providers but doesn't package it as tiers. Our Basic/Premium model is simpler for developers and enables price discrimination.
3. **Call intelligence built-in** — Most competitors offer recordings + transcripts and stop there. We'll offer RAG search, scoring, vulnerability detection, auto-summarization, and compliance scanning. This is what enterprises pay for.
4. **Cross-channel intelligence** — A voice call can reference an email thread. No competitor can connect these dots because they only have one channel.
5. **Agent-scoped security** — PII leakage detection, prompt injection via voice, social engineering detection. No voice platform does this today. It's the #1 enterprise concern for AI agent adoption.

### 2.3. Target Customers

**Primary:** Developers building AI agents that need to communicate across multiple channels.

**Use cases:**
- **Customer support agents** — receive inbound calls, resolve issues, escalate to humans when needed
- **Sales agents** — make outbound calls, qualify leads, book meetings
- **Operations agents** — appointment reminders, order confirmations, delivery updates
- **Operations agents** — fraud alerts, account notifications, scheduling reminders
- **Multi-channel agents** — follow up an email with a phone call

### 2.4. Pricing Strategy

#### Voice Call Pricing

| Component | Basic Tier | Premium Tier |
|-----------|-----------|--------------|
| **Base call rate** | $0.006/min (Telnyx) | $0.006/min (Telnyx) |
| **STT** | $0.025/min (Telnyx native) | $0.0077/min (Deepgram Nova-3) |
| **TTS** | $0.003/min (Telnyx native) | $0.06/min (ElevenLabs Flash) |
| **Streaming fee** | — | $0.0035/min (Telnyx WebSocket) |
| **Our cost** | **$0.034/min** | **$0.077/min** |
| **Our price** | **$0.07/min** | **$0.15/min** |
| **Gross margin** | **51%** | **49%** |

**Rationale:** Pricing at $0.07 and $0.15/min puts us in line with Vapi ($0.07-0.15) and Retell ($0.07-0.15), while our cost structure is competitive. The two-tier model gives us price anchoring — Premium looks like a deal compared to Bland ($0.09/min with worse latency), and Basic undercuts everyone for simple use cases.

#### Tier Limits

| Feature | Free | Developer ($29/mo) | Growth ($99/mo) | Scale ($249/mo) | Enterprise |
|---------|------|---------------------|------------------|-----------------|------------|
| Voice minutes (Basic) | 10 min | 500 min | 5,000 min | 25,000 min | Unlimited |
| Voice minutes (Premium) | 0 min | 200 min | 2,000 min | 10,000 min | Unlimited |
| Concurrent calls | 1 | 5 | 25 | 100 | Custom |
| Call recording | 7-day retention | 30-day retention | 90-day retention | 1-year retention | Custom |
| Call intelligence | Transcription only | + Summarization | + Scoring, RAG search | + Vulnerability detection | + Compliance scanning |
| Voice catalog | Telnyx native voices | + AWS Polly | + ElevenLabs, Azure | All voices | + Custom voice cloning |

#### Call Intelligence Add-Ons (Growth + Enterprise)

| Feature | Price |
|---------|-------|
| RAG search across calls | Included in Growth+ |
| Call scoring & analytics | Included in Growth+ |
| Auto-summarization | Included in Starter+ |
| Vulnerability scanning | Enterprise only |
| Compliance audit reports | Enterprise only |
| Custom retention policies | Enterprise only |

### 2.5. Revenue Model

**Assumptions (Year 1):**
- 500 developers on Free tier (Basic only, 10 min/mo limit, avg 5 min usage) = 2,500 min/mo
- 200 Developer customers (300 min/mo avg) = 60,000 min/mo
- 50 Growth customers (3,000 min/mo avg) = 150,000 min/mo
- 10 Scale customers (15,000 min/mo avg) = 150,000 min/mo
- 5 Enterprise customers (50,000 min/mo avg) = 250,000 min/mo
- 60% Basic / 40% Premium split

**Monthly revenue projection:**

| Source | Monthly Revenue |
|--------|----------------|
| Developer subscriptions (200 x $29) | $5,800 |
| Growth subscriptions (50 x $99) | $4,950 |
| Scale subscriptions (10 x $249) | $2,490 |
| Enterprise subscriptions (5 x $500 avg) | $2,500 |
| Basic voice usage (366,000 paid min x $0.07) | $25,620 |
| Premium voice usage (244,000 paid min x $0.15) | $36,600 |
| **Total monthly** | **$77,960** |
| **Total annual** | **$935,520** |

*Note: Free tier minutes (5,000/mo) excluded from paid usage calculation.*

**Monthly cost projection:**

| Source | Monthly Cost |
|--------|-------------|
| Basic voice (366,000 min x $0.034) | $12,444 |
| Premium voice (244,000 min x $0.077) | $18,788 |
| Infrastructure (servers, storage, DBs) | $3,000 |
| **Total monthly cost** | **$34,232** |
| **Gross margin** | **56%** |

*Note: This is voice revenue only. Anima's total revenue includes email, SMS, and vault usage across the same customer base.*

### 2.6. Go-to-Market

**Phase 1 (Month 1-2): Developer Preview**
- Ship Basic tier with core voice calling
- Blog post: "Give Your AI Agent a Phone — Email, SMS, and Now Voice"
- SDK examples: customer support agent, appointment scheduler
- Free tier with 30 min/month to drive adoption

**Phase 2 (Month 2-3): Premium Launch**
- Ship Premium tier with Deepgram + ElevenLabs
- Launch call intelligence (transcription, summarization, search)
- Case study with early adopters
- Comparison page: Anima vs AgentPhone vs Vapi

**Phase 3 (Month 3-6): Enterprise Push**
- Ship vulnerability detection, compliance scanning
- SOC 2 compliance positioning
- Enterprise sales outreach
- Partner integrations (LangChain, CrewAI, AutoGen)

---

## 3. Technical Design

### 3.1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                               │
│  SDK (Node/Python/Go)  │  MCP Server  │  CLI  │  Direct WS     │
└──────────────┬──────────┴──────────────┴───────┴────────────────┘
               │ WebSocket (text only)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ANIMA API SERVER                            │
│                                                                  │
│  ┌────────────────┐  ┌──────────────────────────────────────┐   │
│  │  Voice Router   │  │       Voice Call Manager              │   │
│  │  /ws/voice      │  │                                      │   │
│  │  REST endpoints │  │  ┌────────────┐  ┌────────────────┐ │   │
│  └────────┬───────┘  │  │   Basic     │  │    Premium     │ │   │
│           │          │  │  Pipeline   │  │    Pipeline    │ │   │
│           │          │  │ (Telnyx     │  │ (Deepgram +    │ │   │
│           └──────────│  │  native)    │  │  ElevenLabs +  │ │   │
│                      │  │             │  │  Telnyx stream) │ │   │
│                      │  └──────┬──────┘  └───────┬────────┘ │   │
│                      └─────────┼─────────────────┼──────────┘   │
│                                │                 │               │
│  ┌─────────────────────────────┼─────────────────┼───────────┐  │
│  │           Call Intelligence Engine             │           │  │
│  │  Recording │ Transcription │ RAG │ Scoring │ Security     │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────┬──────────────────────┘
                       │                   │
           ┌───────────▼──────┐  ┌─────────▼──────────┐
           │     Telnyx       │  │  External Services  │
           │  Call Control    │  │  Deepgram (STT)     │
           │  REST + Webhooks │  │  ElevenLabs (TTS)   │
           │  + WS Streaming  │  │                     │
           └──────────────────┘  └─────────────────────┘
```

### 3.2. Component Design

#### 3.2.1. Voice Call Manager

The central orchestrator. Manages the lifecycle of all active calls.

**Location:** `anima/packages/phone/src/voice/call-manager.ts`

**Responsibilities:**
- Maintain a map of active `CallSession` objects
- Route agent WebSocket messages to the correct call session
- Route Telnyx webhooks to the correct call session
- Select and instantiate the correct pipeline (Basic or Premium) based on tier
- Enforce concurrency limits per tier
- Track call duration for billing

**Call Session:**

```typescript
interface CallSession {
  id: string;                    // Anima call ID (cuid)
  callControlId: string;         // Telnyx call control ID
  direction: "INBOUND" | "OUTBOUND";
  tier: "basic" | "premium";
  state: CallState;              // INITIATING | RINGING | ACTIVE | HOLD | ENDING | ENDED
  voice: VoiceConfig;            // Selected voice
  phoneIdentityId: string;       // Which Anima phone number is used
  from: string;                  // Caller number
  to: string;                    // Callee number
  pipeline: VoiceCallPipeline;   // Basic or Premium implementation
  agentWs: WebSocket | null;     // Agent's WebSocket connection
  startedAt: Date;
  answeredAt: Date | null;
  endedAt: Date | null;
  metadata: Record<string, unknown>;
  // Intelligence
  recordingEnabled: boolean;
  recordingUrl: string | null;
  transcriptSegments: TranscriptSegment[];
}

type CallState = "INITIATING" | "RINGING" | "ACTIVE" | "HOLD" | "ENDING" | "ENDED";
```

**State Machine:**

```
INITIATING ──→ RINGING ──→ ACTIVE ──→ ENDING ──→ ENDED
                  │            │
                  │            ├──→ HOLD ──→ ACTIVE
                  │            │
                  └── (timeout/reject) ──→ ENDED
```

#### 3.2.2. Voice Call Pipeline Interface

Both tiers implement this interface. The Call Manager interacts only through this abstraction.

```typescript
interface VoiceCallPipeline {
  readonly tier: "basic" | "premium";

  /** Initialize the pipeline for a call */
  start(callControlId: string, voice: VoiceConfig): Promise<void>;

  /** Register handler for transcribed speech */
  onTranscription(handler: (segment: TranscriptSegment) => void): void;

  /** Register handler for speech completion */
  onSpeakComplete(handler: (spokenText: string) => void): void;

  /** Register handler for interruption */
  onInterrupted(handler: (spokenUntil: string, newText: string) => void): void;

  /** Send text to be spoken to the caller */
  speak(text: string): Promise<void>;

  /** Cancel current speech */
  stopSpeaking(): Promise<void>;

  /** Tear down all connections */
  destroy(): Promise<void>;
}

interface TranscriptSegment {
  speaker: "caller" | "agent";
  text: string;
  isFinal: boolean;
  confidence: number;
  startTime: number;     // seconds from call start
  endTime: number;
}
```

#### 3.2.3. Basic Pipeline (Telnyx Native)

**Location:** `anima/packages/phone/src/voice/pipelines/basic.ts`

Uses Telnyx Call Control API exclusively. No external services.

**STT:** `POST /v2/calls/{id}/actions/transcription_start` with Telnyx in-house engine. Results arrive via `call.transcription` webhooks.

**TTS:** `POST /v2/calls/{id}/actions/speak` with Telnyx native voices (KokoroTTS), AWS Polly Neural, or Azure — all accessible through the same Telnyx `speak` API by specifying the voice parameter (e.g., `"AWS.Polly.Joanna-Neural"`, `"Telnyx.KokoroTTS.sarah"`). Completion notified via `call.speak.ended` webhook.

**Interruption:** When the caller speaks during active TTS, Telnyx automatically cancels the speech and sends a new `call.transcription` webhook. The pipeline detects the interruption by tracking whether a speak command was active.

**Sequence diagram (one turn):**

```
Agent          Anima (Basic)        Telnyx
  │                │                   │
  │─call.speak────→│                   │
  │                │──POST speak──────→│
  │                │                   │──(plays audio to caller)
  │                │                   │
  │                │←─call.speak.ended─│  (TTS finished)
  │←call.speakEnd──│                   │
  │                │                   │
  │                │                   │──(caller speaks)
  │                │←call.transcription│  (STT result)
  │←call.transcript│                   │
  │                │                   │
```

#### 3.2.4. Premium Pipeline (WebSocket Streaming)

**Location:** `anima/packages/phone/src/voice/pipelines/premium.ts`

Manages three concurrent WebSocket connections per call:

1. **Telnyx Audio Stream** — bidirectional raw audio (RTP frames as base64 JSON)
2. **Deepgram STT** — receives audio, returns text transcriptions
3. **ElevenLabs TTS** — receives text, returns audio chunks

**Audio flow:**

```
Caller speaks → Telnyx WS (audio frames)
                    ↓
              Anima routes audio
                    ↓
              Deepgram WS (audio → text)
                    ↓
              Anima receives transcription
                    ↓ (WebSocket to agent)
              Agent responds with text
                    ↓ (WebSocket from agent)
              ElevenLabs WS (text → audio chunks)
                    ↓
              Anima routes audio back
                    ↓
              Telnyx WS (audio frames → caller)
```

**Telnyx streaming setup:**
- After answering call: `POST /v2/calls/{id}/actions/streaming_start`
- Config: `{ stream_url: "wss://api.anima.com/ws/telnyx-audio/{callId}", codec: "PCMU", channels: "mono" }`
- Audio arrives as: `{ event: "media", media: { track: "inbound", payload: "<base64>", timestamp: "..." } }`
- Audio sent back as: `{ event: "media", media: { track: "outbound", payload: "<base64>" } }`

**Deepgram connection:**
- `wss://api.deepgram.com/v1/listen?model=nova-3&encoding=mulaw&sample_rate=8000&channels=1&interim_results=true&utterance_end_ms=1000`
- Auth: `Authorization: Token <DEEPGRAM_API_KEY>`
- Send: raw audio bytes (decoded from base64)
- Receive: `{ type: "Results", channel: { alternatives: [{ transcript: "..." }] }, is_final: true, speech_final: true }`

**ElevenLabs connection:**
- `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_flash_v2_5&output_format=ulaw_8000`
- Auth: `xi-api-key: <ELEVENLABS_API_KEY>`
- Send: `{ text: "Hello ", try_trigger_generation: true }` (chunk by sentence for streaming)
- Receive: `{ audio: "<base64>", isFinal: false }` (audio chunks to forward to Telnyx)

**Interruption handling (Premium):**
When new inbound audio arrives from Telnyx while ElevenLabs is streaming audio back:
1. Stop forwarding ElevenLabs audio to Telnyx
2. Send `{ text: "" }` to ElevenLabs to flush/cancel
3. Track what portion of the text was actually spoken (based on audio chunks sent)
4. Start forwarding new inbound audio to Deepgram
5. Send `call.interrupted` to agent with `spokenUntil` and `newTranscription`

#### 3.2.5. Agent WebSocket Protocol

**Endpoint:** `wss://api.anima.com/ws/voice`

**Authentication:** API key passed as header during WebSocket upgrade (preferred). Query parameter supported as fallback for environments that cannot set WebSocket headers (e.g., some browser WebSocket implementations), but discouraged as API keys in URLs may be logged.
- **Preferred:** `Authorization: Bearer <agent_api_key>` header during upgrade
- **Fallback:** `wss://api.anima.com/ws/voice?apiKey=<agent_api_key>`

**Connection scoping:** One WebSocket = one agent. Supports multiple concurrent calls on the same connection (multiplexed by `callId`).

**Message types — Agent → Anima:**

| Type | Fields | Description |
|------|--------|-------------|
| `call.create` | `requestId`, `to`, `tier?`, `voice?`, `greeting?` | Initiate outbound call |
| `call.accept` | `callId`, `tier?`, `voice?`, `greeting?` | Accept inbound call (tier/voice override optional) |
| `call.reject` | `callId`, `reason?` | Reject inbound call |
| `call.speak` | `callId`, `text` | Send text to be spoken |
| `call.speak.cancel` | `callId` | Cancel current speech |
| `call.hangup` | `callId`, `reason?` | End the call |
| `call.hold` | `callId`, `holdMusic?` | Place on hold |
| `call.resume` | `callId` | Resume from hold |
| `call.dtmf` | `callId`, `digits` | Send DTMF tones |
| `ping` | — | Keepalive |

**Message types — Anima → Agent:**

| Type | Fields | Description |
|------|--------|-------------|
| `call.incoming` | `callId`, `from`, `to`, `phoneIdentityId`, `defaultTier`, `defaultVoice` | Inbound call notification |
| `call.started` | `requestId`, `callId`, `from`, `to`, `tier`, `direction` | Call connected |
| `call.ringing` | `requestId`, `callId` | Outbound call ringing |
| `call.transcription` | `callId`, `text`, `isFinal`, `confidence` | Caller speech as text |
| `call.speak.started` | `callId`, `text` | TTS playback began |
| `call.speak.ended` | `callId`, `text` | TTS playback finished |
| `call.interrupted` | `callId`, `spokenUntil`, `newTranscription` | Caller interrupted agent |
| `call.ended` | `callId`, `reason`, `duration`, `tier`, `summary` | Call terminated |
| `call.error` | `callId?`, `requestId?`, `code`, `message` | Error |
| `pong` | — | Keepalive response |

**Inbound call timeout:** If agent doesn't `call.accept` or `call.reject` within 15 seconds (configurable on phone identity), Anima auto-rejects.

**Defaults:**
- `tier` defaults to `"basic"` if not specified
- `voice` defaults to the phone identity's configured `defaultVoice`, or `"telnyx:kokoro-sarah"` if none set
- `greeting` is optional — if provided, spoken immediately after call connects

### 3.2.6. WebSocket Reconnection Protocol

If the agent's WebSocket disconnects during an active call:

1. Active calls are kept alive for **30 seconds** (configurable via `VOICE_WS_RECONNECT_WINDOW_MS`).
2. During this window, Telnyx audio continues — the caller hears silence (or optional hold music).
3. The agent can reconnect to the same `/ws/voice` endpoint. Upon reconnection, Anima sends a `call.reconnected` message with the active `callId` and current state.
4. If the agent does not reconnect within the window, Anima plays a configurable message ("We're experiencing technical difficulties. Please call back.") and hangs up.
5. Reconnection is identified by the same API key — no session token needed since agent API keys map 1:1 to agents.

### 3.2.7. Outbound Number Selection

When the agent creates an outbound call via `call.create`, the `from` number is selected automatically:

1. If a `fromNumber` field is provided in `call.create`, use that (must be a provisioned number for this agent with voice capability).
2. Otherwise, use the agent's **primary** phone identity (`isPrimary: true`).
3. If no primary, use the first phone identity with `voice: true` in capabilities.
4. If no voice-capable number exists, return `call.error` with code `NO_VOICE_NUMBER`.

The `call.create` message optionally includes `fromNumber`:

```json
{
  "type": "call.create",
  "requestId": "req_abc123",
  "to": "+1234567890",
  "fromNumber": "+19876543210",
  "tier": "premium",
  "voice": "elevenlabs:rachel",
  "greeting": "Hello!"
}
```

### 3.2.8. REST vs WebSocket Call Creation

Two ways to initiate an outbound call:

- **`POST /voice/calls` (REST):** Creates the call and returns a `Call` object with `callId` and state `INITIATING`. The agent **must** also have a WebSocket connection open to `/ws/voice` to handle the real-time conversation (send `call.speak`, receive `call.transcription`). If no WebSocket is connected, the call will be answered but the agent won't receive transcriptions.

- **`call.create` (WebSocket):** Creates the call and handles the conversation on the same connection. Simpler — no need for a separate REST call.

SDKs use the WebSocket approach via `anima.calls.connect()`. The REST endpoint exists for cases where call initiation needs to be decoupled from the WebSocket lifecycle (e.g., triggering a call from a webhook handler that then hands off to a long-lived WebSocket process).

### 3.2.9. Rate Limiting

| Limit | Value | Scope |
|-------|-------|-------|
| `call.create` messages | 10/minute | Per agent |
| Concurrent active calls | Per tier (1/5/25/100/custom) | Per agent |
| Monthly voice minutes | Per tier | Per org |
| WebSocket connections | 3 per agent | Per agent |

Rate limit exceeded → `call.error` with code `RATE_LIMITED`.

### 3.2.10. Worker Failure Handling

All post-call BullMQ workers use the same retry strategy:

| Worker | Max Retries | Backoff | Dead Letter Queue |
|--------|-------------|---------|-------------------|
| `call-transcription` | 3 | Exponential (30s base, 2x) | Yes — manual review |
| `call-embedding` | 3 | Exponential (30s base, 2x) | Yes — retry after transcription fix |
| `call-summary` | 2 | Exponential (60s base, 2x) | Yes — non-critical, skip |
| `call-scoring` | 2 | Exponential (60s base, 2x) | Yes — non-critical, skip |
| `call-security` | 3 | Exponential (30s base, 2x) | Yes — alert on failure (security-critical) |

**Dependency chain:** `call-transcription` → triggers `call-embedding` + `call-summary` + `call-scoring` + `call-security` in parallel after completion. If transcription fails, downstream workers are never enqueued.

### 3.3. Voice Catalog

Agents need to choose voices. Each voice has a description readable by both humans and LLMs, so agents can programmatically select appropriate voices.

**Data model:**

```typescript
interface Voice {
  id: string;              // "telnyx:kokoro-sarah", "elevenlabs:rachel"
  provider: "telnyx" | "elevenlabs" | "aws-polly" | "azure";
  name: string;            // "Sarah"
  tier: "basic" | "premium"; // Which tier can use this voice
  gender: "female" | "male" | "neutral";
  language: string;        // "en-US"
  accent: string;          // "American", "British", "Australian"
  style: string;           // "warm", "professional", "energetic", "calm"
  ageRange: string;        // "young-adult", "middle-aged", "senior"
  description: string;     // Human + LLM readable description
  sampleUrl: string;       // URL to audio sample
  costTier: "included" | "standard" | "premium"; // Pricing impact
}
```

**Example voices:**

```json
[
  {
    "id": "telnyx:kokoro-sarah",
    "provider": "telnyx",
    "name": "Sarah",
    "tier": "basic",
    "gender": "female",
    "language": "en-US",
    "accent": "American",
    "style": "warm",
    "ageRange": "young-adult",
    "description": "A warm, friendly young American woman's voice. Clear and articulate with a natural, conversational tone. Best suited for customer support, appointment reminders, and general-purpose agent interactions. Sounds approachable and trustworthy.",
    "costTier": "included"
  },
  {
    "id": "elevenlabs:rachel",
    "provider": "elevenlabs",
    "name": "Rachel",
    "tier": "premium",
    "gender": "female",
    "language": "en-US",
    "accent": "American",
    "style": "professional",
    "ageRange": "middle-aged",
    "description": "A polished, professional American woman's voice with exceptional clarity and natural intonation. Conveys confidence and authority without being cold. Ideal for business calls, sales outreach, financial notifications, and any scenario where credibility matters. One of ElevenLabs' most popular and natural-sounding voices.",
    "costTier": "premium"
  },
  {
    "id": "telnyx:kokoro-james",
    "provider": "telnyx",
    "name": "James",
    "tier": "basic",
    "gender": "male",
    "language": "en-US",
    "accent": "American",
    "style": "professional",
    "ageRange": "middle-aged",
    "description": "A steady, professional American man's voice. Deep and reassuring with measured pacing. Well-suited for formal notifications, account alerts, and business communications where a serious, trustworthy tone is needed.",
    "costTier": "included"
  },
  {
    "id": "elevenlabs:adam",
    "provider": "elevenlabs",
    "name": "Adam",
    "tier": "premium",
    "gender": "male",
    "language": "en-US",
    "accent": "American",
    "style": "warm",
    "ageRange": "middle-aged",
    "description": "A deep, warm American man's voice with a rich, resonant quality. Sounds like a friendly expert — knowledgeable but not intimidating. Excellent for customer support escalations, technical explanations, and scenarios where the caller needs to feel heard and understood.",
    "costTier": "premium"
  },
  {
    "id": "aws-polly:joanna-neural",
    "provider": "aws-polly",
    "name": "Joanna",
    "tier": "basic",
    "gender": "female",
    "language": "en-US",
    "accent": "American",
    "style": "neutral",
    "ageRange": "young-adult",
    "description": "A clear, neutral American woman's voice from AWS Polly Neural. Reliable and consistent with good pronunciation of numbers, dates, and technical terms. Best for automated notifications, order confirmations, and high-volume outbound calls where consistency matters more than personality.",
    "costTier": "standard"
  }
]
```

**API endpoint:** `GET /voice/catalog` — returns all available voices, filterable by tier, gender, language, style.

**MCP tool:** `voice_list_voices` — returns voice catalog with descriptions so Claude/LLM agents can select voices programmatically.

### 3.4. Call Intelligence Engine

Voice calls generate rich data. The intelligence engine processes every call to extract value.

#### 3.4.1. Call Recording

**Architecture:**
- Telnyx supports call recording via `POST /v2/calls/{id}/actions/record_start`
- For Premium tier (WebSocket streaming), we also capture audio server-side as a backup
- Store recordings in tiered GCP Cloud Storage:
  - Hot (0-30 days): Standard — ~$0.020/GB/month
  - Warm (30-90 days): Nearline — ~$0.010/GB/month
  - Cold (90+ days): Coldline — ~$0.004/GB/month, or Archive — ~$0.0012/GB/month
- A 10-minute call in Opus 24kbps = ~1.8 MB
- At 100K calls/month (avg 5 min) = ~90 GB/month = ~$1.80/month storage

**Compliance:**
- Recording disclosure played at call start (configurable per phone identity)
- Consent tracking: log timestamp of disclosure + caller's continued participation
- GDPR: support right-to-erasure (delete specific recordings)
- PCI-DSS: auto-pause recording during payment card collection (detect DTMF or card number patterns)
- Configurable retention policies per tier
- Encryption at rest (AES-256) with per-org envelope encryption (already implemented in Anima)

**Database model:**

```prisma
model CallRecording {
  id              String   @id @default(cuid())
  callId          String   @unique @map("call_id")
  agentId         String   @map("agent_id")
  orgId           String   @map("org_id")
  storageUrl      String   @map("storage_url")    // GCS URL (gs://bucket/path)
  storageTier     String   @map("storage_tier")    // standard | nearline | coldline | archive
  durationSeconds Int      @map("duration_seconds")
  fileSizeBytes   Int      @map("file_size_bytes")
  codec           String   // opus | pcmu | wav
  consentType     String   @map("consent_type")    // one_party | two_party | explicit
  consentEvidence Json     @map("consent_evidence") // { timestamp, method, jurisdiction }
  retentionUntil  DateTime @map("retention_until")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")
  call            Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([agentId])
  @@index([orgId])
  @@index([retentionUntil])
  @@map("call_recordings")
}
```

#### 3.4.2. Transcription & RAG

**Real-time transcription** (during call):
- Basic: Telnyx `call.transcription` webhooks (already part of the pipeline)
- Premium: Deepgram streaming results (already part of the pipeline)
- All segments stored in `TranscriptSegment` with speaker, timestamps, confidence

**Post-call enhanced transcription:**
- After call ends, run batch transcription on the recording with highest-accuracy model
- Speaker diarization to cleanly separate agent vs. caller
- Replaces real-time segments for the stored record

**RAG pipeline:**
1. Chunk transcript by conversational turns (3-8 utterances per chunk, 1-2 overlap)
2. Generate embeddings using the same model as Message embeddings (768 dimensions) — enables cross-channel search
3. Store in pgvector alongside rich metadata: callId, agentId, timestamp range, speakers, auto-tags
4. Extract structured data via LLM: topics, questions, action items, decisions, entities
5. Embed structured extractions separately for high-precision retrieval

**Search:**
- **Full-text:** Postgres FTS over transcript text (keyword search)
- **Semantic:** pgvector similarity search (conceptual matches)
- **Time-coded:** Results include timestamp — UI can jump to the moment in the recording
- **Cross-channel:** Search can span calls + emails + SMS for a unified conversation history

**Database models:**

```prisma
enum CallDirection {
  INBOUND
  OUTBOUND
}

enum CallTier {
  BASIC
  PREMIUM
}

enum CallState {
  INITIATING
  RINGING
  ACTIVE
  HOLD
  ENDING
  ENDED
}

enum CallEndReason {
  CALLER_HANGUP
  AGENT_HANGUP
  ACCEPT_TIMEOUT
  ERROR
  NO_ANSWER
}

model Call {
  id              String        @id @default(cuid())
  agentId         String        @map("agent_id")
  orgId           String        @map("org_id")
  phoneIdentityId String        @map("phone_identity_id")
  direction       CallDirection
  tier            CallTier
  state           CallState
  from            String
  to              String
  voiceId         String        @map("voice_id")
  startedAt       DateTime      @map("started_at")
  answeredAt      DateTime?     @map("answered_at")
  endedAt         DateTime?     @map("ended_at")
  durationSeconds Int?          @map("duration_seconds")
  endReason       CallEndReason? @map("end_reason")
  metadata        Json          @default("{}")
  createdAt       DateTime      @default(now()) @map("created_at")
  updatedAt       DateTime      @updatedAt @map("updated_at")
  // Relations
  agent           Agent         @relation(fields: [agentId], references: [id])
  phoneIdentity   PhoneIdentity @relation(fields: [phoneIdentityId], references: [id])
  recording       CallRecording?
  summary         CallSummary?
  score           CallScore?
  securityScan    CallSecurityScan?
  segments        TranscriptSegment[]
  embeddings      CallEmbedding[]

  @@index([orgId])
  @@index([agentId])
  @@index([phoneIdentityId])
  @@index([state])
  @@index([startedAt])
  @@map("calls")
}

// Note: Add `calls Call[]` reverse relation to both `Agent` and `PhoneIdentity` models.

model TranscriptSegment {
  id          String   @id @default(cuid())
  callId      String   @map("call_id")
  orgId       String   @map("org_id")
  speaker     String   // caller | agent
  text        String
  startTime   Float    @map("start_time")   // seconds from call start
  endTime     Float    @map("end_time")
  confidence  Float
  isFinal     Boolean  @map("is_final")
  createdAt   DateTime @default(now()) @map("created_at")
  call        Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([orgId])
  @@map("transcript_segments")
}

model CallEmbedding {
  id          String   @id @default(cuid())
  callId      String   @map("call_id")
  orgId       String   @map("org_id")
  chunkType   String   @map("chunk_type")  // transcript | extraction
  chunkText   String   @map("chunk_text")
  startTime   Float?   @map("start_time")
  endTime     Float?   @map("end_time")
  embedding   Unsupported("vector(768)")
  metadata    Json     @default("{}")
  createdAt   DateTime @default(now()) @map("created_at")
  call        Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([orgId])
  @@map("call_embeddings")
}
```

**Embedding dimension note:** Uses `vector(768)` to match the existing `Message.embedding` column dimension. This enables cross-channel semantic search across emails, SMS, and call transcripts using the same embedding model and vector similarity queries. Both use the same embedding model configured for the org.

#### 3.4.3. Call Scoring

**Computed metrics per call:**

| Metric | How Computed | Applicable To |
|--------|-------------|---------------|
| Talk-to-listen ratio | Sum of agent speech time / caller speech time | All calls |
| Longest monologue | Max contiguous agent speech block | All calls |
| Interruption rate | Overlapping speech count / total utterances | All calls |
| Dead air | Silence gaps > 3s / total duration | All calls |
| Response latency | Average time between caller end and agent start | All calls |
| Resolution rate | LLM classification of outcome vs. intent | All calls |
| Sentiment trajectory | Per-utterance sentiment, compare first vs. last quarter | Growth+ |
| Containment rate | Calls fully handled by AI without human escalation | Growth+ |
| Compliance score | Required disclosures present? Script adherence? | Enterprise |
| Hallucination check | Agent claims verified against knowledge base | Enterprise |

**Composite score (0-100):**

```
Score = 0.25 * Resolution + 0.20 * Sentiment + 0.15 * Compliance
      + 0.15 * Efficiency + 0.15 * Engagement + 0.10 * Latency
```

Weights configurable per org.

**Database model:**

```prisma
model CallScore {
  id                 String   @id @default(cuid())
  callId             String   @unique @map("call_id")
  orgId              String   @map("org_id")
  compositeScore     Float    @map("composite_score")   // 0-100
  resolutionScore    Float    @map("resolution_score")
  sentimentScore     Float    @map("sentiment_score")
  complianceScore    Float    @map("compliance_score")
  efficiencyScore    Float    @map("efficiency_score")
  engagementScore    Float    @map("engagement_score")
  latencyScore       Float    @map("latency_score")
  metrics            Json     // Raw metric values
  scoredAt           DateTime @map("scored_at")
  call               Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([orgId])
  @@index([compositeScore])
  @@map("call_scores")
}
```

#### 3.4.4. Call Summarization

**Three-level summaries generated post-call:**

1. **One-liner** (< 20 words): For list views, notifications, webhook payloads
2. **Structured summary**: Topics, decisions, action items, open questions, next steps — for CRM integration
3. **Detailed narrative** (1-2 paragraphs): Full context — for audit and review

**Processing:**
- Use fast model (Claude Haiku or GPT-4o-mini) for one-liner and structured extraction
- Use larger model only for flagged calls (escalated, compliance-relevant, low-scoring)
- Cache summaries — immutable once generated

```prisma
model CallSummary {
  id             String   @id @default(cuid())
  callId         String   @unique @map("call_id")
  orgId          String   @map("org_id")
  oneLiner       String   @map("one_liner")
  topics         Json     // string[]
  actionItems    Json     @map("action_items")    // { text, owner, deadline? }[]
  decisions      Json     // string[]
  openQuestions  Json     @map("open_questions")   // string[]
  nextSteps      Json     @map("next_steps")       // string[]
  narrative      String?  // Detailed narrative (generated on-demand for non-critical calls)
  intent         String   // Why did the caller call?
  outcome        String   // resolved | unresolved | escalated | callback | sale
  generatedAt    DateTime @map("generated_at")
  call           Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([orgId])
  @@map("call_summaries")
}
```

#### 3.4.5. Vulnerability Detection & Security

**Real-time scanning (during call):**

| Threat | Detection Method | Response |
|--------|-----------------|----------|
| Prompt injection via voice | Classifier on each caller utterance | Canned safe response + flag |
| PII leakage by agent | NER on agent utterances (SSN, CC, DOB patterns) | Immediate alert + flag |
| Social engineering | Pattern scoring (authority claims, urgency, info pumping) | Flag for review |

**Post-call scanning:**

| Analysis | Method | Tier |
|----------|--------|------|
| Full PII audit | NER + regex over complete transcript | Enterprise |
| Compliance violations | Rules engine (required disclosures, prohibited claims) | Enterprise |
| Unauthorized data disclosure | Compare agent statements against access policy | Enterprise |
| Cross-call data exfiltration | Link calls by caller, detect cumulative info extraction | Enterprise |

**Database model:**

```prisma
model CallSecurityScan {
  id             String   @id @default(cuid())
  callId         String   @unique @map("call_id")
  orgId          String   @map("org_id")
  threats        Json     // { type, severity, utteranceIndex, description }[]
  piiDetected    Json     @map("pii_detected")  // { type, speaker, redacted }[]
  compliancePass Boolean  @map("compliance_pass")
  riskScore      Float    @map("risk_score")     // 0-100, higher = riskier
  scannedAt      DateTime @map("scanned_at")
  call           Call     @relation(fields: [callId], references: [id])

  @@index([callId])
  @@index([orgId])
  @@index([riskScore])
  @@map("call_security_scans")
}
```

### 3.5. Twilio Removal

Remove all Twilio code from the phone package. Telnyx-only going forward.

**Files to delete:**
- `anima/packages/phone/src/twilio.ts`
- `anima/packages/phone/src/__tests__/twilio.test.ts`

**Files to modify:**
- `anima/packages/phone/src/types.ts` — remove `"TWILIO"` from `PhoneProvider` union
- `anima/packages/phone/src/factory.ts` — remove Twilio branch, simplify to Telnyx-only
- `anima/apps/api/src/routes/phone-webhooks.ts` — remove Twilio webhook handler
- `anima/packages/db/prisma/schema.prisma` — remove `TWILIO` from `PhoneProvider` enum (migration needed)
- Environment configs — remove `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` references

**Migration:** Database migration to convert any existing `TWILIO` phone identities. Since this is pre-launch, a simple migration that deletes TWILIO records or errors if any exist is sufficient.

### 3.6. API Endpoints (REST)

In addition to the WebSocket, REST endpoints for call management and intelligence:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/voice/catalog` | Any | List available voices |
| GET | `/voice/calls` | Agent key | List calls for agent |
| GET | `/voice/calls/:id` | Agent key | Get call details |
| GET | `/voice/calls/:id/transcript` | Agent key | Get full transcript |
| GET | `/voice/calls/:id/recording` | Agent key | Get recording URL (signed, expiring) |
| GET | `/voice/calls/:id/summary` | Agent key | Get call summary |
| GET | `/voice/calls/:id/score` | Agent key | Get call score |
| GET | `/voice/calls/:id/security` | Agent key | Get security scan results |
| POST | `/voice/search` | Agent key | Semantic search across call transcripts |
| POST | `/api/webhooks/phone/telnyx` | Telnyx signature | Telnyx call control webhooks |

### 3.7. SDK Design

All three SDKs (Node, Python, Go) get a new `calls` resource plus `voices` resource.

**Node SDK:**

```typescript
// Voice catalog
const voices = await anima.voices.list({ tier: "premium", gender: "female" });

// Outbound call (REST — creates call, returns call object)
const call = await anima.calls.create({
  to: "+1234567890",
  tier: "premium",
  voice: "elevenlabs:rachel",
  greeting: "Hello! This is Sarah from Acme.",
});

// List calls
const calls = await anima.calls.list({ limit: 20 });

// Get call details
const call = await anima.calls.get("call_xyz789");

// Get transcript
const transcript = await anima.calls.getTranscript("call_xyz789");

// Get summary
const summary = await anima.calls.getSummary("call_xyz789");

// Get score
const score = await anima.calls.getScore("call_xyz789");

// Search across calls
const results = await anima.calls.search({ query: "pricing discussion", limit: 10 });

// WebSocket for real-time call handling
const ws = anima.calls.connect();  // Opens WebSocket to /ws/voice

ws.on("call.incoming", (call) => {
  ws.accept(call.callId, { tier: "premium", voice: "elevenlabs:rachel" });
});

ws.on("call.transcription", (msg) => {
  if (msg.isFinal) {
    const response = await myLLM.respond(msg.text);
    ws.speak(msg.callId, response);
  }
});

ws.on("call.interrupted", (msg) => {
  // Handle interruption
});

ws.on("call.ended", (msg) => {
  console.log(`Call ended: ${msg.reason}, duration: ${msg.duration}s`);
});
```

**Python SDK:**

```python
# Voice catalog
voices = anima.voices.list(tier="premium", gender="female")

# Outbound call
call = anima.calls.create(
    to="+1234567890",
    tier="premium",
    voice="elevenlabs:rachel",
    greeting="Hello! This is Sarah from Acme.",
)

# WebSocket for real-time handling
async with anima.calls.connect() as ws:
    async for message in ws:
        if message.type == "call.incoming":
            await ws.accept(message.call_id, tier="premium")
        elif message.type == "call.transcription" and message.is_final:
            response = await my_llm.respond(message.text)
            await ws.speak(message.call_id, response)
        elif message.type == "call.ended":
            print(f"Call ended: {message.reason}")

# Search calls
results = anima.calls.search(query="pricing discussion", limit=10)
```

**Go SDK:**

```go
// Voice catalog
voices, err := client.Voices.List(ctx, anima.ListVoicesParams{Tier: "premium"})

// Outbound call
call, err := client.Calls.Create(ctx, anima.CreateCallParams{
    To:       "+1234567890",
    Tier:     "premium",
    Voice:    "elevenlabs:rachel",
    Greeting: "Hello! This is Sarah from Acme.",
})

// WebSocket
ws, err := client.Calls.Connect(ctx)
for msg := range ws.Messages() {
    switch m := msg.(type) {
    case *anima.CallIncoming:
        ws.Accept(m.CallID, anima.AcceptCallParams{Tier: "premium"})
    case *anima.CallTranscription:
        if m.IsFinal {
            response := myLLM.Respond(m.Text)
            ws.Speak(m.CallID, response)
        }
    case *anima.CallEnded:
        log.Printf("Call ended: %s, duration: %ds", m.Reason, m.Duration)
    }
}
```

### 3.8. SDK Improvements

Adding voice is the right time to level up the SDKs across the board. Competitor analysis (Stripe, Retell, Twilio, Vapi, LiveKit) reveals patterns we should adopt.

#### 3.8.1. High-Priority SDK Improvements (Ship with Voice)

**1. Auto-Pagination Iterators (Node + Python)**

Go already has `ListIterator[T]`. Node and Python need equivalents.

```typescript
// Node — async iterator (Stripe pattern)
for await (const call of anima.calls.list({ limit: 100 })) {
  console.log(call.id);
}

// Python — sync + async iterators
for call in anima.calls.list(limit=100):
    print(call.id)

async for call in async_anima.calls.list(limit=100):
    print(call.id)
```

**2. Idempotency Keys**

Critical for financial operations (wallet) and now call creation. Prevents duplicate calls on retries.

```typescript
const call = await anima.calls.create(
  { to: "+1234567890", tier: "premium" },
  { idempotencyKey: "unique-call-request-123" }
);
```

SDK auto-generates idempotency keys on retries (UUID, like Stripe). Manual override for user-controlled deduplication.

**3. Retry Jitter**

Replace fixed `[1s, 2s, 4s]` delays with randomized backoff to prevent thundering herd:

```
delay = min(random(0, BASE_DELAY * 2^attempt), MAX_DELAY)
```

Also respect `Retry-After` headers from rate limit responses (already parsed but unused).

**4. Environment Variable Fallback**

```typescript
// Auto-detects ANIMA_API_KEY if no key passed
const anima = new Anima(); // reads process.env.ANIMA_API_KEY
```

Matches Stripe (`STRIPE_API_KEY`), Twilio (`TWILIO_ACCOUNT_SID`), Retell (`RETELL_API_KEY`).

**5. Per-Request Option Overrides (Retell pattern)**

```typescript
// Override timeout for a slow operation
const result = await anima.calls.getTranscript("call_123", {
  timeout: 60_000,
  maxRetries: 5,
});

// Python equivalent
result = anima.calls.get_transcript("call_123", request_options={"timeout": 60})
```

**6. Raw Response Access (Retell pattern)**

```typescript
const { data, response } = await anima.calls.get("call_123", { rawResponse: true });
console.log(response.status, response.headers.get("x-request-id"));
```

Invaluable for debugging production issues — expose status code, headers, request ID.

**7. Request/Response Event Emitters (Stripe pattern)**

```typescript
anima.on("request", (req) => logger.info("→", req.method, req.path));
anima.on("response", (res) => logger.info("←", res.status, res.duration));
```

Enables observability without wrapping every call.

**8. Debug Logging**

```bash
ANIMA_LOG=debug npx my-agent   # Logs all HTTP requests/responses
```

Matches `RETELL_LOG=debug`, `TWILIO_LOG_LEVEL=debug`.

#### 3.8.2. Medium-Priority SDK Improvements (Ship in V3/V4)

**9. Webhook Middleware**

```typescript
// Express one-liner (Twilio pattern)
app.post("/webhooks", anima.webhooks.middleware("whsec_..."), (req, res) => {
  const event = req.animaEvent;  // Verified and parsed
});
```

```python
# FastAPI
@app.post("/webhooks")
async def handle(event: WebhookEvent = Depends(anima.webhooks.fastapi_dependency("whsec_..."))):
    ...
```

**10. Test Mode / Mock Client**

```typescript
// Test mode — no real API calls, returns fixtures
const anima = new Anima({ apiKey: "sk_test_..." });

// Or explicit mock
import { MockAnima } from "@anima-labs/sdk/testing";
const anima = new MockAnima();
anima.calls.mock("create", { id: "call_mock_123", state: "ACTIVE" });
```

### 3.9. MCP Tools

New MCP tools for the voice module (in `@anima-labs/mcp-phone`):

| Tool | Description |
|------|-------------|
| `voice_catalog` | List available voices with descriptions, filterable by tier/gender/language/style |
| `voice_create_call` | Initiate an outbound call (returns call ID, requires WebSocket for real-time) |
| `voice_list_calls` | List past calls with filtering |
| `voice_get_call` | Get call details, state, duration |
| `voice_get_transcript` | Get full transcript of a completed call |
| `voice_get_recording` | Get signed recording URL |
| `voice_get_summary` | Get call summary (one-liner, structured, narrative) |
| `voice_get_score` | Get call quality score and metrics |
| `voice_search_calls` | Semantic search across call transcripts |
| `voice_get_security_scan` | Get security scan results for a call |

**Note:** Real-time call handling (speak, listen, interrupt) happens over WebSocket, not MCP tools. MCP tools cover call initiation, history, and intelligence. An MCP client that wants real-time voice would use `voice_create_call` to start the call and then connect via WebSocket.

### 3.9. CLI Commands

New `voice` command group:

| Command | Description |
|---------|-------------|
| `anima voice catalog` | List available voices (table with name, tier, gender, style, description) |
| `anima voice call --to <number> [--tier basic\|premium] [--voice <id>] [--greeting <text>]` | Make outbound call (interactive terminal mode) |
| `anima voice calls` | List past calls |
| `anima voice calls:get <callId>` | Get call details |
| `anima voice calls:transcript <callId>` | Print call transcript |
| `anima voice calls:summary <callId>` | Print call summary |
| `anima voice calls:score <callId>` | Print call score |
| `anima voice calls:search <query>` | Search across call transcripts |

The interactive `anima voice call` command opens a terminal UI where the user can type responses that get spoken to the caller, and see the caller's speech as text. This is useful for testing and demos.

### 3.10. Webhook Events

New webhook events for voice calls:

| Event | Trigger | Payload |
|-------|---------|---------|
| `call.started` | Call answered (inbound or outbound) | callId, direction, from, to, tier |
| `call.ended` | Call terminated | callId, duration, reason, tier |
| `call.transcription` | Final transcription segment | callId, speaker, text, timestamp |
| `call.summary.ready` | Post-call summary generated | callId, oneLiner, topics, outcome |
| `call.score.ready` | Post-call scoring complete | callId, compositeScore, metrics |
| `call.security.alert` | Real-time security threat detected | callId, threatType, severity |
| `call.security.scan.ready` | Post-call security scan complete | callId, threats, riskScore |

These integrate with the existing webhook delivery system (BullMQ + Redis, exponential backoff, auto-disable after failures).

---

## 4. Implementation Plan

### 4.1. Phase Overview

| Phase | Name | Duration | Deliverables |
|-------|------|----------|-------------|
| **V1** | Foundation | 2 weeks | Twilio removal [✓], Call model [✓], Basic pipeline [✓], Telnyx Call Control [✓], Agent WebSocket [✓], SDK (Node) [✓], REST API [✓], E2E tests [✓] |
| **V2** | Premium + Catalog | 1.5 weeks | Premium pipeline (Deepgram + ElevenLabs), Voice catalog, All SDKs (`/node/`, `/python/`, `/go/`), MCP tools (`/mcp/`), CLI (`/cli/`), deprecate monorepo sdk-node |
| **V3** | Intelligence | 2 weeks | Recording, transcription, RAG search, summarization, scoring |
| **V4** | Security & Voice Polish | 1 week | Vulnerability detection, compliance scanning, CLI commands |
| **V5** | MCP Split + Hosting | 1.5 weeks | Break monolith MCP into domain servers, deploy hosted MCP on Cloud Run |
| **V6** | SDK Improvements | 1.5 weeks | Auto-pagination, idempotency, retry jitter, env vars, raw responses, middleware |
| **V7** | Docs, Examples & Launch | 1 week | Documentation, examples, final testing |

**Total: ~10.5 weeks**

### 4.2. Phase V1 — Foundation (2 weeks)

#### V1.1. Remove Twilio (Day 1-2) [✓]

**Tasks:**
1. [✓] Delete `anima/packages/phone/src/twilio.ts`
2. [✓] Delete `anima/packages/phone/src/__tests__/twilio.test.ts`
3. [✓] Remove `TWILIO` from `PhoneProvider` enum in Prisma schema
4. [✓] Create database migration
5. [✓] Simplify `factory.ts` to Telnyx-only (remove factory pattern, direct instantiation)
6. [✓] Remove Twilio webhook handler from `phone-webhooks.ts`
7. [✓] Remove `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` from all env configs
8. [✓] Update `types.ts` — remove Twilio-specific types
9. [✓] Run all existing phone tests, fix any breakage
10. [✓] Commit: "Remove Twilio provider — Telnyx-only going forward"

#### V1.2. Database Models (Day 2-3) [✓]

**Tasks:**
1. [✓] Add `Call` model to Prisma schema
2. [✓] Add `TranscriptSegment` model
3. [✓] Add `CallRecording` model (empty for now, populated in V3)
4. [✓] Add `CallSummary`, `CallScore`, `CallSecurityScan` models (empty, populated in V3/V4)
5. [✓] Add `CallEmbedding` model with pgvector column
6. [✓] Add `voiceTier` and `defaultVoice` fields to `PhoneIdentity`
7. [✓] Create and run migration
8. [✓] Add relations to existing `Agent` and `PhoneIdentity` models
9. [✓] Commit: "Add voice call database models"

#### V1.3. Voice Call Pipeline Interface + Basic Pipeline (Day 3-6) [✓]

**Tasks:**
1. [✓] Create `anima/packages/phone/src/voice/` directory structure
2. [✓] Implement `VoiceCallPipeline` interface
3. [✓] Implement `BasicPipeline` (start, speak, stopSpeaking, onTranscription, onSpeakComplete, onInterrupted, destroy)
4. [✓] Implement `CallSession` class with state machine
5. [✓] Implement `CallManager` — manages active sessions, routes webhooks
6. [✓] Write unit tests for Basic pipeline and Call Manager
7. [✓] Commit: "Implement Basic voice pipeline with Telnyx native STT/TTS"

#### V1.4. Telnyx Call Control Integration (Day 5-7) [✓]

**Tasks:**
1. [✓] Extend `telnyx.ts` provider with call control methods (answerCall, dialCall, hangupCall, startTranscription, stopTranscription, speak, stopSpeak, startStreaming, stopStreaming, sendDtmf, holdCall, unholdCall, startRecording, stopRecording)
2. [✓] Add new webhook event handlers in `phone-webhooks.ts` (call.initiated, call.answered, call.transcription, call.speak.ended, call.hangup)
3. Create a Telnyx Call Control Application (config/setup docs) — deferred
4. [✓] Write integration test with Telnyx sandbox (13 tests)
5. [✓] Commit: "Integrate Telnyx Call Control API for voice calls"

#### V1.5. Agent WebSocket Server (Day 7-10) [✓]

**Tasks:**
1. [✓] Create WebSocket endpoint at `/ws/voice` in Fastify (Bearer token auth + query param fallback)
2. [✓] Implement message routing (call.create, call.accept, call.reject, call.speak, call.speak.cancel, call.hangup, call.hold, call.resume, call.dtmf, ping)
3. [✓] Implement inbound call notification (webhook → session → agent WS, 15s auto-reject timeout)
4. [✓] Implement session events → agent messages (transcription, speak.ended, interrupted, ended)
5. [✓] Handle WebSocket disconnection gracefully (30s reconnect window, re-sends active call state)
6. [✓] Write WebSocket tests (31 tests — 24 message parsing + 7 state management)
7. [✓] Commit: "Implement agent-facing WebSocket server for voice calls"

#### V1.6. Node SDK — Calls Resource (Day 10-12) [✓]

> **Note:** V1.6 created a temporary `@anima/sdk-node` package inside the monorepo (`anima/packages/sdk-node/`).
> This will be migrated to the standalone Node SDK at `/node/` (`@anima-labs/sdk`) in V2.7.

**Tasks:**
1. [✓] Add `calls` resource to Node SDK (create, list, get, getTranscript REST + connect() WebSocket)
2. [✓] Add `voices` resource (list with tier/gender/language filtering)
3. [✓] Add TypeScript types for all WebSocket messages (re-exported from @anima/phone)
4. [✓] Write SDK tests (20 tests — client config, WS connection, message sending/receiving)
5. [✓] Commit: "Add calls and voices resources to Node SDK"

#### V1.7. REST API Endpoints (Day 11-13) [✓]

**Tasks:**
1. [✓] Create `anima/apps/api/src/routes/handlers/voice.ts`:
   - `GET /voice/catalog` — return voices, filterable
   - `GET /voice/calls` — list calls for agent
   - `GET /voice/calls/:id` — get call details
   - `POST /voice/calls` — create outbound call (alternative to WebSocket)
   - `GET /voice/calls/:id/transcript` — get transcript
2. [✓] Add Zod schemas in `anima/packages/contracts/src/schemas/voice.ts`
3. [✓] Register routes in router
4. Add tier limit enforcement (concurrent calls, monthly minutes)
5. Add usage tracking events: `call_started`, `call_ended`, `call_minute`
6. Write API tests
7. [✓] Commit: "Add voice REST API endpoints"

#### V1.8. End-to-End Test (Day 13-14) [✓]

**Tasks:**
1. [✓] Write E2E test: outbound call via Node SDK WebSocket
2. [✓] Write E2E test: inbound call simulation (mock Telnyx webhook)
3. [✓] Write E2E test: full conversation loop (speak → transcribe → respond)
4. [✓] Write E2E test: interruption handling
5. [✓] Write E2E test: call hangup from both sides
6. Manual testing with real phone number
7. [✓] Commit: "Add voice call E2E tests"

### 4.3. Phase V2 — Premium Pipeline (1.5 weeks)

#### V2.1. Premium Pipeline — Telnyx Audio Streaming (Day 1-2) [✓]

**Tasks:**
1. [✓] Implement Telnyx WebSocket audio stream handler:
   - Accept incoming WebSocket connection at `/ws/telnyx-audio/:callId`
   - Parse inbound audio frames (base64 PCMU → raw bytes)
   - Forward outbound audio frames (raw bytes → base64 PCMU)
   - Handle stream lifecycle events
2. [✓] Extend Telnyx provider: `startStreaming()` to tell Telnyx to stream to our WebSocket URL
3. [✓] Write tests for audio stream handling
4. [✓] Commit: "Implement Telnyx WebSocket audio streaming"

#### V2.2. Premium Pipeline — Deepgram STT Integration (Day 2-4) [✓]

**Tasks:**
1. [✓] Create `anima/packages/phone/src/voice/providers/deepgram.ts`:
   - Manage WebSocket connection to Deepgram Nova-3
   - Forward raw audio bytes from Telnyx stream
   - Parse streaming transcription results (interim + final)
   - Handle utterance end detection
   - Reconnection logic with exponential backoff
2. [✓] Add `DEEPGRAM_API_KEY` to environment config
3. [✓] Write tests with mock Deepgram WebSocket
4. [✓] Commit: "Integrate Deepgram Nova-3 streaming STT"

#### V2.3. Premium Pipeline — ElevenLabs TTS Integration (Day 4-6) [✓]

**Tasks:**
1. Create `anima/packages/phone/src/voice/providers/elevenlabs.ts`:
   - Manage WebSocket connection to ElevenLabs streaming API
   - Send text chunks (sentence-by-sentence for streaming)
   - Receive audio chunks, convert to PCMU format
   - Forward audio to Telnyx outbound stream
   - Handle flush/cancel for interruptions
2. Add `ELEVENLABS_API_KEY` to environment config
3. Implement audio format conversion (ElevenLabs ulaw_8000 → Telnyx PCMU)
4. Write tests with mock ElevenLabs WebSocket
5. Commit: "Integrate ElevenLabs streaming TTS"

#### V2.4. Premium Pipeline — Assembly & Interruption (Day 6-8) [✓]

**Tasks:**
1. Implement `PremiumPipeline` class combining all three WebSocket connections:
   - Telnyx audio in → Deepgram STT → text out
   - Text in → ElevenLabs TTS → Telnyx audio out
2. Implement interruption detection:
   - Track whether TTS audio is being sent to Telnyx
   - When new inbound speech detected during TTS playback:
     a. Stop forwarding ElevenLabs audio
     b. Flush ElevenLabs stream
     c. Calculate `spokenUntil` from bytes sent
     d. Let Deepgram process new speech
     e. Emit `interrupted` event
3. Implement Voice Activity Detection (VAD):
   - Detect when caller starts/stops speaking
   - Prevent false interruptions from background noise
4. Handle edge cases: simultaneous speak + transcription, rapid fire messages
5. Write comprehensive tests for Premium pipeline
6. Commit: "Implement Premium pipeline with interruption handling"

#### V2.5. Voice Catalog (Day 8-9) [✓]

**Tasks:**
1. Create voice catalog data file: `anima/packages/phone/src/voice/catalog.ts`
   - All Telnyx native voices with descriptions
   - All AWS Polly Neural voices with descriptions
   - All ElevenLabs pre-made voices with descriptions (at least 10-15 voices)
   - Each voice: id, provider, name, tier, gender, language, accent, style, ageRange, description
2. Implement `GET /voice/catalog` endpoint with filtering
3. Implement `voice_list_voices` MCP tool in **`/mcp/`** (`@anima-labs/mcp`)
4. Add `anima voice catalog` CLI command in **`/cli/`** (`@anima-labs/cli`)
5. Write tests
6. Commit: "Add voice catalog with descriptions"

#### V2.6. All SDKs — Calls & Voices Resources (Day 9-11) [✓]

> **Directory references:**
> - Node SDK: **`/node/`** (`@anima-labs/sdk`)
> - Python SDK: **`/python/`** (`anima-labs`)
> - Go SDK: **`/go/`** (`anima-go`)

**Tasks:**
1. Add `calls` and `voices` resources to Node SDK at **`/node/src/resources/`**
   - Port `CallsResource` and `VoicesResource` from monorepo `anima/packages/sdk-node/`
   - Adapt to standalone SDK patterns (HTTP client, error handling, auth)
   - Add WebSocket `connect()` method returning typed `VoiceConnection`
2. Add `calls` and `voices` resources to Python SDK at **`/python/src/anima/resources/`** (sync + async)
3. Add `calls` and `voices` resources to Go SDK at **`/go/`**
4. Add WebSocket `connect()` method to both Python and Go SDKs
5. Write SDK tests for all three
6. Commit: "Add calls and voices to Node, Python, and Go SDKs"

#### V2.7. Deprecate Monorepo sdk-node (Day 11) [✓]

> Housekeeping: remove the temporary `@anima/sdk-node` package from the monorepo
> now that the resources have been migrated to the standalone `/node/` SDK.

**Tasks:**
1. Remove `anima/packages/sdk-node/` directory
2. Remove `@anima/sdk-node` from monorepo workspace config
3. Verify no internal packages depend on `@anima/sdk-node`
4. Commit: "Remove temporary monorepo sdk-node (migrated to standalone @anima-labs/sdk)"

### 4.4. Phase V3 — Call Intelligence (2 weeks)

#### V3.1. Call Recording (Day 1-3) [✓]

**Tasks:**
1. Implement recording initiation:
   - Basic: Telnyx `record_start` API after call answered
   - Premium: capture audio frames server-side into buffer, write to file on call end
2. Implement recording storage:
   - Upload to S3 with per-org encryption
   - Create `CallRecording` record
   - Set retention based on tier
3. Implement recording consent:
   - Configurable disclosure message on PhoneIdentity
   - Play disclosure at call start before any conversation
   - Log consent timestamp
4. Implement `GET /voice/calls/:id/recording` — return signed S3 URL (expires in 1 hour)
5. Implement storage tier migration (cron job: hot → warm → cold based on age)
6. Write tests
7. Commit: "Add call recording with compliance-first architecture"

#### V3.2. Post-Call Transcription Pipeline (Day 3-5) [✓]

**Tasks:**
1. Create BullMQ worker: `call-transcription-worker.ts`
   - Triggered when call ends
   - Downloads recording
   - Runs batch transcription (Deepgram batch API for accuracy)
   - Speaker diarization
   - Replaces real-time segments with enhanced transcript
   - Stores final TranscriptSegment records
2. Implement structured extraction via LLM:
   - Topics discussed
   - Questions asked (and answers)
   - Action items (with owner if identifiable)
   - Decisions made
   - Entities mentioned (companies, products, people)
3. Store structured extractions as JSON on CallSummary
4. Write tests
5. Commit: "Add post-call transcription and structured extraction pipeline"

#### V3.3. RAG & Search (Day 5-8) [✓]

**Tasks:**
1. Create BullMQ worker: `call-embedding-worker.ts`
   - Triggered after transcription complete
   - Chunk transcript by conversational turns
   - Generate embeddings via `text-embedding-3-large`
   - Store in `CallEmbedding` table with pgvector
   - Also embed structured extractions separately
2. Implement `POST /voice/search`:
   - Hybrid search: pgvector similarity + Postgres FTS
   - Return results with callId, matched text, timestamp, relevance score
   - Filterable by date range, agent, outcome
3. Implement cross-channel search:
   - Extend existing message search to include call transcripts
   - Unified search endpoint that spans emails + SMS + calls
4. Write tests
5. Commit: "Add RAG search across voice call transcripts"

#### V3.4. Call Summarization (Day 8-10) [✓]

**Tasks:**
1. Create BullMQ worker: `call-summary-worker.ts`
   - Triggered after transcription complete
   - Generate one-liner via Haiku/GPT-4o-mini
   - Generate structured summary (topics, action items, decisions, etc.)
   - Classify intent and outcome
   - Generate detailed narrative only for flagged calls
2. Implement `GET /voice/calls/:id/summary`
3. Add `call.summary.ready` webhook event
4. Write tests
5. Commit: "Add auto-summarization for voice calls"

#### V3.5. Call Scoring (Day 10-14) [✓]

**Tasks:**
1. Create BullMQ worker: `call-scoring-worker.ts`
   - Triggered after transcription complete
   - Compute metrics: talk-to-listen ratio, monologue length, interruption rate, dead air, response latency
   - Compute resolution via LLM classification
   - Compute sentiment trajectory (per-utterance sentiment, compare quarters)
   - Calculate composite score with configurable weights
2. Implement `GET /voice/calls/:id/score`
3. Add `call.score.ready` webhook event
4. Build aggregate analytics queries:
   - Average score by agent, by time period
   - Score distribution
   - Trend over time
5. Write tests
6. Commit: "Add call quality scoring and analytics"

### 4.5. Phase V4 — Security & Voice Polish (1 week)

#### V4.1. Vulnerability Detection (Day 1-3) [✓]

**Tasks:**
1. Implement real-time scanning (during call):
   - PII leakage detector: NER + regex on agent utterances
   - Prompt injection classifier: keyword + pattern matching on caller utterances
   - Runs on every TranscriptSegment as it arrives
   - If threat detected: emit `call.security.alert` webhook, flag in session
2. Implement post-call scanning:
   - Create BullMQ worker: `call-security-worker.ts`
   - Full PII audit across complete transcript
   - Compliance rules engine (configurable required disclosures)
   - Social engineering pattern scoring
   - Cross-call exfiltration detection (link by caller number, detect patterns)
3. Implement `GET /voice/calls/:id/security`
4. Add `call.security.alert` and `call.security.scan.ready` webhook events
5. Write tests
6. Commit: "Add voice call vulnerability detection and security scanning"

#### V4.2. CLI Commands (Day 3-4) [✓]

> **Directory:** `/cli/` (`@anima-labs/cli`)

**Tasks:**
1. Add **`/cli/src/commands/voice/`** directory:
   - `catalog.ts` — list voices
   - `call.ts` — interactive outbound call (terminal UI)
   - `calls.ts` — list past calls
   - `get.ts` — get call details
   - `transcript.ts` — print transcript
   - `summary.ts` — print summary
   - `score.ts` — print score
   - `search.ts` — search call transcripts
2. Register in command index at `/cli/src/commands/index.ts`
3. Write CLI tests
4. Commit: "Add voice CLI commands"

#### V4.3. Webhook Events & Usage Tracking (Day 4-5) [✓]

**Tasks:**
1. Add all new webhook event types to the event system
2. Implement usage tracking:
   - `voice_call_started` event
   - `voice_call_minute` event (emitted every minute during active call)
   - `voice_call_ended` event with final duration
   - Track by tier (basic vs premium) for billing
3. Integrate with existing tier limit enforcement
4. Write tests
5. Commit: "Add voice webhook events and usage tracking"

#### V4.4. Voice E2E Testing (Day 5-7) [✓]

**Tasks:**
1. Full E2E testing: Basic tier complete flow
2. Full E2E testing: Premium tier complete flow
3. Full E2E testing: Call intelligence pipeline (record → transcribe → embed → score → summarize → scan)
4. Load testing: concurrent calls (5, 25, 100)
5. Latency benchmarking: measure end-to-end response time for both tiers
6. Error handling audit: network failures, provider outages, WebSocket disconnects
7. Security audit: auth on all endpoints, WebSocket auth, recording access
8. Fix issues found during testing
9. Commit: "Voice calls — E2E testing and polish"

### 4.6. Phase V5 — MCP Split + Hosting (1.5 weeks)

This phase restructures the monolithic MCP server into domain-specific servers and deploys hosted endpoints.

#### V5.1. Extract MCP Core (Day 1-2) [✓]

**Tasks:**
1. Create `mcp-core/` package with shared infrastructure:
   - `api-client.ts` — HTTP client with auth
   - `config.ts` — env var loading, API URL, keys
   - `http-transport.ts` — StreamableHTTPServerTransport setup
   - `rate-limiter.ts` — per-key rate limiting
   - `circuit-breaker.ts` — org-level failure detection
   - `session-registry.ts` — HTTP session management
   - `metrics.ts` — tool call tracking
   - `auth.ts` — API key validation, prefix checking
2. Publish as `@anima-labs/mcp-core`
3. Write tests for core infrastructure
4. Commit: "Extract MCP core infrastructure package"

#### V5.2. Split Into Domain MCP Servers (Day 2-5) [✓]

**Tasks:**
1. Create `mcp-agent/` — agent, organization, identity, registry, a2a tools (~25 tools)
   - Import from `@anima-labs/mcp-core`
   - Own `package.json`, `tsconfig.json`, entry point
   - Publish as `@anima-labs/mcp-agent`
2. Create `mcp-email/` — email, message, domain, address tools (~30 tools)
   - Publish as `@anima-labs/mcp-email`
3. Create `mcp-phone/` — phone SMS + voice tools (~25 tools, including new voice tools)
   - Publish as `@anima-labs/mcp-phone`
4. Create `mcp-vault/` — vault, security tools (~15 tools)
   - Publish as `@anima-labs/mcp-vault`
5. Create `mcp-platform/` — utility, webhook, pod, compliance, anomaly tools (~20 tools)
   - Publish as `@anima-labs/mcp-platform`
6. Update `@anima-labs/mcp` meta-package to import all sub-packages (backwards compatible)
7. Verify `npx @anima-labs/mcp --tools=phone,email` still works
8. Write tests for each sub-server
9. Commit: "Split MCP into domain-specific servers"

#### V5.3. Add Voice MCP Tools to mcp-phone (Day 5-6) [✓]

> **Directory:** `/mcp/` (`@anima-labs/mcp`) — or split into `mcp-phone/` if V5.2 splits first

**Tasks:**
1. Add 10 voice tools to **`/mcp/src/tools/voice/`** (or `mcp-phone/src/tools/voice/` post-split):
   - `voice_catalog`, `voice_create_call`, `voice_list_calls`, `voice_get_call`
   - `voice_get_transcript`, `voice_get_recording`, `voice_get_summary`
   - `voice_get_score`, `voice_search_calls`, `voice_get_security_scan`
2. Add Zod schemas with rich descriptions for Claude
3. Ensure existing phone_* tools (search, provision, send_sms, etc.) still work
4. Write tests
5. Commit: "Add voice tools to mcp-phone server"

#### V5.4. Deploy Hosted MCP on Cloud Run (Day 6-8) [✓]

**Tasks:**
1. Create `Dockerfile` for each MCP server (lightweight, Bun runtime)
2. Create `cloudbuild.yaml` for MCP deployment pipeline
3. Deploy Cloud Run services:
   - `mcp-agent.anima.com` or `mcp.anima.com/agent`
   - `mcp-email.anima.com` or `mcp.anima.com/email`
   - `mcp-phone.anima.com` or `mcp.anima.com/phone`
   - `mcp-vault.anima.com` or `mcp.anima.com/vault`
   - `mcp-platform.anima.com` or `mcp.anima.com/platform`
4. Configure Cloud Run:
   - Min instances: 0 (scale to zero for cost)
   - Max instances: 10 per server (auto-scale)
   - Memory: 256MB (MCP servers are lightweight)
   - CPU: 1 vCPU
   - Concurrency: 80 requests per instance
   - Startup: < 2 seconds (Bun + small package)
5. Set up load balancer with custom domain (`mcp.anima.com`)
6. Configure auth: Bearer token validation against Anima API
7. Add health check endpoints
8. Write deployment verification tests
9. Commit: "Deploy hosted MCP servers on Cloud Run"

#### V5.5. Update Documentation & Claude Desktop Config (Day 8-10) [✓]

**Tasks:**
1. Update MCP setup docs with new package names:
   ```json
   // Claude Desktop config — local
   {
     "mcpServers": {
       "anima-phone": {
         "command": "npx",
         "args": ["@anima-labs/mcp-phone"],
         "env": { "ANIMA_API_KEY": "ak_..." }
       }
     }
   }

   // Claude Desktop config — hosted remote
   {
     "mcpServers": {
       "anima-phone": {
         "url": "https://mcp.anima.com/phone",
         "headers": { "Authorization": "Bearer ak_..." }
       }
     }
   }
   ```
2. Update CLI `setup-mcp` command to offer choice of servers
3. Update README with new MCP architecture
4. Test with Claude Desktop, Cursor, and Claude Code
5. Commit: "Update MCP docs for split servers and hosted endpoints"

### 4.7. Phase V6 — SDK Improvements (1.5 weeks)

> **Directory references for all V6 tasks:**
> - Node SDK: **`/node/`** (`@anima-labs/sdk`)
> - Python SDK: **`/python/`** (`anima-labs`)
> - Go SDK: **`/go/`** (`anima-go`)

#### V6.1. Auto-Pagination Iterators (Day 1-3) [✓]

**Tasks:**
1. **Node SDK (`/node/`):** Add `AsyncIterableIterator` to all `.list()` methods
   - Return async iterable that auto-fetches next pages
   - Support `for await (const item of anima.calls.list())` pattern
   - Also keep existing direct `.list()` returning `PaginatedResponse<T>` for single-page use
2. **Python SDK (`/python/`):** Add `__iter__` and `__aiter__` to all `.list()` methods
   - Support `for call in anima.calls.list()` and `async for call in async_anima.calls.list()`
3. Write tests for both with pagination edge cases (empty pages, single item, many pages)
4. Commit: "Add auto-pagination iterators to Node and Python SDKs"

#### V6.2. Idempotency Keys (Day 3-4) [✓]

**Tasks:**
1. Add optional `requestOptions` parameter to all mutating methods across all 3 SDKs:
   ```typescript
   // Node
   create(params: CreateParams, options?: RequestOptions): Promise<T>
   interface RequestOptions { idempotencyKey?: string; timeout?: number; maxRetries?: number; }
   ```
2. Auto-generate UUID idempotency key on retries (like Stripe)
3. Pass as `Idempotency-Key` header
4. Add server-side idempotency check (Redis-based, 24h TTL)
5. Write tests
6. Commit: "Add idempotency key support to all SDKs"

#### V6.3. Retry Improvements (Day 4-5) [✓]

**Tasks:**
1. Replace fixed `[1s, 2s, 4s]` with jittered exponential backoff:
   ```
   delay = min(random(0, BASE * 2^attempt), MAX_DELAY)
   ```
2. Respect `Retry-After` header (already parsed, wire it into retry loop)
3. Apply to all 3 SDKs
4. Write tests
5. Commit: "Add retry jitter and Retry-After header support"

#### V6.4. Environment Variable Fallback + Debug Logging (Day 5-6) [✓]

**Tasks:**
1. All SDKs auto-detect `ANIMA_API_KEY` and `ANIMA_API_URL` environment variables
2. Add debug logging activated by `ANIMA_LOG=debug`:
   - Log all HTTP requests (method, path, status, duration)
   - Log retry attempts
   - Log WebSocket events
3. Node: use `console.debug` with prefix
4. Python: use `logging` module with `anima` logger
5. Go: use `log/slog` with structured output
6. Write tests
7. Commit: "Add env var fallback and debug logging to all SDKs"

#### V6.5. Per-Request Options + Raw Response (Day 6-8) [✓]

**Tasks:**
1. Add `RequestOptions` to all methods (timeout, maxRetries, idempotencyKey)
2. Add raw response access pattern:
   ```typescript
   // Node
   const { data, response } = await anima.calls.get("call_123", { rawResponse: true });

   // Python
   data, response = anima.calls.get("call_123", raw_response=True)

   // Go
   call, resp, err := client.Calls.GetRaw(ctx, "call_123")
   ```
3. Expose: status code, headers, request ID, response time
4. Write tests
5. Commit: "Add per-request options and raw response access"

#### V6.6. Request/Response Events + Webhook Middleware (Day 8-10) [✓]

**Tasks:**
1. Add event emitters to client:
   ```typescript
   anima.on("request", (req) => { /* method, path, headers */ });
   anima.on("response", (res) => { /* status, duration, headers */ });
   ```
2. Add Express middleware for webhook verification:
   ```typescript
   app.post("/webhooks", anima.webhooks.middleware("whsec_..."), handler);
   ```
3. Add FastAPI dependency for Python:
   ```python
   @app.post("/webhooks")
   async def handle(event = Depends(anima.webhooks.fastapi("whsec_..."))):
   ```
4. Write tests
5. Commit: "Add request/response events and webhook middleware"

### 4.8. Phase V7 — Docs, Examples & Launch (1 week)

#### V7.1. Documentation (Day 1-3) [✓]

**Tasks:**
1. Voice quickstart guide (5-minute "make your first call")
2. WebSocket protocol reference (all message types, examples)
3. Voice catalog reference (all voices with audio samples)
4. Call intelligence guide (recording, transcription, RAG, scoring)
5. MCP setup guide (local + hosted, per-server)
6. SDK migration guide (new features: pagination, idempotency, etc.)
7. Pricing page content
8. Commit: "Add comprehensive voice and SDK documentation"

#### V7.2. Examples (Day 3-5) [✓]

**Tasks:**
1. `examples/voice-customer-support/` — inbound support agent (Node + Python)
2. `examples/voice-outbound-sales/` — outbound sales caller with CRM integration
3. `examples/voice-appointment-reminder/` — outbound notification
4. `examples/multi-channel-agent/` — email + SMS + voice combined workflow
5. `examples/voice-mcp-claude/` — Claude Desktop making phone calls via MCP
6. Update main README with voice capabilities and new SDK features
7. Commit: "Add voice and multi-channel examples"

#### V7.3. Final Testing & Launch (Day 5-7) [✓]

**Tasks:**
1. [✓] Full regression testing across all phases
2. Load testing hosted MCP servers (Cloud Run auto-scaling)
3. SDK compatibility testing (Node 18+, Python 3.9+, Go 1.22+)
4. Security audit: all new endpoints, WebSocket auth, MCP auth, recording access
5. Performance benchmarking: voice latency, MCP response time
6. [✓] Fix any remaining issues
7. Tag releases for all packages
8. Commit: "Voice calls v1.0 — ready for launch"

---

### 3.11. MCP Server Restructuring

The current MCP server (`@anima-labs/mcp`) has grown to **162 tools across 21 groups** — all in a single monolithic server. This is too large. Loading 162 tool definitions overwhelms LLM context windows and makes it harder for agents to discover relevant tools. We will break the MCP server into focused, domain-specific MCP servers.

#### Proposed MCP Server Split

| MCP Server | Package Name | Tools | Tool Groups |
|---|---|---|---|
| **@anima-labs/mcp-agent** | `mcp-agent` | ~25 | agent, organization, identity, registry, a2a |
| **@anima-labs/mcp-email** | `mcp-email` | ~30 | email, message, domain, address |
| **@anima-labs/mcp-phone** | `mcp-phone` | ~25 | phone (SMS + Voice), webhook (phone-specific) |
| **@anima-labs/mcp-vault** | `mcp-vault` | ~15 | vault, security |
| **@anima-labs/mcp-platform** | `mcp-platform` | ~20 | utility, webhook, pod, compliance, anomaly |

**Each MCP server is independently installable:**

```bash
# Install only what you need
npx @anima-labs/mcp-phone          # Just phone (SMS + voice)
npx @anima-labs/mcp-email          # Just email
```

**Meta-package for everything:**

```bash
# Install all MCP servers at once (backwards compatible)
npx @anima-labs/mcp                # Loads all sub-servers
npx @anima-labs/mcp --tools=phone,email  # Selective (existing flag still works)
```

#### Shared Infrastructure

All MCP servers share the same core infrastructure (extracted to `@anima-labs/mcp-core`):
- API client with auth
- Rate limiter
- Circuit breaker
- Session registry
- HTTP transport
- Config loading
- Metrics

```
@anima-labs/mcp-core       ← Shared infra (api-client, auth, transports)
  ├── @anima-labs/mcp-agent
  ├── @anima-labs/mcp-email
  ├── @anima-labs/mcp-phone   ← Voice tools land here
  ├── @anima-labs/mcp-vault
  └── @anima-labs/mcp-platform
```

#### MCP Hosting Model

**Current state:** MCP is local-only. Users run `npx @anima-labs/mcp` which starts a stdio process that Claude Desktop, Cursor, etc. connect to. The HTTP mode exists but is not deployed as a hosted service.

**Recommendation: Keep local-first, add optional hosted remote endpoint.**

| Mode | How It Works | Best For |
|---|---|---|
| **Local stdio (default)** | `npx @anima-labs/mcp-phone` — runs locally, Claude connects via stdio | Development, Claude Desktop, Cursor, VS Code |
| **Local HTTP** | `npx @anima-labs/mcp-phone --http` — local HTTP server | Multi-client local setups, testing |
| **Hosted remote** | `https://mcp.anima.com/phone` — deployed on Cloud Run | Production agents, serverless functions, remote MCP clients |

**Why hosted matters for voice:** An AI agent running in the cloud (e.g., on a serverless platform) that needs to make phone calls can't run a local stdio MCP server. It needs a remote MCP endpoint. AgentPhone already offers this (`https://mcp.agentphone.to/mcp`).

**Hosted deployment:**
- Deploy each MCP server as a separate Cloud Run service behind `mcp.anima.com`
- Routes: `mcp.anima.com/agent`, `mcp.anima.com/email`, `mcp.anima.com/phone`, etc.
- Auth: Bearer token (existing API key auth)
- Auto-scaling: Cloud Run handles scaling per-server independently
- Cost: Minimal — Cloud Run bills per-request, MCP servers are stateless between sessions

**This is NOT in scope for the voice call implementation** — it's a separate workstream. But the voice MCP tools should be designed to work in both local and hosted modes from day one.

## Appendix A: Environment Variables

New environment variables required:

```env
# Deepgram (Premium tier)
DEEPGRAM_API_KEY=           # Deepgram API key for Nova-3 STT

# ElevenLabs (Premium tier)
ELEVENLABS_API_KEY=         # ElevenLabs API key for streaming TTS

# Call Recording
CALL_RECORDING_GCS_BUCKET=  # GCS bucket for call recordings
CALL_RECORDING_GCS_PROJECT= # GCP project ID

# Voice defaults
DEFAULT_VOICE_TIER=basic    # Default tier for new phone identities
DEFAULT_VOICE_ID=telnyx:kokoro-sarah  # Default voice
INBOUND_ACCEPT_TIMEOUT_MS=15000       # How long to wait for agent to accept
```

## Appendix B: Files Created/Modified Summary

**New packages (V5 — MCP Split):**
- `mcp-core/` — shared MCP infrastructure (~10 files)
- `mcp-agent/` — agent MCP server (~8 files)
- `mcp-email/` — email MCP server (~8 files)
- `mcp-phone/` — phone + voice MCP server (~10 files)
- `mcp-vault/` — vault MCP server (~6 files)
- `mcp-platform/` — platform MCP server (~8 files)

**New files — Voice (~25):**
- `anima/packages/phone/src/voice/call-manager.ts`
- `anima/packages/phone/src/voice/call-session.ts`
- `anima/packages/phone/src/voice/types.ts`
- `anima/packages/phone/src/voice/catalog.ts`
- `anima/packages/phone/src/voice/pipelines/interface.ts`
- `anima/packages/phone/src/voice/pipelines/basic.ts`
- `anima/packages/phone/src/voice/pipelines/premium.ts`
- `anima/packages/phone/src/voice/providers/deepgram.ts`
- `anima/packages/phone/src/voice/providers/elevenlabs.ts`
- `anima/apps/api/src/routes/handlers/voice.ts`
- `anima/apps/api/src/ws/voice.ts`
- `anima/apps/api/src/ws/telnyx-audio.ts`
- `anima/apps/api/src/workers/call-transcription.ts`
- `anima/apps/api/src/workers/call-embedding.ts`
- `anima/apps/api/src/workers/call-summary.ts`
- `anima/apps/api/src/workers/call-scoring.ts`
- `anima/apps/api/src/workers/call-security.ts`
- `anima/packages/contracts/src/schemas/voice.ts`
- `mcp/src/tools/voice/index.ts`
- `cli/src/commands/voice/*.ts` (8 files)
- `node/src/resources/calls.ts`
- `node/src/resources/voices.ts`
- `python/src/anima/resources/calls.py`
- `python/src/anima/resources/voices.py`
- `go/calls.go`
- `go/voices.go`

**Modified files (~15):**
- `anima/packages/db/prisma/schema.prisma` (new models, remove TWILIO)
- `anima/packages/phone/src/telnyx.ts` (add call control methods)
- `anima/packages/phone/src/types.ts` (remove Twilio, add voice types)
- `anima/packages/phone/src/factory.ts` (simplify to Telnyx-only)
- `anima/apps/api/src/routes/phone-webhooks.ts` (add call webhooks, remove Twilio)
- `anima/apps/api/src/server.ts` (register voice WS endpoints)
- `anima/apps/api/src/routes/router.ts` (add voice routes)
- `mcp/src/tools/index.ts` (register voice tools)
- `cli/src/commands/index.ts` (register voice commands)
- `node/src/index.ts` (export calls, voices)
- `python/src/anima/__init__.py` (export calls, voices)
- `go/client.go` (add calls, voices services)

**Deleted files (2):**
- `anima/packages/phone/src/twilio.ts`
- `anima/packages/phone/src/__tests__/twilio.test.ts`

## Appendix C: Competitor Feature Comparison (Post-Implementation)

| Feature | Anima | AgentPhone | Vapi | Retell AI | Bland AI |
|---------|-------|------------|------|-----------|----------|
| **Voice calls** | Yes (2 tiers) | Yes | Yes | Yes | Yes |
| **Email** | Yes | No | No | No | No |
| **SMS** | Yes | Yes | No | No | No |
| **Credential vault** | Yes | No | No | No | No |
| **Agent identity** | Yes | No | No | No | No |
| **MCP tools** | 360+ | 26 | 0 | 0 | 0 |
| **SDKs** | Node, Python, Go | Python, TS | Python, Node, React | Python, Node, React | Node, Python |
| **CLI** | Yes (50+ cmds) | No | No | No | No |
| **Tiered voice quality** | Yes (Basic/Premium) | No | No (BYO) | No | No |
| **Call recording** | Yes | Yes | Yes | Yes | Yes |
| **Call transcription** | Yes (real-time + batch) | Yes | Yes | Yes | Yes |
| **RAG search** | Yes (semantic + FTS) | No | No | No | No |
| **Call scoring** | Yes (12 metrics) | No | No | No | Limited |
| **Auto-summarization** | Yes (3-level) | No | No | Limited | Limited |
| **Vulnerability detection** | Yes (6 threat types) | No | No | No | No |
| **Cross-channel intelligence** | Yes | No | No | No | No |
| **Compliance scanning** | Yes | No | No | No | No |
| **Interruption handling** | Yes (both tiers) | Yes (barge-in) | Yes | Yes | Yes |
| **Voice catalog w/ descriptions** | Yes | Partial | Yes | Limited | Limited |
| **Webhook events** | 17+ types | ~5 types | ~8 types | ~6 types | ~5 types |
