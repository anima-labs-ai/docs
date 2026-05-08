# Voice Calls Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a comprehensive Voice Calls dashboard in the Anima console, covering call history, transcripts, recordings, summaries, scoring, security, search, analytics, and voice catalog.

**Architecture:** New pages under `/phone/calls` and `/phone/voices` in the existing Next.js 15 App Router `(dashboard)` layout group. Shared voice components in `src/components/voice/`. All data fetched via existing oRPC contract (`orpc.voice.*`) with TanStack Query.

**Tech Stack:** Next.js 15, React 19, TypeScript 5.7, Tailwind CSS 4 (CSS custom properties), oRPC + TanStack Query, Recharts, Framer Motion, Lucide React, Clerk auth.

**Spec:** `docs/superpowers/specs/2026-04-04-voice-calls-dashboard-design.md`

---

## File Structure

All paths relative to `anima/apps/console/src/`.

### New Files

| File | Responsibility |
|------|---------------|
| `components/voice/call-tabs.tsx` | Secondary tab nav (Calls / Search / Analytics / Voices) |
| `components/voice/call-badges.tsx` | Direction, tier, state, score badge components |
| `components/voice/call-table.tsx` | Sortable call list table with filters + pagination |
| `components/voice/recording-player.tsx` | Audio player with custom play/pause/seek/download |
| `components/voice/transcript-view.tsx` | Chat-style transcript with clickable timestamps, speaker filter |
| `components/voice/score-card.tsx` | Composite score display + sub-score bars |
| `components/voice/security-card.tsx` | Risk score + threats list + PII list |
| `components/voice/summary-card.tsx` | One-liner + topics + action items + decisions |
| `components/voice/voice-card.tsx` | Voice catalog card with audio preview |
| `components/voice/search-results.tsx` | Search result card with snippet highlighting |
| `components/voice/stats-row.tsx` | 3-card stats row for analytics page |
| `app/(dashboard)/phone/calls/page.tsx` | Call list page |
| `app/(dashboard)/phone/calls/loading.tsx` | Call list skeleton |
| `app/(dashboard)/phone/calls/[id]/page.tsx` | Call detail page (tabbed) |
| `app/(dashboard)/phone/calls/[id]/loading.tsx` | Call detail skeleton |
| `app/(dashboard)/phone/calls/search/page.tsx` | Semantic search page |
| `app/(dashboard)/phone/calls/analytics/page.tsx` | Analytics page with charts |
| `app/(dashboard)/phone/voices/page.tsx` | Voice catalog grid |
| `app/(dashboard)/phone/voices/loading.tsx` | Voice catalog skeleton |

### Modified Files

| File | Change |
|------|--------|
| `components/dashboard/config.ts` | Add grouped nav type with `children` for Phone |
| `components/dashboard/sidebar.tsx` | Handle grouped nav items with collapsible children |
| `components/dashboard/header.tsx` | Handle breadcrumb for grouped + nested routes |
| `lib/date.ts` | Add `formatDuration()` helper |

---

## [✔] Task 1: Navigation — Config & Sidebar Group

Update the sidebar config to support grouped nav items. The Phone item becomes a collapsible group with "Numbers" and "Voice Calls" children.

**Files:**
- Modify: `components/dashboard/config.ts`
- Modify: `components/dashboard/sidebar.tsx`
- Modify: `components/dashboard/header.tsx`

- [ ] **Step 1: Update nav config with group type**

In `components/dashboard/config.ts`, change the config to support both flat items and grouped items:

```typescript
export const dashboardWorkspaceName = "Anima";

export type NavItem = { href: string; label: string };
export type NavGroup = { label: string; children: NavItem[] };
export type NavEntry = NavItem | NavGroup;

export function isNavGroup(entry: NavEntry): entry is NavGroup {
  return "children" in entry;
}

export const dashboardNavConfig: NavEntry[] = [
  { href: "/", label: "Overview" },
  { href: "/agents", label: "Agents" },
  { href: "/inboxes", label: "Inboxes" },
  { href: "/messages", label: "Messages" },
  {
    label: "Phone",
    children: [
      { href: "/phone", label: "Numbers" },
      { href: "/phone/calls", label: "Voice Calls" },
    ],
  },
  { href: "/vault", label: "Vault" },
  { href: "/domains", label: "Domains" },
  { href: "/webhooks", label: "Webhooks" },
  { href: "/security", label: "Security" },
  { href: "/api-keys", label: "API Keys" },
  { href: "/settings", label: "Settings" },
];
```

**Note on type narrowing:** The existing config uses `as const` which provides literal types for `iconMap` keys. Since we now have a union type (`NavEntry[]`), the `iconMap` in `sidebar.tsx` must change its key type from `(typeof dashboardNavConfig)[number]["label"]` to `Record<string, typeof LayoutDashboard>`. This is addressed in Step 2.

- [ ] **Step 2: Update sidebar to render grouped items**

In `components/dashboard/sidebar.tsx`, the current code maps `dashboardNavConfig` into `dashboardNavItems` (a flat `NavItem[]` array). This needs to change to handle both flat items and groups.

Key changes:
1. Import `NavEntry, NavGroup, isNavGroup` from config
2. Remove the old `dashboardNavItems` export (it was a flat array)
3. Add state for expanded groups: `const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(["Phone"]))`
4. In the `<nav>` iteration, check `isNavGroup(entry)`:
   - If group: render a collapsible section with the group label and a chevron icon. The group is "active" if any child route matches `pathname` (use `pathname.startsWith(child.href)`). Render children as indented links.
   - If flat item: render exactly as before (existing link/button logic unchanged)
5. The `iconMap` needs to map the group label "Phone" to the `Phone` icon (already does), and also map "Numbers" → `Phone`, "Voice Calls" → `PhoneCall` (import from lucide-react)
6. Feature state: `getFeatureState("Phone")` already returns `{ isEnabled: isPhoneFeatureEnabled(), featureKey: "phone" }`. Apply this to the entire group — if phone feature is disabled, show ComingSoonChip on the group header and don't render children.

The group rendering (when expanded and sidebar is expanded):
```tsx
// Inside the nav iteration for a group entry:
<div key={group.label}>
  <button
    type="button"
    onClick={() => toggleGroup(group.label)}
    className={`w-full group relative flex items-center justify-between transition-colors ${
      expanded
        ? "px-3 py-2 font-mono text-xs font-medium uppercase tracking-wider"
        : "justify-center p-2.5"
    } ${
      isGroupActive ? "text-accent" : "text-fg-muted hover:bg-bg-elevated hover:text-fg"
    }`}
  >
    <div className="flex items-center">
      <Icon className={`h-5 w-5 shrink-0 ${expanded ? "mr-3" : ""} ${isGroupActive ? "text-accent" : "text-fg-dimmer"}`} />
      {expanded && group.label}
    </div>
    {expanded && (
      <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
    )}
  </button>
  {expanded && isOpen && (
    <div className="ml-8 space-y-0.5">
      {group.children.map((child) => {
        const ChildIcon = childIconMap[child.label];
        const isActive = pathname === child.href || (child.href !== "/" && pathname.startsWith(child.href + "/"));
        return (
          <Link key={child.href} href={child.href} className={`flex items-center gap-2 px-3 py-1.5 font-mono text-xs uppercase tracking-wider ${isActive ? "text-accent" : "text-fg-muted hover:text-fg"}`}>
            {ChildIcon && <ChildIcon className="h-3.5 w-3.5" />}
            {child.label}
            {isActive && <div className="absolute left-0 top-0 h-full w-1 bg-accent" />}
          </Link>
        );
      })}
    </div>
  )}
</div>
```

When sidebar is collapsed: show only the group icon (Phone). Clicking it could expand the sidebar, or show a tooltip with children.

- [ ] **Step 3: Update header breadcrumb logic**

In `components/dashboard/header.tsx`, the current code does a simple `find` on `dashboardNavConfig` to get the page title. This needs to handle nested routes:

