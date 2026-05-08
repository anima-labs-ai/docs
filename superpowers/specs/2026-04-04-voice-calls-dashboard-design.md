# Voice Calls Dashboard — Design Specification

**Date:** 2026-04-04
**Author:** Diyan Bogdanov + Claude
**Status:** Draft
**Scope:** Console UI for visualizing voice calls, transcripts, intelligence, analytics, and voice catalog

---

## 1. Overview

The Anima console (`anima/apps/console/`) has pages for Agents, Messages, Phone (number provisioning), Vault, and more — but no UI for the voice call features built in the voice calls design spec. This spec adds a comprehensive "Voice Calls" section under the Phone group, covering call history, transcripts, recordings, summaries, scoring, security scans, semantic search, analytics, and voice catalog.

**Target persona:** Developer/builder — building and debugging AI agent voice features. Prioritizes raw technical detail, timestamps, IDs, and API-level visibility over high-level dashboards.

**Tech stack (existing):** Next.js 15, React 19, TypeScript 5.7, Tailwind CSS 4, oRPC + TanStack Query, Recharts, Framer Motion, Lucide React, Clerk auth. No component library — all UI built directly with Tailwind + CSS custom properties.

---

## 2. Navigation Changes

### 2.1. Sidebar Config

The flat `Phone` nav item becomes an expandable group with two sub-items.

**File:** `apps/console/src/components/dashboard/config.ts`

Current:
```typescript
{ href: "/phone", label: "Phone" }
```

New structure:
```typescript
{
  label: "Phone",
  children: [
    { href: "/phone", label: "Numbers" },
    { href: "/phone/calls", label: "Voice Calls" },
  ],
}
```

The sidebar component (`sidebar.tsx`) needs to handle grouped nav items — show a collapsible group that highlights when any child route is active. This is a type change: the current `dashboardNavConfig` is a flat `readonly` array of `{ href, label }`. Adding `children` requires updating the type definition and the sidebar rendering logic to distinguish flat items from grouped items (check for `children` property). The `sidebar.tsx` iteration logic and `header.tsx` breadcrumb logic will both need to handle the new shape.

### 2.2. Route Structure

All new routes live under `/phone/` in the existing `(dashboard)` layout group:

```
/phone                     — existing phone numbers page (renamed to "Numbers" in nav)
/phone/calls               — call list table
/phone/calls/search        — semantic transcript search
/phone/calls/analytics     — aggregate metrics + charts
/phone/calls/[id]          — call detail (tabbed)
/phone/voices              — voice catalog grid
```

### 2.3. Secondary Navigation

The Voice Calls pages share a tab bar at the top:

```
Calls | Search | Analytics | Voices
```

This is a simple row of links using `usePathname()` to highlight the active tab. Styled as monospace uppercase text with an underline on the active item, matching the terminal aesthetic.

---

## 3. Pages

### 3.1. Call List (`/phone/calls`)

**Data:** `GET /voice/calls` via `orpc.voice.listCalls.queryOptions()`

**Layout:**
1. Page title "Voice Calls" + secondary tab nav
2. Filter bar (single row):
   - Agent dropdown (populated from `orpc.agent.list`)
   - Direction toggle: All / Inbound / Outbound
   - State dropdown: All / Active / Ended / Failed
3. Sortable table

**Table columns:**

| Column | Render | Sortable |
|--------|--------|----------|
| Call ID | Truncated, monospace, `font-mono text-xs`. Links to `/phone/calls/:id` | No |
| Direction | Badge: `INBOUND` (cyan) / `OUTBOUND` (default) | Yes |
| From → To | Formatted phone numbers, `→` separator | No |
| Agent | Agent name, linked to `/agents/:id` | Yes |
| Tier | Badge: `basic` (muted) / `premium` (accent) | Yes |
| State | Color-coded badge: green = ACTIVE, gray = ENDED, red = FAILED | Yes |
| Duration | Formatted, e.g., "8m 12s". Dash if null. | Yes |
| Score | Composite score. Green ≥80, yellow 60-79, red <60. Dash if not scored. | Yes |
| Date | Relative time ("2h ago") with ISO tooltip on hover | Yes |

**Pagination:** Offset-based at bottom. Previous / Next buttons with page indicator. Matches API params (`limit`, `offset`).

**Empty state:** Phone icon + "No calls yet. Create your first call via the SDK or API."

**Loading state:** `loading.tsx` with `TableSkeleton` matching column count and row count (8 rows).

**Pattern:** Follows existing phone page patterns — `"use client"`, `useSuspenseQuery`, `useMemo` for client-side filter application, `AnimatePresence` for row animations, hover-revealed action column.

### 3.2. Call Detail (`/phone/calls/[id]`)

**Data:** Multiple parallel queries:
- `orpc.voice.getCall.queryOptions({ input: { callId } })`
- `orpc.voice.getTranscript.queryOptions({ input: { callId } })`
- `orpc.voice.getSummary.queryOptions({ input: { callId } })`
- `orpc.voice.getScore.queryOptions({ input: { callId } })`
- `orpc.voice.getSecurity.queryOptions({ input: { callId } })`
- `orpc.voice.getRecording.queryOptions({ input: { callId } })`

Use `useSuspenseQueries` or individual `useSuspenseQuery` calls wrapped in a Suspense boundary so partial data renders progressively.

#### 3.2.1. Fixed Header (always visible)

- Back link: "← Voice Calls" (monospace, links to `/phone/calls`)
- Call ID (monospace, copyable) + direction badge + tier badge + state badge
- **Recording player:**
  - Audio element with custom styled controls (play/pause button, progress bar, current time / total time, download button)
  - Source URL from `getRecording` response (signed URL)
  - If no recording: gray placeholder "Recording not available"
- **Metadata row** (4-6 compact stat cards in a grid):
  - From → To (formatted phone numbers)
  - Agent (linked)
  - Duration
  - Started at (formatted timestamp)
  - End reason (if ended)

#### 3.2.2. Tab Navigation

Three tabs below the header. Uses URL search params (`?tab=overview|transcript|intelligence`) with `overview` as default. Styled as monospace uppercase with bottom border indicator.

#### 3.2.3. Tab: Overview

- **Summary card:**
  - One-liner in larger text (`text-base text-fg`)
  - Topics as inline tags/badges
  - Intent + outcome badges
- **Action items** list (bulleted, with owner if available)
- **Decisions** list
- **Open questions** list
- **Next steps** list
- **Full metadata** section: call ID, phone identity ID, created at, updated at

If summary is not yet generated (call still active or processing): "Summary will be available after the call ends."

#### 3.2.4. Tab: Transcript

- **Speaker filter** toggle: All / Agent / Caller (top-right)
- **Copy transcript** button (top-right, copies as plain text)
- **Conversation view:**
  - Each segment as a row:
    - Left gutter: timestamp (`00:03:24`, monospace, `text-fg-dimmer`)
    - Speaker label: `agent` in cyan (`text-cyan`), `caller` in default (`text-fg`)
    - Text content
  - Timestamps are clickable — sets recording player to that time
  - Low-confidence segments (< 0.7): dimmed with `opacity-60` + dotted underline
  - Final vs interim: only show `isFinal: true` segments by default, toggle to show interim
- **Empty state:** "No transcript segments recorded."

#### 3.2.5. Tab: Intelligence

Two sections side by side (or stacked on narrow screens):

**Left: Score**
- Large composite score number (e.g., "87" in 48px font) with `/100` suffix
- Color: green ≥80, yellow 60-79, red <60
- 6 sub-score bars (horizontal bar chart using Recharts `BarChart` or simple CSS bars):
  - Resolution, Sentiment, Compliance, Efficiency, Engagement, Latency
  - Each: label + score + colored bar
- **Metrics section** below bars (rendered dynamically from `metrics` JSON record):
  - The API returns `metrics` as `Record<string, unknown>` — an untyped bag of key-value pairs
  - Render each key-value pair as a label + formatted value row
  - Expected keys (based on scoring worker implementation): `talkToListenRatio`, `longestMonologue`, `interruptionRate`, `deadAir`, `avgResponseLatency`
  - Format known keys: ratios as "2.3:1", durations in seconds, percentages with %
  - Unknown keys: render raw value with humanized key label