```typescript
import { dashboardNavConfig, isNavGroup } from "./config";

function getPageTitle(pathname: string): string {
  for (const entry of dashboardNavConfig) {
    if (isNavGroup(entry)) {
      // Sort children by href length descending so more-specific routes match first
      // e.g. "/phone/calls" matches before "/phone" for path "/phone/calls/abc123"
      const sorted = [...entry.children].sort((a, b) => b.href.length - a.href.length);
      for (const child of sorted) {
        if (pathname === child.href || pathname.startsWith(child.href + "/")) {
          return child.label;
        }
      }
    } else if (entry.href === pathname) {
      return entry.label;
    }
  }
  return "Dashboard";
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/console/src/components/dashboard/config.ts apps/console/src/components/dashboard/sidebar.tsx apps/console/src/components/dashboard/header.tsx
git commit -m "feat(console): add grouped Phone nav with Numbers + Voice Calls"
```

---

## [✔] Task 2: Shared Components — Badges & Tab Nav

Create the foundational shared components used across all voice pages.

**Files:**
- Create: `components/voice/call-badges.tsx`
- Create: `components/voice/call-tabs.tsx`
- Modify: `lib/date.ts` (add `formatDuration`)

- [ ] **Step 1: Add formatDuration to date utils**

In `lib/date.ts`, add:

```typescript
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}
```

- [ ] **Step 2: Create call-badges.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";

export function DirectionBadge({ direction }: { direction: "INBOUND" | "OUTBOUND" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 font-mono text-xs uppercase",
        direction === "INBOUND" ? "bg-info-muted text-info" : "bg-bg-elevated text-fg-muted",
      )}
    >
      {direction}
    </span>
  );
}

export function TierBadge({ tier }: { tier: "basic" | "premium" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 font-mono text-xs uppercase",
        tier === "premium" ? "bg-accent-muted text-accent" : "bg-bg-elevated text-fg-muted",
      )}
    >
      {tier}
    </span>
  );
}

export function StateBadge({ state }: { state: string }) {
  const color =
    state === "ACTIVE" || state === "active"
      ? "bg-accent-muted text-accent"
      : state === "FAILED" || state === "failed"
        ? "bg-error-muted text-error"
        : "bg-bg-elevated text-fg-muted";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 font-mono text-xs uppercase", color)}>
      {state}
    </span>
  );
}

export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return <span className="text-fg-dimmer">—</span>;
  const color = score >= 80 ? "text-accent" : score >= 60 ? "text-warning" : "text-error";
  return <span className={cn("font-mono text-sm font-medium", color)}>{score}</span>;
}
```

- [ ] **Step 3: Create call-tabs.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/phone/calls", label: "Calls" },
  { href: "/phone/calls/search", label: "Search" },
  { href: "/phone/calls/analytics", label: "Analytics" },
  { href: "/phone/voices", label: "Voices" },
];

export function CallTabs() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-0 border-b border-border">
      {tabs.map((tab) => {
        const isActive =
          tab.href === "/phone/calls"
            ? pathname === "/phone/calls" || pathname.startsWith("/phone/calls/") && !tabs.slice(1).some((t) => pathname.startsWith(t.href))
            : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "px-4 py-2.5 font-mono text-xs uppercase tracking-wider transition-colors",
              isActive
                ? "border-b-2 border-accent text-accent"
                : "text-fg-muted hover:text-fg",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
```

Note: The "Calls" tab should be active for `/phone/calls` and `/phone/calls/[id]` but NOT for `/phone/calls/search` or `/phone/calls/analytics`. The logic above handles this by checking if the pathname matches any other tab first.

- [ ] **Step 4: Commit**

```bash
git add apps/console/src/components/voice/ apps/console/src/lib/date.ts
git commit -m "feat(console): add voice badge components and tab nav"
```

---

## [✔] Task 3: Call List Page

Build the main call list table with filters, sorting, pagination, and loading/empty states.

**Files:**
- Create: `components/voice/call-table.tsx`
- Create: `app/(dashboard)/phone/calls/page.tsx`
- Create: `app/(dashboard)/phone/calls/loading.tsx`

- [ ] **Step 1: Create call-table.tsx**

This component handles the sortable table with inline sort state. It receives the call data and agent list as props.

**Note:** The spec lists a "Score" column, but `CallSchema` does not include a composite score field. Adding it would require a secondary batch query (`getScore` per call) which is expensive. Defer the Score column — it can be added later if the API adds a `compositeScore` field to `ListCallsOutput`.

```typescript
"use client";

import { DirectionBadge, ScoreBadge, StateBadge, TierBadge } from "@/components/voice/call-badges";
import { formatDuration } from "@/lib/date";
import { formatRelativeTime } from "@/lib/date";
import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";
import { Phone } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

type Call = {
  id: string;
  agentId: string;
  direction: "INBOUND" | "OUTBOUND";
  tier: "basic" | "premium";
  state: string;
  from: string;
  to: string;
  durationSeconds: number | null;
  startedAt: string;
  createdAt: string;
};

type SortKey = "direction" | "tier" | "state" | "durationSeconds" | "startedAt";
type SortDir = "asc" | "desc";

export function CallTable({
  calls,
  agents,
}: {
  calls: Call[];
  agents: { id: string; name: string }[];
}) {
  const [sortKey, setSortKey] = useState<SortKey>("startedAt");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("desc"); }
  };

  const agentMap = useMemo(() => new Map(agents.map((a) => [a.id, a.name])), [agents]);

  const sorted = useMemo(() => {
    const arr = [...calls];
    arr.sort((a, b) => {
      let cmp = 0;
      const av = a[sortKey], bv = b[sortKey];
      if (av == null && bv == null) cmp = 0;
      else if (av == null) cmp = 1;
      else if (bv == null) cmp = -1;
      else if (typeof av === "string") cmp = av.localeCompare(bv as string);
      else cmp = (av as number) - (bv as number);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return arr;
  }, [calls, sortKey, sortDir]);

  const SortHeader = ({ label, col }: { label: string; col: SortKey }) => (
    <th
      className="px-6 py-3 font-medium cursor-pointer select-none hover:text-fg"
      onClick={() => toggleSort(col)}
    >
      {label} {sortKey === col && (sortDir === "asc" ? "↑" : "↓")}
    </th>
  );

  if (calls.length === 0) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center p-8 text-center border border-border bg-bg-surface">
        <div className="mb-4 bg-bg-elevated p-3"><Phone className="h-6 w-6 text-fg-dimmer" /></div>
        <h3 className="font-mono text-sm uppercase tracking-wider text-fg">No calls yet</h3>
        <p className="mt-1 text-sm text-fg-muted">Create your first call via the SDK or API.</p>
      </div>
    );
  }

  return (
    <div className="border border-border bg-bg-surface overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-bg-elevated font-mono text-xs uppercase tracking-wider text-fg-muted">
            <tr>
              <th className="px-6 py-3 font-medium">Call ID</th>
              <SortHeader label="Direction" col="direction" />
              <th className="px-6 py-3 font-medium">From → To</th>
              <th className="px-6 py-3 font-medium">Agent</th>
              <SortHeader label="Tier" col="tier" />
              <SortHeader label="State" col="state" />
              <SortHeader label="Duration" col="durationSeconds" />
              <SortHeader label="Date" col="startedAt" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            <AnimatePresence initial={false}>
              {sorted.map((call) => (
                <motion.tr
                  key={call.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="group hover:bg-bg-elevated"
                >
                  <td className="px-6 py-4">
                    <Link href={`/phone/calls/${call.id}`} className="font-mono text-xs text-accent hover:underline">
                      {call.id.slice(0, 12)}…
                    </Link>
                  </td>
                  <td className="px-6 py-4"><DirectionBadge direction={call.direction} /></td>
                  <td className="px-6 py-4 text-sm text-fg-muted">{call.from} → {call.to}</td>
                  <td className="px-6 py-4">
                    <Link href={`/agents/${call.agentId}`} className="text-accent hover:underline text-sm">
                      {agentMap.get(call.agentId) || call.agentId.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-6 py-4"><TierBadge tier={call.tier} /></td>
                  <td className="px-6 py-4"><StateBadge state={call.state} /></td>
                  <td className="px-6 py-4 font-mono text-xs text-fg-muted">{formatDuration(call.durationSeconds)}</td>
                  <td className="px-6 py-4 text-xs text-fg-muted" title={call.startedAt}>
                    {formatRelativeTime(call.startedAt)}
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create the call list page**

`app/(dashboard)/phone/calls/page.tsx`:

```typescript
"use client";

import { CallTabs } from "@/components/voice/call-tabs";
import { CallTable } from "@/components/voice/call-table";
import { isPhoneFeatureEnabled } from "@/lib/features";
import { FeatureLockedState } from "@/components/dashboard/feature-locked-state";
import { orpc } from "@/lib/orpc";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";

export default function CallListPage() {
  if (!isPhoneFeatureEnabled()) {
    return <FeatureLockedState title="Voice Calls" description="Phone features are not enabled." />;
  }

  const [agentFilter, setAgentFilter] = useState("");
  const [directionFilter, setDirectionFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data } = useSuspenseQuery(
    orpc.voice.listCalls.queryOptions({
      input: {
        limit,
        offset: page * limit,
        ...(agentFilter ? { agentId: agentFilter } : {}),
        ...(directionFilter ? { direction: directionFilter as "INBOUND" | "OUTBOUND" } : {}),
        ...(stateFilter ? { state: stateFilter } : {}),
      },
    }),
  );

  const { data: agentData } = useSuspenseQuery(
    orpc.agent.list.queryOptions({ input: { limit: 100 } }),
  );

  const agents = agentData.items.map((a) => ({ id: a.id, name: a.name }));
  const totalPages = Math.ceil(data.total / limit);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Voice Calls</h1>
        <p className="text-sm text-fg-muted">Monitor and inspect voice calls across your agents.</p>
      </div>

      <CallTabs />

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={agentFilter}
          onChange={(e) => { setAgentFilter(e.target.value); setPage(0); }}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All Agents</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>

        <select
          value={directionFilter}
          onChange={(e) => { setDirectionFilter(e.target.value); setPage(0); }}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All Directions</option>
          <option value="INBOUND">Inbound</option>
          <option value="OUTBOUND">Outbound</option>
        </select>

        <select
          value={stateFilter}
          onChange={(e) => { setStateFilter(e.target.value); setPage(0); }}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All States</option>
          <option value="active">Active</option>
          <option value="ended">Ended</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <CallTable calls={data.calls} agents={agents} />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs text-fg-muted">
            Page {page + 1} of {totalPages} ({data.total} calls)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="border border-border px-3 py-1 font-mono text-xs text-fg hover:bg-bg-elevated disabled:opacity-50"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="border border-border px-3 py-1 font-mono text-xs text-fg hover:bg-bg-elevated disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create loading skeleton**

`app/(dashboard)/phone/calls/loading.tsx`:

```typescript
export default function Loading() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Voice Calls</h1>
        <p className="text-sm text-fg-muted">Monitor and inspect voice calls across your agents.</p>
      </div>
      <div className="h-10 w-64 animate-pulse bg-bg-elevated" />
      <div className="flex gap-3">
        <div className="h-8 w-32 animate-pulse bg-bg-elevated" />
        <div className="h-8 w-32 animate-pulse bg-bg-elevated" />
        <div className="h-8 w-32 animate-pulse bg-bg-elevated" />
      </div>
      <div className="border border-border bg-bg-surface overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-bg-elevated font-mono text-xs uppercase tracking-wider text-fg-muted">
            <tr>
              <th className="px-6 py-3 font-medium">Call ID</th>
              <th className="px-6 py-3 font-medium">Direction</th>
              <th className="px-6 py-3 font-medium">From → To</th>
              <th className="px-6 py-3 font-medium">Agent</th>
              <th className="px-6 py-3 font-medium">Tier</th>
              <th className="px-6 py-3 font-medium">State</th>
              <th className="px-6 py-3 font-medium">Duration</th>
              <th className="px-6 py-3 font-medium">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <tr key={i} className="animate-pulse">
                <td className="px-6 py-4"><div className="h-4 w-24 bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-5 w-16 rounded-full bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-4 w-40 bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-4 w-20 bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-5 w-16 rounded-full bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-5 w-14 rounded-full bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-4 w-14 bg-bg-elevated" /></td>
                <td className="px-6 py-4"><div className="h-4 w-16 bg-bg-elevated" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/console/src/components/voice/call-table.tsx apps/console/src/app/\(dashboard\)/phone/calls/
git commit -m "feat(console): add call list page with filters, sorting, pagination"
```

---

## [✔] Task 4: Call Detail — Fixed Header + Overview Tab

Build the call detail page with the fixed header (recording player, metadata), and the Overview tab.

**Files:**
- Create: `components/voice/recording-player.tsx`
- Create: `components/voice/summary-card.tsx`
- Create: `app/(dashboard)/phone/calls/[id]/page.tsx`
- Create: `app/(dashboard)/phone/calls/[id]/loading.tsx`

- [ ] **Step 1: Create recording-player.tsx**

```typescript
"use client";

import { Download, Pause, Play } from "lucide-react";
import { useRef, useState } from "react";

export function RecordingPlayer({
  downloadUrl,
  durationSeconds,
  onTimeUpdate,
}: {
  downloadUrl: string | null;
  durationSeconds: number | null;
  onTimeUpdate?: (currentTime: number) => void;
}) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(durationSeconds || 0);

  if (!downloadUrl) {
    return (
      <div className="flex items-center gap-3 rounded bg-bg-elevated px-4 py-3 text-sm text-fg-dimmer">
        Recording not available
      </div>
    );
  }

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) audio.pause();
    else audio.play();
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(audio.currentTime);
    onTimeUpdate?.(audio.currentTime);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = Number(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${String(sec).padStart(2, "0")}`;
  };

  // Public method for seeking from transcript timestamps
  const seekTo = (time: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = time;
    setCurrentTime(time);
    if (!isPlaying) { audio.play(); setIsPlaying(true); }
  };

  return (
    <div className="flex items-center gap-3 rounded bg-bg-elevated px-4 py-3">
      <audio
        ref={audioRef}
        src={downloadUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={() => {
          if (audioRef.current) setDuration(audioRef.current.duration);
        }}
        onEnded={() => setIsPlaying(false)}
      />
      <button
        type="button"
        onClick={togglePlay}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-bg hover:bg-accent-hover"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
      </button>
      <input
        type="range"
        min={0}
        max={duration}
        value={currentTime}
        onChange={handleSeek}
        className="flex-1 accent-accent"
        aria-label="Seek"
      />
      <span className="font-mono text-xs text-fg-muted whitespace-nowrap">
        {fmt(currentTime)} / {fmt(duration)}
      </span>
      <a
        href={downloadUrl}
        download
        className="p-1 text-fg-dimmer hover:text-fg"
        title="Download recording"
      >
        <Download className="h-4 w-4" />
      </a>
    </div>
  );
}
```

Note: To allow transcript timestamps to control the player, the parent page will use a ref or callback pattern. The `seekTo` function above is internal — the parent should pass a ref and call `audioRef.current.currentTime = seconds` directly. Alternatively, lift `currentTime` into page-level state. The simplest approach: pass a `seekToRef` callback from parent that stores the seek function.

- [ ] **Step 2: Create summary-card.tsx**

```typescript
"use client";