If score is not yet generated: "Scoring will be available after the call ends and transcript is processed."

**Right: Security Scan**
- Risk score (0-100) with color coding (green ≤20, yellow 21-60, red >60)
- Compliance pass/fail badge
- **Threats list:** If empty: green checkmark + "No threats detected". If threats exist: list with severity badge (critical/high/medium/low), type, description
- **PII detected list:** If empty: "No PII detected". If found: type, speaker, redacted indicator

If security scan not yet run: "Security scan will be available after the call ends."

### 3.3. Search Page (`/phone/calls/search`)

**Data:** Two endpoints depending on toggle state:
- **Voice only:** `POST /voice/search` via `orpc.voice.search.mutationOptions()` — input: `{ query, agentId?, dateFrom?, dateTo?, limit?, threshold? }`
- **Cross-channel:** `POST /voice/search/cross-channel` via `orpc.voice.crossChannelSearch.mutationOptions()` — input: `{ query, channels?, limit?, threshold? }` where `channels` defaults to `["voice", "email", "sms"]`

Both are mutations (user-initiated, not auto-fetched).

**Layout:**
1. Secondary tab nav (Calls | **Search** | Analytics | Voices)
2. Large search input with magnifying glass icon
   - Placeholder: "Search across call transcripts..."
   - Submits on Enter or button click
3. Toggle: "Voice only" / "Cross-channel" (adds emails + SMS). Switching clears current results.
4. Filters row (collapsible, shown after first search):
   - Agent dropdown (voice-only mode)
   - Date range (from / to date inputs, voice-only mode)
   - Relevance threshold slider (0.5-1.0, default 0.7)
5. Results list

**Each result card:**
- Call ID (linked) + speaker label + timestamp range
- Matched text snippet with search terms highlighted (bold or background highlight)
- Timestamp in call (clickable → navigates to `/phone/calls/:id?tab=transcript&t=<seconds>`)
- Relevance/similarity score as a thin colored bar or percentage

**Note:** The search API returns `callId`, `matchedText`, `speaker`, `startTime`, `endTime`, `similarity`, `chunkType` — but not call direction or date. To show additional call context, the UI can either do a secondary batch lookup for displayed results or show only the fields available from the search response. Recommend the simpler approach: show only search-returned fields.

**States:**
- Before search: centered illustration + "Enter a query to semantically search across all call transcripts."
- No results: "No matching transcripts found. Try a broader query."
- Loading: spinner below search bar
- Results: list with count ("12 results")

### 3.4. Analytics Page (`/phone/calls/analytics`)

**Data:** `GET /voice/analytics` via `orpc.voice.analytics.queryOptions()`

**Note:** The current API returns `totalCalls`, `averageCompositeScore`, `averageResolutionScore`, `averageSentimentScore`, and a 4-bucket `scoreDistribution` (excellent/good/average/poor). The UI is scoped to match this available data. Additional charts (calls over time, direction split, per-agent breakdown) would require backend API extensions and are deferred.

**Layout:**
1. Secondary tab nav (Calls | Search | **Analytics** | Voices)
2. Stats row — 3 cards:
   - Total calls (number)
   - Average composite score (colored: green ≥80, yellow 60-79, red <60)
   - Average resolution score
3. Charts (using Recharts):
   - **Score distribution:** `BarChart` with 4 buckets from API: Excellent, Good, Average, Poor. Color-coded bars (green, cyan, yellow, red).
   - **Score breakdown:** `BarChart` horizontal — composite vs resolution vs sentiment average scores for easy comparison.

**Chart styling:** Use accent green for primary data, cyan for secondary, muted backgrounds. Match the dark terminal aesthetic — dark chart backgrounds, light grid lines.

**Empty state:** "No call data yet. Analytics will appear after your first completed call."