export function SummaryCard({
  summary,
}: {
  summary: {
    oneLiner: string;
    topics: string[];
    actionItems: { text: string; owner: string | null }[];
    decisions: string[];
    openQuestions: string[];
    nextSteps: string[];
    intent: string;
    outcome: string;
  } | null;
}) {
  if (!summary) {
    return (
      <div className="border border-border bg-bg-surface p-6 text-sm text-fg-muted">
        Summary will be available after the call ends.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* One-liner */}
      <div className="border border-border bg-bg-surface p-4">
        <p className="text-base text-fg">{summary.oneLiner}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {summary.topics.map((topic) => (
            <span key={topic} className="rounded-full bg-bg-elevated px-2.5 py-0.5 font-mono text-xs text-fg-muted">
              {topic}
            </span>
          ))}
        </div>
        <div className="mt-2 flex gap-2">
          <span className="rounded-full bg-info-muted px-2 py-0.5 font-mono text-xs text-info">{summary.intent}</span>
          <span className="rounded-full bg-accent-muted px-2 py-0.5 font-mono text-xs text-accent">{summary.outcome}</span>
        </div>
      </div>

      {/* Action Items */}
      {summary.actionItems.length > 0 && (
        <Section title="Action Items">
          <ul className="space-y-1.5">
            {summary.actionItems.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-fg">
                <span className="text-fg-dimmer">•</span>
                <span>{item.text}{item.owner && <span className="ml-1 text-fg-muted">({item.owner})</span>}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Decisions */}
      {summary.decisions.length > 0 && (
        <Section title="Decisions">
          <ul className="space-y-1 text-sm text-fg">
            {summary.decisions.map((d, i) => (
              <li key={i} className="flex items-start gap-2"><span className="text-fg-dimmer">•</span>{d}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Open Questions */}
      {summary.openQuestions.length > 0 && (
        <Section title="Open Questions">
          <ul className="space-y-1 text-sm text-fg">
            {summary.openQuestions.map((q, i) => (
              <li key={i} className="flex items-start gap-2"><span className="text-fg-dimmer">•</span>{q}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Next Steps */}
      {summary.nextSteps.length > 0 && (
        <Section title="Next Steps">
          <ul className="space-y-1 text-sm text-fg">
            {summary.nextSteps.map((s, i) => (
              <li key={i} className="flex items-start gap-2"><span className="text-fg-dimmer">•</span>{s}</li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-border bg-bg-surface p-4">
      <h3 className="mb-2 font-mono text-xs uppercase tracking-wider text-fg-dimmer">{title}</h3>
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Create call detail page**

`app/(dashboard)/phone/calls/[id]/page.tsx`:

This is the largest page. It loads all call data in parallel and renders three tabs: Overview, Transcript, Intelligence.

```typescript
"use client";

import { DirectionBadge, StateBadge, TierBadge } from "@/components/voice/call-badges";
import { RecordingPlayer } from "@/components/voice/recording-player";
import { SummaryCard } from "@/components/voice/summary-card";
import { formatDuration, formatRelativeTime } from "@/lib/date";
import { isPhoneFeatureEnabled } from "@/lib/features";
import { FeatureLockedState } from "@/components/dashboard/feature-locked-state";
import { orpc } from "@/lib/orpc";
import { cn } from "@/lib/utils";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { ArrowLeft, Copy } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { useState } from "react";

// Transcript and Intelligence tabs will be added in Tasks 5 and 6.
// For now, stub them with placeholder content.

export default function CallDetailPage() {
  if (!isPhoneFeatureEnabled()) {
    return <FeatureLockedState title="Call Detail" description="Phone features are not enabled." />;
  }

  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeTab = searchParams.get("tab") || "overview";

  // Required data — always exists
  const { data: call } = useSuspenseQuery(
    orpc.voice.getCall.queryOptions({ input: { callId: id } }),
  );

  // Optional data — may 404 if not yet generated. Use useQuery (not useSuspenseQuery)
  // so the page renders without blocking on these.
  const { data: recording } = useQuery({
    ...orpc.voice.getRecording.queryOptions({ input: { callId: id } }),
    retry: false,
  });
  const { data: summary } = useQuery({
    ...orpc.voice.getSummary.queryOptions({ input: { callId: id } }),
    retry: false,
  });

  const setTab = (tab: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`/phone/calls/${id}?${params.toString()}`);
  };

  const [copied, setCopied] = useState(false);
  const copyId = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link href="/phone/calls" className="inline-flex items-center gap-1 font-mono text-xs text-fg-muted hover:text-fg">
        <ArrowLeft className="h-3.5 w-3.5" /> Voice Calls
      </Link>

      {/* Header */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={copyId} className="flex items-center gap-1 font-mono text-sm text-fg hover:text-accent" title="Copy Call ID">
            {id} <Copy className="h-3.5 w-3.5 text-fg-dimmer" />
          </button>
          {copied && <span className="font-mono text-xs text-accent">Copied!</span>}
          <DirectionBadge direction={call.direction} />
          <TierBadge tier={call.tier} />
          <StateBadge state={call.state} />
        </div>

        {/* Recording player */}
        <RecordingPlayer
          downloadUrl={recording?.downloadUrl ?? null}
          durationSeconds={recording?.durationSeconds ?? call.durationSeconds}
        />

        {/* Metadata row */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <MetaCard label="From → To" value={`${call.from} → ${call.to}`} />
          <MetaCard label="Agent" value={call.agentId} link={`/agents/${call.agentId}`} />
          <MetaCard label="Duration" value={formatDuration(call.durationSeconds)} />
          <MetaCard label="Started" value={formatRelativeTime(call.startedAt)} title={call.startedAt} />
          {call.endReason && <MetaCard label="End Reason" value={call.endReason} />}
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex gap-0 border-b border-border">
        {["overview", "transcript", "intelligence"].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setTab(tab)}
            className={cn(
              "px-4 py-2.5 font-mono text-xs uppercase tracking-wider transition-colors",
              activeTab === tab ? "border-b-2 border-accent text-accent" : "text-fg-muted hover:text-fg",
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "overview" && <SummaryCard summary={summary} />}
      {activeTab === "transcript" && <TranscriptTabPlaceholder callId={id} />}
      {activeTab === "intelligence" && <IntelligenceTabPlaceholder callId={id} />}
    </div>
  );
}

function MetaCard({ label, value, link, title }: { label: string; value: string; link?: string; title?: string }) {
  return (
    <div className="border border-border bg-bg-surface p-3">
      <div className="font-mono text-[10px] uppercase tracking-wider text-fg-dimmer">{label}</div>
      {link ? (
        <Link href={link} className="text-sm text-accent hover:underline" title={title}>{value}</Link>
      ) : (
        <div className="text-sm text-fg truncate" title={title || value}>{value}</div>
      )}
    </div>
  );
}

function TranscriptTabPlaceholder({ callId }: { callId: string }) {
  return <div className="p-8 text-center text-sm text-fg-muted">Transcript tab — coming in next task.</div>;
}

function IntelligenceTabPlaceholder({ callId }: { callId: string }) {
  return <div className="p-8 text-center text-sm text-fg-muted">Intelligence tab — coming in next task.</div>;
}
```

Use `recording ?? null` and `summary ?? null` when passing to child components.

- [ ] **Step 4: Create call detail loading skeleton**

`app/(dashboard)/phone/calls/[id]/loading.tsx`:

```typescript
export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="h-4 w-24 animate-pulse bg-bg-elevated" />
      <div className="space-y-3">
        <div className="flex gap-2">
          <div className="h-5 w-48 animate-pulse bg-bg-elevated" />
          <div className="h-5 w-16 rounded-full animate-pulse bg-bg-elevated" />
          <div className="h-5 w-16 rounded-full animate-pulse bg-bg-elevated" />
        </div>
        <div className="h-14 w-full animate-pulse bg-bg-elevated rounded" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-14 animate-pulse bg-bg-elevated border border-border" />
          ))}
        </div>
      </div>
      <div className="h-10 w-64 animate-pulse bg-bg-elevated" />
      <div className="space-y-3">
        <div className="h-24 w-full animate-pulse bg-bg-elevated" />
        <div className="h-16 w-full animate-pulse bg-bg-elevated" />
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add apps/console/src/components/voice/recording-player.tsx apps/console/src/components/voice/summary-card.tsx apps/console/src/app/\(dashboard\)/phone/calls/\[id\]/
git commit -m "feat(console): add call detail page with recording player and overview tab"
```

---

## [✔] Task 5: Call Detail — Transcript Tab

Replace the transcript placeholder with the full conversation view.

**Files:**
- Create: `components/voice/transcript-view.tsx`
- Modify: `app/(dashboard)/phone/calls/[id]/page.tsx` (replace placeholder)

- [ ] **Step 1: Create transcript-view.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";
import { Copy, Filter } from "lucide-react";
import { useMemo, useState } from "react";

type Segment = {
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
  isFinal: boolean;
};

export function TranscriptView({
  segments,
  onTimestampClick,
}: {
  segments: Segment[];
  onTimestampClick?: (seconds: number) => void;
}) {
  const [speakerFilter, setSpeakerFilter] = useState<string>("all");
  const [showInterim, setShowInterim] = useState(false);

  const speakers = useMemo(() => {
    const set = new Set(segments.map((s) => s.speaker));
    return Array.from(set);
  }, [segments]);

  const filtered = useMemo(() => {
    let result = segments;
    if (!showInterim) result = result.filter((s) => s.isFinal);
    if (speakerFilter !== "all") result = result.filter((s) => s.speaker === speakerFilter);
    return result;
  }, [segments, speakerFilter, showInterim]);

  const fmt = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  const copyTranscript = () => {
    const text = filtered
      .map((s) => `[${fmt(s.startTime)}] ${s.speaker}: ${s.text}`)
      .join("\n");
    navigator.clipboard.writeText(text);
  };

  if (segments.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-fg-muted">
        No transcript segments recorded.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-fg-dimmer" />
          <select
            value={speakerFilter}
            onChange={(e) => setSpeakerFilter(e.target.value)}
            className="border border-border bg-bg-surface px-2 py-1 font-mono text-xs text-fg focus:border-accent focus:outline-none"
          >
            <option value="all">All Speakers</option>
            {speakers.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 font-mono text-xs text-fg-muted">
            <input
              type="checkbox"
              checked={showInterim}
              onChange={(e) => setShowInterim(e.target.checked)}
              className="accent-accent"
            />
            Show interim
          </label>
        </div>
        <button
          type="button"
          onClick={copyTranscript}
          className="flex items-center gap-1 px-2 py-1 font-mono text-xs text-fg-muted hover:text-fg"
        >
          <Copy className="h-3.5 w-3.5" /> Copy
        </button>
      </div>

      {/* Segments */}
      <div className="space-y-1 border border-border bg-bg-surface p-4">
        {filtered.map((segment, i) => (
          <div key={i} className={cn("group", segment.confidence < 0.7 && "opacity-60")}>
            <button
              type="button"
              onClick={() => onTimestampClick?.(segment.startTime)}
              className="font-mono text-[10px] text-fg-dimmer hover:text-accent cursor-pointer"
            >
              {fmt(segment.startTime)}
            </button>
            <div className={cn("ml-0 mt-0.5 mb-3", segment.confidence < 0.7 && "underline decoration-dotted")}>
              <span className={cn(
                "font-mono text-xs mr-2",
                segment.speaker === "agent" ? "text-info" : "text-fg-muted",
              )}>
                {segment.speaker}:
              </span>
              <span className="text-sm text-fg">{segment.text}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Wire transcript into call detail page**

In `app/(dashboard)/phone/calls/[id]/page.tsx`:

1. Import `TranscriptView` and add a `useQuery` for transcript data:
```typescript
import { TranscriptView } from "@/components/voice/transcript-view";

// Inside the component, after other queries:
const { data: transcript } = useQuery({
  ...orpc.voice.getTranscript.queryOptions({ input: { callId: id } }),
  retry: false,
});
```

2. Replace `TranscriptTabPlaceholder` with:
```typescript
{activeTab === "transcript" && (
  <TranscriptView
    segments={transcript?.segments ?? []}
    onTimestampClick={(seconds) => {
      // Seek the recording player — connect via ref or state
      const audio = document.querySelector("audio");
      if (audio) { audio.currentTime = seconds; audio.play(); }
    }}
  />
)}
```

- [ ] **Step 3: Commit**

```bash
git add apps/console/src/components/voice/transcript-view.tsx apps/console/src/app/\(dashboard\)/phone/calls/\[id\]/page.tsx
git commit -m "feat(console): add transcript tab with speaker filter and timestamp sync"
```

---

## [✔] Task 6: Call Detail — Intelligence Tab

Replace the intelligence placeholder with score card and security card.

**Files:**
- Create: `components/voice/score-card.tsx`
- Create: `components/voice/security-card.tsx`
- Modify: `app/(dashboard)/phone/calls/[id]/page.tsx` (replace placeholder)

- [ ] **Step 1: Create score-card.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";

type ScoreData = {
  compositeScore: number;
  resolutionScore: number;
  sentimentScore: number;
  complianceScore: number;
  efficiencyScore: number;
  engagementScore: number;
  latencyScore: number;
  metrics: Record<string, unknown>;
};

const subScores: { key: keyof Omit<ScoreData, "compositeScore" | "metrics" | "callId" | "scoredAt">; label: string }[] = [
  { key: "resolutionScore", label: "Resolution" },
  { key: "sentimentScore", label: "Sentiment" },
  { key: "complianceScore", label: "Compliance" },
  { key: "efficiencyScore", label: "Efficiency" },
  { key: "engagementScore", label: "Engagement" },
  { key: "latencyScore", label: "Latency" },
];

function scoreColor(score: number) {
  if (score >= 80) return "text-accent bg-accent";
  if (score >= 60) return "text-warning bg-warning";
  return "text-error bg-error";
}

function formatMetricValue(key: string, value: unknown): string {
  if (typeof value === "number") {
    if (key.toLowerCase().includes("ratio")) return `${value.toFixed(1)}:1`;
    if (key.toLowerCase().includes("rate") || key.toLowerCase().includes("percent")) return `${(value * 100).toFixed(0)}%`;
    if (key.toLowerCase().includes("latency") || key.toLowerCase().includes("duration") || key.toLowerCase().includes("monologue") || key.toLowerCase().includes("deadair")) return `${value.toFixed(1)}s`;
    return String(value);
  }
  return String(value ?? "—");
}

function humanizeKey(key: string): string {
  return key.replace(/([A-Z])/g, " $1").replace(/^./, (s) => s.toUpperCase()).trim();
}

export function ScoreCard({ score }: { score: ScoreData | null }) {
  if (!score) {
    return (
      <div className="border border-border bg-bg-surface p-6 text-sm text-fg-muted">
        Scoring will be available after the call ends and transcript is processed.
      </div>
    );
  }

  const compositeColor = score.compositeScore >= 80 ? "text-accent" : score.compositeScore >= 60 ? "text-warning" : "text-error";

  return (
    <div className="border border-border bg-bg-surface p-4 space-y-4">
      <div className="flex items-baseline gap-1">
        <span className={cn("font-mono text-5xl font-bold", compositeColor)}>{score.compositeScore}</span>
        <span className="font-mono text-lg text-fg-dimmer">/100</span>
      </div>

      {/* Sub-scores */}
      <div className="space-y-2">
        {subScores.map(({ key, label }) => {
          const val = score[key] as number;
          const color = scoreColor(val);
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="w-24 font-mono text-xs text-fg-muted">{label}</span>
              <div className="flex-1 h-2 bg-bg-elevated rounded-full overflow-hidden">
                <div className={cn("h-full rounded-full", color.split(" ")[1])} style={{ width: `${val}%` }} />
              </div>
              <span className={cn("w-8 text-right font-mono text-xs", color.split(" ")[0])}>{val}</span>
            </div>
          );
        })}
      </div>

      {/* Metrics */}
      {Object.keys(score.metrics).length > 0 && (
        <div className="border-t border-border pt-3">
          <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-fg-dimmer">Metrics</h4>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {Object.entries(score.metrics).map(([key, value]) => (
              <div key={key} className="flex justify-between text-xs">
                <span className="text-fg-muted">{humanizeKey(key)}</span>
                <span className="font-mono text-fg">{formatMetricValue(key, value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create security-card.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";

type SecurityData = {
  threats: { type: string; severity: string; description: string; speaker: string }[];
  piiDetected: { type: string; speaker: string; redacted: string }[];
  compliancePass: boolean;
  riskScore: number;
};

const severityColor: Record<string, string> = {
  critical: "bg-error-muted text-error",
  high: "bg-error-muted text-error",
  medium: "bg-warning-muted text-warning",
  low: "bg-bg-elevated text-fg-muted",
};

export function SecurityCard({ security }: { security: SecurityData | null }) {
  if (!security) {
    return (
      <div className="border border-border bg-bg-surface p-6 text-sm text-fg-muted">
        Security scan will be available after the call ends.
      </div>
    );
  }

  const riskColor = security.riskScore <= 20 ? "text-accent" : security.riskScore <= 60 ? "text-warning" : "text-error";

  return (
    <div className="border border-border bg-bg-surface p-4 space-y-4">
      {/* Risk score + compliance */}
      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-1">
          <span className={cn("font-mono text-3xl font-bold", riskColor)}>{security.riskScore}</span>
          <span className="font-mono text-sm text-fg-dimmer">/100 risk</span>
        </div>
        <span className={cn(
          "rounded-full px-2.5 py-0.5 font-mono text-xs uppercase",
          security.compliancePass ? "bg-accent-muted text-accent" : "bg-error-muted text-error",
        )}>
          {security.compliancePass ? "Compliant" : "Non-compliant"}
        </span>
      </div>

      {/* Threats */}
      <div>
        <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-fg-dimmer">Threats</h4>
        {security.threats.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-accent">
            <CheckCircle2 className="h-4 w-4" /> No threats detected
          </div>
        ) : (
          <div className="space-y-2">
            {security.threats.map((threat, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <ShieldAlert className="h-4 w-4 mt-0.5 text-error shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className={cn("rounded-full px-1.5 py-0.5 font-mono text-[10px] uppercase", severityColor[threat.severity] || severityColor.low)}>
                      {threat.severity}
                    </span>
                    <span className="font-mono text-xs text-fg-muted">{threat.type}</span>
                  </div>
                  <p className="text-fg-muted mt-0.5">{threat.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* PII */}
      <div>
        <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-fg-dimmer">PII Detected</h4>
        {security.piiDetected.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-accent">
            <CheckCircle2 className="h-4 w-4" /> No PII detected
          </div>
        ) : (
          <div className="space-y-1">
            {security.piiDetected.map((pii, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-3.5 w-3.5 text-warning shrink-0" />
                <span className="text-fg-muted">{pii.type}</span>
                <span className="font-mono text-xs text-fg-dimmer">({pii.speaker})</span>
                {pii.redacted && <span className="font-mono text-xs text-fg-dimmer">redacted</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire intelligence tab into call detail page**

In `app/(dashboard)/phone/calls/[id]/page.tsx`:

1. Add imports:
```typescript
import { ScoreCard } from "@/components/voice/score-card";
import { SecurityCard } from "@/components/voice/security-card";
```

2. Add queries (alongside existing ones):
```typescript
const { data: score } = useQuery({ ...orpc.voice.getScore.queryOptions({ input: { callId: id } }), retry: false });
const { data: security } = useQuery({ ...orpc.voice.getSecurity.queryOptions({ input: { callId: id } }), retry: false });
```

3. Replace `IntelligenceTabPlaceholder` with:
```typescript
{activeTab === "intelligence" && (
  <div className="grid gap-4 lg:grid-cols-2">
    <ScoreCard score={score ?? null} />
    <SecurityCard security={security ?? null} />
  </div>
)}
```

- [ ] **Step 4: Commit**

```bash
git add apps/console/src/components/voice/score-card.tsx apps/console/src/components/voice/security-card.tsx apps/console/src/app/\(dashboard\)/phone/calls/\[id\]/page.tsx
git commit -m "feat(console): add intelligence tab with score card and security card"
```

---

## [✔] Task 7: Voice Catalog Page

Build the voice catalog grid with filters and audio preview.

**Files:**
- Create: `components/voice/voice-card.tsx`
- Create: `app/(dashboard)/phone/voices/page.tsx`
- Create: `app/(dashboard)/phone/voices/loading.tsx`

- [ ] **Step 1: Create voice-card.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";
import { Copy, Pause, Play } from "lucide-react";
import { useRef, useState } from "react";

type Voice = {
  id: string;
  name: string;
  provider: "telnyx" | "elevenlabs" | "aws-polly";
  tier: "basic" | "premium";
  gender?: string;
  language: string;
  accent?: string;
  style?: string;
  description?: string;
  previewUrl?: string;
};

const providerColor: Record<string, string> = {
  telnyx: "bg-info-muted text-info",
  elevenlabs: "bg-purple-500/10 text-purple-400",
  "aws-polly": "bg-warning-muted text-warning",
};

export function VoiceCard({ voice }: { voice: Voice }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [copied, setCopied] = useState(false);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) audio.pause();
    else audio.play();
    setIsPlaying(!isPlaying);
  };

  const copyId = () => {
    navigator.clipboard.writeText(voice.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="border border-border bg-bg-surface p-4 space-y-3 hover:border-accent/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-medium text-fg">{voice.name}</h3>
        <span className={cn("rounded-full px-2 py-0.5 font-mono text-[10px] uppercase", providerColor[voice.provider] || "bg-bg-elevated text-fg-muted")}>
          {voice.provider}
        </span>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5">
        <span className={cn(
          "rounded-full px-2 py-0.5 font-mono text-[10px] uppercase",
          voice.tier === "premium" ? "bg-accent-muted text-accent" : "bg-bg-elevated text-fg-muted",
        )}>
          {voice.tier}
        </span>
        {voice.gender && (
          <span className="rounded-full bg-bg-elevated px-2 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{voice.gender}</span>
        )}
        <span className="rounded-full bg-bg-elevated px-2 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{voice.language}</span>
        {voice.accent && (
          <span className="rounded-full bg-bg-elevated px-2 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{voice.accent}</span>
        )}
      </div>

      {/* Style */}
      {voice.style && <p className="text-xs italic text-fg-muted">{voice.style}</p>}

      {/* Description */}
      {voice.description && <p className="text-xs text-fg-muted line-clamp-2">{voice.description}</p>}

      {/* Audio preview */}
      <div className="flex items-center justify-between">
        {voice.previewUrl ? (
          <button type="button" onClick={togglePlay} className="flex items-center gap-1.5 text-xs text-fg-muted hover:text-fg">
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            Preview
            <audio ref={audioRef} src={voice.previewUrl} onEnded={() => setIsPlaying(false)} />
          </button>
        ) : (
          <span className="text-xs text-fg-dimmer">No preview</span>
        )}

        {/* Voice ID */}
        <button type="button" onClick={copyId} className="flex items-center gap-1 font-mono text-[10px] text-fg-dimmer hover:text-fg-muted" title="Copy voice ID">
          {copied ? "Copied!" : voice.id.slice(0, 12)} <Copy className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create voices page**

`app/(dashboard)/phone/voices/page.tsx`:

```typescript
"use client";

import { CallTabs } from "@/components/voice/call-tabs";
import { VoiceCard } from "@/components/voice/voice-card";
import { isPhoneFeatureEnabled } from "@/lib/features";
import { FeatureLockedState } from "@/components/dashboard/feature-locked-state";
import { orpc } from "@/lib/orpc";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function VoiceCatalogPage() {
  if (!isPhoneFeatureEnabled()) {
    return <FeatureLockedState title="Voice Catalog" description="Phone features are not enabled." />;
  }

  const { data } = useSuspenseQuery(orpc.voice.catalog.queryOptions({ input: {} }));
  const [tierFilter, setTierFilter] = useState("");
  const [genderFilter, setGenderFilter] = useState("");
  const [languageFilter, setLanguageFilter] = useState("");

  const languages = useMemo(() => {
    const set = new Set(data.voices.map((v) => v.language));
    return Array.from(set).sort();
  }, [data.voices]);

  const filtered = useMemo(() => {
    return data.voices.filter((v) => {
      if (tierFilter && v.tier !== tierFilter) return false;
      if (genderFilter && v.gender !== genderFilter) return false;
      if (languageFilter && v.language !== languageFilter) return false;
      return true;
    });
  }, [data.voices, tierFilter, genderFilter, languageFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Voice Catalog</h1>
        <p className="text-sm text-fg-muted">Browse available voices for your AI agents.</p>
      </div>

      <CallTabs />

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All Tiers</option>
          <option value="basic">Basic</option>
          <option value="premium">Premium</option>
        </select>
        <select
          value={genderFilter}
          onChange={(e) => setGenderFilter(e.target.value)}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All Genders</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="neutral">Neutral</option>
        </select>
        <select
          value={languageFilter}
          onChange={(e) => setLanguageFilter(e.target.value)}
          className="border border-border bg-bg-surface px-3 py-1.5 font-mono text-xs text-fg focus:border-accent focus:outline-none"
        >
          <option value="">All Languages</option>
          {languages.map((lang) => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="flex min-h-[200px] items-center justify-center text-sm text-fg-muted">
          No voices match your filters.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((voice) => (
            <VoiceCard key={voice.id} voice={voice} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create voices loading skeleton**

`app/(dashboard)/phone/voices/loading.tsx`:

```typescript
export default function Loading() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Voice Catalog</h1>
        <p className="text-sm text-fg-muted">Browse available voices for your AI agents.</p>
      </div>
      <div className="h-10 w-64 animate-pulse bg-bg-elevated" />
      <div className="flex gap-3">
        <div className="h-8 w-28 animate-pulse bg-bg-elevated" />
        <div className="h-8 w-28 animate-pulse bg-bg-elevated" />
        <div className="h-8 w-28 animate-pulse bg-bg-elevated" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-48 animate-pulse border border-border bg-bg-elevated" />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/console/src/components/voice/voice-card.tsx apps/console/src/app/\(dashboard\)/phone/voices/
git commit -m "feat(console): add voice catalog page with filters and audio preview"
```

---

## [✔] Task 8: Search Page

Build the semantic transcript search with cross-channel toggle.

**Files:**
- Create: `components/voice/search-results.tsx`
- Create: `app/(dashboard)/phone/calls/search/page.tsx`

- [ ] **Step 1: Create search-results.tsx**

```typescript
"use client";

import { cn } from "@/lib/utils";
import Link from "next/link";

type VoiceResult = {
  callId: string;
  matchedText: string;
  speaker: string;
  startTime: number;
  endTime: number;
  similarity: number;
  chunkType: string;
};

type CrossChannelResult = {
  id: string;
  channel: "email" | "sms" | "voice";
  content: string;
  similarity: number;
  createdAt: string;
  agentId: string;
  callId?: string;
  speaker?: string;
  startTime?: number;
};

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function VoiceSearchResult({ result, query }: { result: VoiceResult; query: string }) {
  const link = `/phone/calls/${result.callId}?tab=transcript&t=${Math.floor(result.startTime)}`;
  return (
    <Link href={link} className="block border border-border bg-bg-surface p-4 hover:border-accent/30 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-accent">{result.callId.slice(0, 12)}…</span>
          <span className="font-mono text-[10px] text-fg-dimmer">{result.speaker}</span>
          <span className="font-mono text-[10px] text-fg-dimmer">{fmt(result.startTime)} — {fmt(result.endTime)}</span>
        </div>
        <span className="font-mono text-xs text-fg-muted">{(result.similarity * 100).toFixed(0)}%</span>
      </div>
      <p className="text-sm text-fg">{result.matchedText}</p>
      <div className="mt-1.5 h-1 w-full bg-bg-elevated rounded-full overflow-hidden">
        <div className="h-full bg-accent rounded-full" style={{ width: `${result.similarity * 100}%` }} />
      </div>
    </Link>
  );
}

const channelBadge: Record<string, string> = {
  voice: "bg-accent-muted text-accent",
  email: "bg-info-muted text-info",
  sms: "bg-warning-muted text-warning",
};

export function CrossChannelSearchResultCard({ result }: { result: CrossChannelResult }) {
  const link = result.channel === "voice" && result.callId
    ? `/phone/calls/${result.callId}?tab=transcript${result.startTime != null ? `&t=${Math.floor(result.startTime)}` : ""}`
    : undefined;

  const inner = (
    <>
      <div className="flex items-center justify-between mb-1">
        <span className={cn("rounded-full px-2 py-0.5 font-mono text-[10px] uppercase", channelBadge[result.channel] || "bg-bg-elevated text-fg-muted")}>
          {result.channel}
        </span>
        <span className="font-mono text-xs text-fg-muted">{(result.similarity * 100).toFixed(0)}%</span>
      </div>
      <p className="text-sm text-fg line-clamp-3">{result.content}</p>
    </>
  );
  const cls = "block border border-border bg-bg-surface p-4 hover:border-accent/30 transition-colors";

  return link ? (
    <Link href={link} className={cls}>{inner}</Link>
  ) : (
    <div className={cls}>{inner}</div>
  );
}
```

- [ ] **Step 2: Create search page**

`app/(dashboard)/phone/calls/search/page.tsx`:

```typescript
"use client";

import { CallTabs } from "@/components/voice/call-tabs";
import { CrossChannelSearchResultCard, VoiceSearchResult } from "@/components/voice/search-results";
import { isPhoneFeatureEnabled } from "@/lib/features";
import { FeatureLockedState } from "@/components/dashboard/feature-locked-state";
import { orpc } from "@/lib/orpc";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";
import { useState } from "react";

export default function SearchPage() {
  if (!isPhoneFeatureEnabled()) {
    return <FeatureLockedState title="Search" description="Phone features are not enabled." />;
  }

  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"voice" | "cross-channel">("voice");

  const voiceSearch = useMutation(orpc.voice.search.mutationOptions());
  const crossSearch = useMutation(orpc.voice.crossChannelSearch.mutationOptions());

  const isLoading = voiceSearch.isPending || crossSearch.isPending;
  const hasSearched = voiceSearch.data != null || crossSearch.data != null;

  const handleSearch = () => {
    if (!query.trim()) return;
    if (mode === "voice") {
      voiceSearch.mutate({ query: query.trim(), limit: 20, threshold: 0.3 });
    } else {
      crossSearch.mutate({ query: query.trim(), channels: ["voice", "email", "sms"], limit: 20, threshold: 0.3 });
    }
  };

  const switchMode = (m: "voice" | "cross-channel") => {
    setMode(m);
    voiceSearch.reset();
    crossSearch.reset();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Search</h1>
        <p className="text-sm text-fg-muted">Semantically search across call transcripts.</p>
      </div>

      <CallTabs />

      {/* Search bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-dimmer" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search across call transcripts..."
            className="w-full border border-border bg-bg-surface px-3 py-2.5 pl-9 font-mono text-sm text-fg placeholder:text-fg-dimmer focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <button
          type="button"
          onClick={handleSearch}
          disabled={isLoading || !query.trim()}
          className="flex items-center gap-2 bg-accent px-4 py-2 font-mono text-xs font-medium uppercase tracking-wider text-bg hover:bg-accent-hover disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </button>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-0 border-b border-border w-fit">
        {(["voice", "cross-channel"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => switchMode(m)}
            className={`px-3 py-1.5 font-mono text-xs uppercase tracking-wider ${
              mode === m ? "border-b-2 border-accent text-accent" : "text-fg-muted hover:text-fg"
            }`}
          >
            {m === "voice" ? "Voice Only" : "Cross-Channel"}
          </button>
        ))}
      </div>

      {/* Results */}
      {!hasSearched && !isLoading && (
        <div className="flex min-h-[200px] flex-col items-center justify-center text-center">
          <Search className="mb-3 h-8 w-8 text-fg-dimmer" />
          <p className="text-sm text-fg-muted">Enter a query to semantically search across all call transcripts.</p>
        </div>
      )}

      {isLoading && (
        <div className="flex min-h-[100px] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-fg-dimmer" />
        </div>
      )}

      {mode === "voice" && voiceSearch.data && (
        <div className="space-y-3">
          <p className="font-mono text-xs text-fg-muted">{voiceSearch.data.results.length} results</p>
          {voiceSearch.data.results.length === 0 ? (
            <p className="text-sm text-fg-muted">No matching transcripts found. Try a broader query.</p>
          ) : (
            voiceSearch.data.results.map((r, i) => (
              <VoiceSearchResult key={i} result={r} query={query} />
            ))
          )}
        </div>
      )}

      {mode === "cross-channel" && crossSearch.data && (
        <div className="space-y-3">
          <p className="font-mono text-xs text-fg-muted">{crossSearch.data.results.length} results</p>
          {crossSearch.data.results.length === 0 ? (
            <p className="text-sm text-fg-muted">No matching content found. Try a broader query.</p>
          ) : (
            crossSearch.data.results.map((r, i) => (
              <CrossChannelSearchResultCard key={i} result={r} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/console/src/components/voice/search-results.tsx apps/console/src/app/\(dashboard\)/phone/calls/search/
git commit -m "feat(console): add semantic search page with cross-channel toggle"
```

---

## [✔] Task 9: Analytics Page

Build the analytics page with stats cards and Recharts charts.

**Files:**
- Create: `components/voice/stats-row.tsx`
- Create: `app/(dashboard)/phone/calls/analytics/page.tsx`

- [ ] **Step 1: Create stats-row.tsx**

```typescript
import { cn } from "@/lib/utils";

type Stat = {
  label: string;
  value: string | number;
  color?: string;
};

export function StatsRow({ stats }: { stats: Stat[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {stats.map((stat) => (
        <div key={stat.label} className="border border-border bg-bg-surface p-4">
          <div className="font-mono text-[10px] uppercase tracking-wider text-fg-dimmer">{stat.label}</div>
          <div className={cn("mt-1 font-mono text-2xl font-bold", stat.color || "text-fg")}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create analytics page**

`app/(dashboard)/phone/calls/analytics/page.tsx`:

```typescript
"use client";

import { CallTabs } from "@/components/voice/call-tabs";
import { StatsRow } from "@/components/voice/stats-row";
import { isPhoneFeatureEnabled } from "@/lib/features";
import { FeatureLockedState } from "@/components/dashboard/feature-locked-state";
import { orpc } from "@/lib/orpc";
import { useSuspenseQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

function scoreColor(score: number) {
  if (score >= 80) return "text-accent";
  if (score >= 60) return "text-warning";
  return "text-error";
}

export default function AnalyticsPage() {
  if (!isPhoneFeatureEnabled()) {
    return <FeatureLockedState title="Analytics" description="Phone features are not enabled." />;
  }

  const { data } = useSuspenseQuery(orpc.voice.analytics.queryOptions({ input: {} }));

  if (data.totalCalls === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Analytics</h1>
          <p className="text-sm text-fg-muted">Aggregate metrics across your voice calls.</p>
        </div>
        <CallTabs />
        <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
          <p className="text-sm text-fg-muted">No call data yet. Analytics will appear after your first completed call.</p>
        </div>
      </div>
    );
  }

  const distributionData = [
    { name: "Excellent", count: data.scoreDistribution.excellent, fill: "var(--color-accent)" },
    { name: "Good", count: data.scoreDistribution.good, fill: "var(--color-info)" },
    { name: "Average", count: data.scoreDistribution.average, fill: "var(--color-warning)" },
    { name: "Poor", count: data.scoreDistribution.poor, fill: "var(--color-error)" },
  ];

  const breakdownData = [
    { name: "Composite", score: data.averageCompositeScore },
    { name: "Resolution", score: data.averageResolutionScore },
    { name: "Sentiment", score: data.averageSentimentScore },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-mono text-lg uppercase tracking-wider text-fg">Analytics</h1>
        <p className="text-sm text-fg-muted">Aggregate metrics across your voice calls.</p>
      </div>

      <CallTabs />

      <StatsRow
        stats={[
          { label: "Total Calls", value: data.totalCalls },
          { label: "Avg Composite Score", value: data.averageCompositeScore, color: scoreColor(data.averageCompositeScore) },
          { label: "Avg Resolution Score", value: data.averageResolutionScore, color: scoreColor(data.averageResolutionScore) },
        ]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Score Distribution */}
        <div className="border border-border bg-bg-surface p-4">
          <h3 className="mb-4 font-mono text-xs uppercase tracking-wider text-fg-dimmer">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="name" tick={{ fill: "var(--color-fg-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }} />
              <YAxis tick={{ fill: "var(--color-fg-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }} />
              <Tooltip contentStyle={{ background: "var(--color-bg-elevated)", border: "1px solid var(--color-border)", color: "var(--color-fg)", fontFamily: "var(--font-mono)", fontSize: 12 }} />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {distributionData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Score Breakdown */}
        <div className="border border-border bg-bg-surface p-4">
          <h3 className="mb-4 font-mono text-xs uppercase tracking-wider text-fg-dimmer">Average Score Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={breakdownData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: "var(--color-fg-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }} />
              <YAxis dataKey="name" type="category" tick={{ fill: "var(--color-fg-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }} width={80} />
              <Tooltip contentStyle={{ background: "var(--color-bg-elevated)", border: "1px solid var(--color-border)", color: "var(--color-fg)", fontFamily: "var(--font-mono)", fontSize: 12 }} />
              <Bar dataKey="score" fill="var(--color-accent)" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/console/src/components/voice/stats-row.tsx apps/console/src/app/\(dashboard\)/phone/calls/analytics/
git commit -m "feat(console): add analytics page with stats and Recharts charts"
```

---

## [✔] Task 10: Polish — Animations, Responsive, Accessibility

Final pass to add Framer Motion animations, responsive tweaks, and accessibility attributes.

**Files:**
- Modify: Multiple component files (call-table, transcript-view, voice-card, call detail tabs)

- [ ] **Step 1: Add tab ARIA attributes**

In call detail page tab navigation, add `role="tablist"` to the container and `role="tab"`, `aria-selected` to each tab button. Add `role="tabpanel"` to the tab content containers.

- [ ] **Step 2: Add ARIA labels to audio elements**

In `recording-player.tsx`: ensure play/pause button has `aria-label` (already present). Add `aria-label="Recording progress"` to the range input.

In `voice-card.tsx`: add `aria-label={`Preview ${voice.name}`}` to the play button.

- [ ] **Step 3: Ensure table semantics**

In `call-table.tsx`: verify `<thead>` / `<tbody>` structure (already correct). Add `scope="col"` to `<th>` elements.

- [ ] **Step 4: Add keyboard navigation to search**

In search page: the Enter key handler is already wired. Ensure the mode toggle buttons are keyboard accessible (they use `<button>` so already are).

- [ ] **Step 5: Responsive testing checklist**

Verify these breakpoints work:
- `sm:` (640px) — filter rows stack, grid reduces columns
- `lg:` (1024px) — intelligence tab side-by-side, analytics charts side-by-side
- Voice catalog: 3 columns → 2 → 1
- Call table: horizontal scroll on narrow screens (already `overflow-x-auto`)

- [ ] **Step 6: Commit**

```bash
git add -A apps/console/src/
git commit -m "feat(console): accessibility and responsive polish for voice dashboard"
```

---

## Summary

| Task | What it builds | Approx files |
|------|---------------|------|
| 1 | Navigation — sidebar group + header | 3 modified |
| 2 | Shared components — badges, tabs, date util | 2 created, 1 modified |
| 3 | Call list page | 3 created |
| 4 | Call detail — header + overview | 4 created |
| 5 | Call detail — transcript tab | 1 created, 1 modified |
| 6 | Call detail — intelligence tab | 2 created, 1 modified |
| 7 | Voice catalog page | 3 created |
| 8 | Search page | 2 created |
| 9 | Analytics page | 2 created |
| 10 | Polish — a11y + responsive | Multiple modified |

Total: ~19 new files, ~5 modified files, 10 commits.