**Future extensions (require backend changes):**
- Calls over time (daily line chart) — needs time-series endpoint
- Direction split (inbound vs outbound) — needs direction aggregation
- Top agents by call volume — needs per-agent aggregation
- Average duration / total minutes — needs duration aggregation

### 3.5. Voice Catalog (`/phone/voices`)

**Data:** `GET /voice/catalog` via `orpc.voice.catalog.queryOptions()`

**Layout:**
1. Secondary tab nav (Calls | Search | Analytics | **Voices**)
2. Filter bar:
   - Tier toggle: All / Basic / Premium
   - Gender toggle: All / Male / Female / Neutral
   - Language dropdown (populated from voice data)
3. Grid of cards (3 columns on desktop, 2 on tablet, 1 on mobile)

**Each voice card:**
- **Header:** Voice name (large) + provider badge (telnyx = blue, elevenlabs = purple, aws-polly = orange)
- **Tags row:** Tier badge + gender + language + accent
- **Style:** Style tag (e.g., "warm", "professional") in italics
- **Description:** 2-3 lines, truncated with "..." and expand on hover/click
- **Audio preview:** Small play button with waveform or simple progress bar. Uses `previewUrl` from voice data. Shows "No preview" if URL is null.
- **Voice ID:** Monospace, small, with copy button (`text-fg-dimmer font-mono text-xs`)

**Client-side filtering** with `useMemo` (voice catalog is small enough to load all at once).

**Empty state with filters:** "No voices match your filters."

---

## 4. Shared Components

New components created for this feature, placed in `apps/console/src/components/voice/`:

| Component | Purpose |
|-----------|---------|
| `call-tabs.tsx` | Secondary tab nav (Calls / Search / Analytics / Voices) |
| `call-table.tsx` | Sortable call list table with filters |
| `call-badges.tsx` | Direction, tier, state, score badges |
| `recording-player.tsx` | Audio player with custom controls |
| `transcript-view.tsx` | Chat-style transcript with clickable timestamps |
| `score-card.tsx` | Composite score + sub-score bars |
| `security-card.tsx` | Risk score + threats + PII list |
| `summary-card.tsx` | One-liner + topics + action items |
| `voice-card.tsx` | Voice catalog card with audio preview |
| `search-results.tsx` | Search result card with snippet highlight |
| `stats-row.tsx` | 4-card stats row for analytics |

These components are specific to voice/calls. They use existing Tailwind conventions and CSS custom properties — no new design system components needed.

---

## 5. Data Fetching

All API calls go through the existing oRPC client. New query/mutation keys:

```typescript
// Queries
orpc.voice.listCalls.queryOptions({ input: { agentId?, direction?, state?, limit?, offset? } })
orpc.voice.getCall.queryOptions({ input: { callId } })
orpc.voice.getTranscript.queryOptions({ input: { callId } })
orpc.voice.getRecording.queryOptions({ input: { callId } })
orpc.voice.getSummary.queryOptions({ input: { callId } })
orpc.voice.getScore.queryOptions({ input: { callId } })
orpc.voice.getSecurity.queryOptions({ input: { callId } })
orpc.voice.catalog.queryOptions({ input: { tier?, gender?, language? } })
orpc.voice.analytics.queryOptions({ input: { from?, to? } })

// Mutations
orpc.voice.search.mutationOptions()  // POST /voice/search
```

**Prerequisite:** The oRPC contract (`packages/contracts/src/contracts/voice.ts`) already defines these endpoints. The console just needs to wire them up via `orpc.voice.*`.

**Cache invalidation:** Call list should refetch when navigating back from detail page (stale-while-revalidate with 30s stale time). Analytics page can have a longer stale time (5 min).

---

## 6. Styling Conventions

Follow existing console patterns exactly:

- **Backgrounds:** `bg-bg`, `bg-bg-surface`, `bg-bg-elevated`
- **Text:** `text-fg`, `text-fg-muted`, `text-fg-dimmer`
- **Borders:** `border-border`
- **Accent:** `bg-accent`, `text-accent`, `bg-accent-muted`, `hover:bg-accent-hover`
- **Status colors:** Success = `bg-accent-muted text-accent`, Warning = `bg-warning-muted text-warning`, Error = `bg-error-muted text-error`
- **Labels:** `font-mono text-xs uppercase tracking-wider text-fg-dimmer`
- **Tables:** `px-6 py-3` header, `px-6 py-4` rows
- **Hover actions:** `opacity-0 group-hover:opacity-100 transition-opacity`
- **Animations:** Framer Motion `AnimatePresence` for list items, `motion.tr` for table rows
- **Loading:** Dedicated `loading.tsx` per route with matching skeleton

---

## 7. Testing Plan

### 7.1. Unit Tests

Test individual components in isolation using the existing test setup. Mock oRPC responses.

| Component | Tests |
|-----------|-------|
| `call-badges.tsx` | Renders correct badge color/text for each direction, tier, state, score range |
| `recording-player.tsx` | Renders play/pause, handles no-recording state, displays time correctly |
| `transcript-view.tsx` | Renders segments with correct speaker colors, handles empty state, filters by speaker |
| `score-card.tsx` | Renders score with correct color thresholds, handles missing score |
| `security-card.tsx` | Renders clean state, renders threats list, renders PII list |
| `summary-card.tsx` | Renders one-liner, topics tags, action items, handles not-yet-generated state |
| `voice-card.tsx` | Renders voice info, play button, handles missing preview URL |
| `call-table.tsx` | Sorts by column, filters by direction/state/agent, handles empty state |
| `search-results.tsx` | Renders snippet with highlight, handles empty results |
| `stats-row.tsx` | Renders 4 stat cards, handles zero/null values |

### 7.2. Page-Level Tests

Test each page renders correctly with mocked data and handles loading/error/empty states.

| Page | Tests |
|------|-------|
| Call List | Renders table with mock calls, filters reduce rows, pagination works, empty state shows correctly, loading skeleton matches layout |
| Call Detail — Overview | Renders summary, action items, metadata. Handles missing summary (not generated yet) |
| Call Detail — Transcript | Renders conversation view, speaker filter toggles work, timestamp click calls handler, low-confidence segments are dimmed |
| Call Detail — Intelligence | Renders score + sub-scores, renders security scan, handles not-yet-generated states for both |
| Search | Renders before-search state, submits query, renders results, toggles cross-channel, handles no results |
| Analytics | Renders stats row (3 cards), renders 2 charts (score distribution + score breakdown), empty state when no data |
| Voice Catalog | Renders voice grid, filters reduce cards, audio preview plays, handles no-preview state |

### 7.3. Integration Tests

Test data fetching and navigation flows end-to-end against a running API (or MSW-mocked API).

| Flow | Steps |
|------|-------|
| Call list → detail → back | Load call list, click a call, verify detail page loads all tabs, click back, verify list still has correct filters |
| Search → result → detail | Enter search query, click a result, verify navigates to correct call detail at correct transcript timestamp |
| Filter persistence | Apply filters on call list, navigate to detail, come back, verify filters are preserved (URL params) |
| Analytics date range | Change date range, verify all 4 charts update, verify stats row updates |
| Voice catalog filters | Apply tier + gender filter, verify grid reduces, clear filters, verify all voices return |
| Recording playback | On call detail, verify audio element loads signed URL, play button toggles to pause |
| Tab navigation | Click each tab in secondary nav, verify correct page loads, verify active tab is highlighted |

### 7.4. Manual Testing Checklist

Run through these with a real Anima API key and real call data:

| # | Test | Pass |
|---|------|------|
| 1 | Navigate to Phone → Voice Calls, see call list | ☐ |
| 2 | Call list shows real calls with correct data | ☐ |
| 3 | Filter by direction (Inbound), verify table updates | ☐ |
| 4 | Filter by agent, verify table updates | ☐ |
| 5 | Sort by duration, verify order changes | ☐ |
| 6 | Click a call, arrive at detail page | ☐ |
| 7 | Recording player loads and plays audio | ☐ |
| 8 | Overview tab shows summary, topics, action items | ☐ |
| 9 | Transcript tab shows conversation with timestamps | ☐ |
| 10 | Click transcript timestamp, recording seeks to that time | ☐ |
| 11 | Filter transcript by speaker (Agent only) | ☐ |
| 12 | Intelligence tab shows score with sub-score bars | ☐ |
| 13 | Intelligence tab shows security scan results | ☐ |
| 14 | Navigate to Search, enter a query, see results | ☐ |
| 15 | Toggle cross-channel search, verify results include email/SMS | ☐ |
| 16 | Click search result, navigate to call at correct timestamp | ☐ |
| 17 | Navigate to Analytics, see stats and charts | ☐ |
| 18 | Analytics shows score distribution and breakdown charts | ☐ |
| 19 | Navigate to Voices, see voice cards grid | ☐ |
| 20 | Filter voices by tier (Premium), grid reduces | ☐ |
| 21 | Play voice preview audio sample | ☐ |
| 22 | Copy voice ID from catalog card | ☐ |
| 23 | All pages show correct loading skeletons | ☐ |
| 24 | All pages show correct empty states | ☐ |
| 25 | Call detail handles call with no recording gracefully | ☐ |
| 26 | Call detail handles call with no summary (still processing) | ☐ |
| 27 | Call detail handles call with no score (still processing) | ☐ |
| 28 | Dark mode renders correctly on all pages | ☐ |
| 29 | Responsive: pages render correctly on 1024px width | ☐ |
| 30 | Sidebar shows Phone group expanded with Numbers + Voice Calls | ☐ |

### 7.5. Accessibility

- All interactive elements (buttons, links, tabs) are keyboard-navigable
- Audio player has aria-labels for play/pause/seek
- Table has proper `<thead>` / `<tbody>` structure
- Tab navigation uses `role="tablist"` / `role="tab"` / `role="tabpanel"`
- Color-coded scores have text labels (not color-only information)
- Search input has associated label

---

## 8. Implementation Order

Suggested build sequence (each step is independently shippable):

1. **Navigation changes** — sidebar group, secondary tab nav component
2. **Call list page** — table, filters, pagination, loading/empty states
3. **Call detail — fixed header + Overview tab** — metadata, summary, recording player
4. **Call detail — Transcript tab** — conversation view, speaker filter, timestamp click
5. **Call detail — Intelligence tab** — score card, security card
6. **Voice catalog page** — grid, filters, audio preview
7. **Search page** — search input, results, cross-channel toggle
8. **Analytics page** — stats row, charts
9. **Polish** — animations, responsive breakpoints, accessibility audit

---

## Appendix: File Structure

```
apps/console/src/
├── app/(dashboard)/phone/
│   ├── page.tsx                    # existing — phone numbers (unchanged)
│   ├── loading.tsx                 # existing — phone numbers loading
│   ├── calls/
│   │   ├── page.tsx                # call list table
│   │   ├── loading.tsx             # call list skeleton
│   │   ├── [id]/
│   │   │   ├── page.tsx            # call detail (tabbed)
│   │   │   └── loading.tsx         # call detail skeleton
│   │   ├── search/
│   │   │   └── page.tsx            # semantic search
│   │   └── analytics/
│   │       └── page.tsx            # aggregate metrics + charts
│   └── voices/
│       ├── page.tsx                # voice catalog grid
│       └── loading.tsx             # voice catalog skeleton
├── components/voice/
│   ├── call-tabs.tsx               # secondary tab nav
│   ├── call-table.tsx              # sortable table with filters
│   ├── call-badges.tsx             # direction, tier, state, score badges
│   ├── recording-player.tsx        # audio player
│   ├── transcript-view.tsx         # chat-style transcript
│   ├── score-card.tsx              # composite score + bars
│   ├── security-card.tsx           # risk + threats + PII
│   ├── summary-card.tsx            # one-liner + topics + actions
│   ├── voice-card.tsx              # voice catalog card
│   ├── search-results.tsx          # search result with highlight
│   └── stats-row.tsx               # 4-card stats row
```
