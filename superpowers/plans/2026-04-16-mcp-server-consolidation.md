# MCP Server Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the per-domain MCP servers (`mcp-agent`, `mcp-email`, `mcp-phone`, `mcp-platform`, `mcp-vault`) and the shared `mcp-core` library into a single `mcp-server` package deployed as one Cloud Run service with path-routed endpoints (`/agent`, `/email`, `/phone`, `/platform`, `/vault`), then delete the old packages and Cloud Run services.

**Architecture:** One Bun+TypeScript package owns all MCP domains. A modified HTTP transport accepts a `{ path → serverFactory }` map so each domain path boots its own `McpServer` instance with only its tool group registered. Bearer-token auth and session/rate-limit/circuit-breaker infrastructure are shared across all domains. One Dockerfile, one Cloud Build, one Cloud Run service (`mcp-server`) with `min-instances=1`, replacing six services scaled to zero. No client compatibility constraints — hosted MCP has no production clients today, so the cutover is destructive (old URLs go away).

**Tech Stack:** Bun runtime, TypeScript, `@modelcontextprotocol/sdk`, Zod, Node `http`. Deployed on Google Cloud Run via Cloud Build (project `anima-labs`, region `us-central1`, Artifact Registry repo `anima`).

---

## Multi-repo reality (context update 2026-04-16)

Each source package is its own independent GitHub repo under the `anima-labs-ai` org (`mcp-agent`, `mcp-email`, `mcp-phone`, `mcp-platform`, `mcp-vault`, `mcp-core`). The parent directory `/Users/diyanbogdanov/projects/agenticmail` is not a git repo — it's a folder of independent checkouts plus loose files like `mcp-deploy/`.

Decisions:
- **New standalone repo:** `anima-labs-ai/mcp-server` created on GitHub. All consolidated code lives there.
- **Clean git history:** First commit in `mcp-server` is a scaffold. No `git subtree`; old repos become reference archives.
- **Old repos deleted permanently** after cutover via `gh repo delete` (Task 9).

Rollback safety: tag `pre-consolidation` on every old repo's `main` before destructive work begins.

## Pre-flight (do once before starting)

- [ ] **Step 0.1: Tag all 7 old repos at current HEAD**

For rollback capability. Run:
```
for d in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault mcp-core; do
  (cd /Users/diyanbogdanov/projects/agenticmail/$d && \
   git tag -f pre-consolidation && \
   git push -f origin pre-consolidation)
done
```
Expected: each repo prints `[new tag]` or `[new tag]` update confirmation.

- [ ] **Step 0.2: Create new GitHub repo**

```
gh repo create anima-labs-ai/mcp-server --public \
  --description "Unified Anima MCP server (path-routed, replaces 6 per-domain repos)" \
  --gitignore Node --license MIT
```

Then create the local directory and init as the new repo:
```
mkdir -p /Users/diyanbogdanov/projects/agenticmail/mcp-server
cd /Users/diyanbogdanov/projects/agenticmail/mcp-server
git init -b main
git remote add origin https://github.com/anima-labs-ai/mcp-server.git
```

All subsequent steps work inside `/Users/diyanbogdanov/projects/agenticmail/mcp-server/`. Commits push to `anima-labs-ai/mcp-server`, not any of the old repos.

- [ ] **Step 0.3: Record baseline test counts per old repo**

```
for d in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault mcp-core; do
  echo "=== $d ==="
  (cd /Users/diyanbogdanov/projects/agenticmail/$d && bun install --silent 2>&1 >/dev/null && bun test 2>&1 | tail -3)
done
```
Record the totals. Task 5.6 validates the unified package matches the sum.

---

## Task 1: Scaffold `mcp-server` package

**Files:**
- Create: `mcp-server/package.json`
- Create: `mcp-server/tsconfig.json`
- Create: `mcp-server/bunfig.toml`
- Create: `mcp-server/.gitignore`
- Create: `mcp-server/README.md`
- Create: `mcp-server/src/index.ts` (stub)

- [ ] **Step 1.1: Write `package.json`**

```json
{
  "name": "@anima-labs/mcp-server",
  "version": "0.1.0",
  "type": "module",
  "description": "Unified Anima MCP server. One process, path-routed endpoints per domain.",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/anima-labs-ai/mcp-server.git"
  },
  "bin": {
    "anima-mcp-server": "./src/index.ts"
  },
  "exports": {
    ".": "./src/index.ts"
  },
  "scripts": {
    "start": "bun run src/index.ts",
    "dev": "bun run --watch src/index.ts",
    "typecheck": "bunx tsc --noEmit",
    "test": "bun test"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.0",
    "zod": "^3.24.0",
    "jose": "^5.9.0"
  },
  "devDependencies": {
    "@types/bun": "^1.2.0",
    "typescript": "^5.7.0"
  }
}
```

All deps are unified across the old servers.

- [ ] **Step 1.2: Write `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["bun"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "noEmit": true
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 1.3: Write `.gitignore` and stub `src/index.ts`**

`.gitignore`:
```
node_modules/
dist/
.DS_Store
```

`src/index.ts` (placeholder, replaced in Task 6):
```ts
#!/usr/bin/env bun
console.error("mcp-server scaffold — not wired yet");
```

- [ ] **Step 1.4: Write `README.md`**

```markdown
# @anima-labs/mcp-server

Unified MCP server for the Anima platform. Exposes domain endpoints:

- `/agent` — agent, organization, identity, registry, A2A tools
- `/email` — Gmail/SMTP email tools
- `/phone` — Telnyx voice + SMS tools
- `/platform` — messaging, spam, webhooks, pods, agent orchestration
- `/vault` — credential vault, OAuth connections, Connect Links

Run:
\`\`\`
bun run src/index.ts --http
\`\`\`

Replaces separate packages (`mcp-agent`, `mcp-email`, `mcp-phone`, `mcp-platform`, `mcp-vault`) and the `mcp-core` shared library.
```

- [ ] **Step 1.5: Install deps and verify scaffold builds**

Run:
```
cd mcp-server && bun install && bun run typecheck
```
Expected: `bun install` completes, `typecheck` exits 0.

- [ ] **Step 1.6: Commit**

```bash
git add mcp-server/package.json mcp-server/tsconfig.json mcp-server/bunfig.toml mcp-server/.gitignore mcp-server/README.md mcp-server/src/index.ts mcp-server/bun.lock
git commit -m "feat(mcp-server): scaffold unified MCP package"
```

---

## Task 2: Port `mcp-core` internals into `mcp-server/src/shared/`

Since there will be only one consumer of mcp-core after consolidation, it stops being a package and becomes internal modules.

**Files:**
- Create: `mcp-server/src/shared/api-client.ts`
- Create: `mcp-server/src/shared/config.ts`
- Create: `mcp-server/src/shared/tool-helpers.ts`
- Create: `mcp-server/src/shared/rate-limiter.ts`
- Create: `mcp-server/src/shared/circuit-breaker.ts`
- Create: `mcp-server/src/shared/session-registry.ts`
- Create: `mcp-server/src/shared/metrics.ts`
- Create: `mcp-server/src/shared/pending-followup.ts`
- Create: `mcp-server/src/shared/__tests__/*` (ported from mcp-core)

- [ ] **Step 2.1: Copy core files**

```bash
cp mcp-core/src/api-client.ts        mcp-server/src/shared/api-client.ts
cp mcp-core/src/config.ts            mcp-server/src/shared/config.ts
cp mcp-core/src/tool-helpers.ts      mcp-server/src/shared/tool-helpers.ts
cp mcp-core/src/rate-limiter.ts      mcp-server/src/shared/rate-limiter.ts
cp mcp-core/src/circuit-breaker.ts   mcp-server/src/shared/circuit-breaker.ts
cp mcp-core/src/session-registry.ts  mcp-server/src/shared/session-registry.ts
cp mcp-core/src/metrics.ts           mcp-server/src/shared/metrics.ts
```

`pending-followup.ts` is identical between `mcp-email` and `mcp-platform` (verified via `diff`). Copy once:
```bash
cp mcp-email/src/pending-followup.ts mcp-server/src/shared/pending-followup.ts
```

Do NOT copy `http-transport.ts` yet — that's refactored in Task 3.

- [ ] **Step 2.2: Copy core tests**

```bash
mkdir -p mcp-server/src/shared/__tests__
cp mcp-core/src/__tests__/*.test.ts mcp-server/src/shared/__tests__/
```

- [ ] **Step 2.3: Fix import paths in copied files**

In copied tests, rewrite `from "../<x>.js"` paths so they still resolve (they already will if the relative depth is the same — both mcp-core and shared are one level deep).

Run: `grep -rn "from \"@anima-labs/mcp-core" mcp-server/src/shared/` — expected: zero results. If any, change to relative imports.

- [ ] **Step 2.4: Run ported tests**

Run: `cd mcp-server && bun test src/shared`
Expected: all ported tests pass. Note count matches mcp-core's pretest count from Step 0.3.

- [ ] **Step 2.5: Commit**

```bash
git add mcp-server/src/shared mcp-server/bun.lock
git commit -m "feat(mcp-server): port mcp-core internals to shared/"
```

---

## Task 3: Build path-routed HTTP transport (TDD)

This is the one piece of genuinely new code. The existing `http-transport.ts` accepts a single `serverFactory`; the new one accepts a `{ path → factory }` map, dispatches MCP sessions per path, and keeps rate limiter / circuit breaker / registry shared.

**Files:**
- Create: `mcp-server/src/transport/http.ts`
- Create: `mcp-server/src/transport/__tests__/http.test.ts`

- [ ] **Step 3.1: Write failing test for path routing**

Create `mcp-server/src/transport/__tests__/http.test.ts`:

```ts
import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createMcpHttpServer, type HttpTransportServer } from "../http.ts";

const buildEmptyServer = (name: string) =>
  new McpServer({ name, version: "0.0.0" }, { capabilities: { tools: {} } });

describe("createMcpHttpServer path routing", () => {
  let handle: HttpTransportServer;
  let baseUrl: string;

  beforeAll(async () => {
    handle = createMcpHttpServer(
      {
        "/agent": () => buildEmptyServer("agent"),
        "/email": () => buildEmptyServer("email"),
      },
      { port: 0 },
    );
    await new Promise<void>((res) => handle.httpServer.listen(0, () => res()));
    const addr = handle.httpServer.address();
    if (!addr || typeof addr === "string") throw new Error("no addr");
    baseUrl = `http://127.0.0.1:${addr.port}`;
  });

  afterAll(async () => {
    await handle.close();
  });

  it("returns 200 on /health", async () => {
    const r = await fetch(`${baseUrl}/health`);
    expect(r.status).toBe(200);
    const body = await r.json();
    expect(body.status).toBe("ok");
  });

  it("404s an unknown domain path", async () => {
    const r = await fetch(`${baseUrl}/unknown`, { method: "POST" });
    expect(r.status).toBe(404);
  });

  it("accepts an MCP initialize on a registered path", async () => {
    const init = {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-03-26",
        capabilities: {},
        clientInfo: { name: "test", version: "0" },
      },
    };
    const r = await fetch(`${baseUrl}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
      body: JSON.stringify(init),
    });
    expect(r.status).toBe(200);
    expect(r.headers.get("mcp-session-id")).toBeTruthy();
  });
});
```

- [ ] **Step 3.2: Run test to verify it fails**

Run: `cd mcp-server && bun test src/transport`
Expected: FAIL — `../http.ts` does not exist.

- [ ] **Step 3.3: Implement path-routed transport**

Create `mcp-server/src/transport/http.ts` by adapting `mcp-core/src/http-transport.ts` with these changes:

1. Replace `serverFactory` parameter with `factories: Record<string, () => McpServer>`.
2. Replace the hard-coded `if (url.pathname !== "/mcp")` check with: look up `factories[url.pathname]` — if absent, return 404.
3. Pass the matched factory into the initialize handler.
4. Keep `/health`, `/favicon.ico`, `/icon.png`, `/robots.txt`, `/.well-known/oauth-protected-resource`, and `/` (landing page) as top-level routes.
5. Update the landing page HTML to list all registered domain paths.

Preserve all session registry / rate limiter / circuit breaker / metrics behaviour verbatim. The session map's values gain a `path: string` field so cleanup/telemetry is per-domain.

Paste the complete new file:

```ts
// mcp-server/src/transport/http.ts
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { randomUUID } from "node:crypto";
import { createSessionRegistry, type SessionRegistry, type SessionRegistryOptions } from "../shared/session-registry.ts";
import { createMcpRateLimiter, type McpRateLimiter, type McpRateLimiterOptions } from "../shared/rate-limiter.ts";
import { createCircuitBreaker, CircuitOpenError, type CircuitBreaker, type CircuitBreakerOptions } from "../shared/circuit-breaker.ts";
import { createMcpMetrics, type McpMetrics } from "../shared/metrics.ts";
import { ANIMA_ICON_PNG_BASE64 } from "../shared/config.ts";

const ICON_PNG_BUFFER = Buffer.from(ANIMA_ICON_PNG_BASE64, "base64");

export const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, mcp-session-id, Last-Event-ID, mcp-protocol-version",
  "Access-Control-Expose-Headers": "mcp-session-id, mcp-protocol-version",
};

export function jsonError(res: ServerResponse, status: number, message: string) {
  res.writeHead(status, { ...CORS_HEADERS, "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: message }));
}

export function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
    req.on("error", reject);
  });
}

export function parseBearerToken(req: IncomingMessage): string | undefined {
  const header = req.headers.authorization;
  if (!header) return undefined;
  const match = header.match(/^Bearer\s+(\S+)$/i);
  return match?.[1];
}

interface McpSession {
  server: McpServer;
  transport: StreamableHTTPServerTransport;
  path: string;
  apiKeyId?: string;
  orgId?: string;
}

export interface McpAuthContext {
  apiKeyId: string;
  orgId: string;
}

export interface McpAuthError {
  status: number;
  message: string;
}

export interface OAuthDiscovery {
  mcpBaseUrl: string;
  authServerUrl: string;
}

export type DomainFactories = Record<string, () => McpServer>;

export interface HttpTransportOptions {
  port?: number;
  onShutdown?: () => void;
  authenticate?: (req: IncomingMessage, path: string) => Promise<McpAuthContext | undefined>;
  sessionRegistry?: SessionRegistryOptions;
  rateLimiter?: McpRateLimiterOptions;
  circuitBreaker?: CircuitBreakerOptions;
  oauth?: OAuthDiscovery;
}

export interface HttpTransportServer {
  httpServer: Server;
  sessions: Map<string, McpSession>;
  registry: SessionRegistry;
  rateLimiter: McpRateLimiter;
  circuitBreaker: CircuitBreaker;
  metrics: McpMetrics;
  close: () => Promise<void>;
}

export function createMcpHttpServer(
  factories: DomainFactories,
  options?: HttpTransportOptions,
): HttpTransportServer {
  const sessions = new Map<string, McpSession>();
  const port = options?.port ?? 0;
  const startedAt = Date.now();

  const registry = createSessionRegistry(options?.sessionRegistry);
  const rateLimiter = createMcpRateLimiter(options?.rateLimiter);
  const circuitBreaker = createCircuitBreaker(options?.circuitBreaker);
  const metrics = createMcpMetrics();

  registry.startSweep(async (sessionId: string) => {
    const session = sessions.get(sessionId);
    if (session) {
      await session.transport.close();
      await session.server.close();
      sessions.delete(sessionId);
      metrics.sessionClosed();
    }
  });

  function setRateLimitHeaders(res: ServerResponse, remaining: number, limit: number, retryAfterMs?: number): void {
    res.setHeader("X-RateLimit-Limit", limit);
    res.setHeader("X-RateLimit-Remaining", remaining);
    if (retryAfterMs !== undefined) res.setHeader("Retry-After", Math.ceil(retryAfterMs / 1000));
  }

  const domainPaths = Object.keys(factories);

  const httpServer = createServer(async (req: IncomingMessage, res: ServerResponse) => {
    const url = new URL(req.url ?? "/", `http://localhost:${port}`);

    if (req.method === "OPTIONS") {
      res.writeHead(204, CORS_HEADERS);
      res.end();
      return;
    }

    if (url.pathname === "/favicon.ico" || url.pathname === "/icon.png") {
      res.writeHead(200, {
        ...CORS_HEADERS,
        "Content-Type": "image/png",
        "Content-Length": ICON_PNG_BUFFER.length,
        "Cache-Control": "public, max-age=604800",
      });
      res.end(ICON_PNG_BUFFER);
      return;
    }

    if (url.pathname === "/robots.txt") {
      res.writeHead(200, { ...CORS_HEADERS, "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=86400" });
      res.end("User-agent: *\nAllow: /\n");
      return;
    }

    if (url.pathname === "/" && req.method === "GET") {
      const links = domainPaths.map((p) => `<li><code>${p}</code></li>`).join("");
      const html = `<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Anima MCP</title>
<link rel="icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="96x96" href="/icon.png">
<link rel="apple-touch-icon" href="/icon.png">
</head><body>
<h1>Anima MCP Server</h1>
<p>This is an MCP (Model Context Protocol) server. Available domains:</p>
<ul>${links}</ul>
</body></html>`;
      res.writeHead(200, { ...CORS_HEADERS, "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600" });
      res.end(html);
      return;
    }

    if (options?.oauth && url.pathname === "/.well-known/oauth-protected-resource") {
      res.writeHead(200, { ...CORS_HEADERS, "Content-Type": "application/json", "Cache-Control": "public, max-age=3600" });
      res.end(JSON.stringify({
        resource: options.oauth.mcpBaseUrl,
        authorization_servers: [options.oauth.authServerUrl],
        bearer_methods_supported: ["header"],
      }));
      return;
    }

    if (url.pathname === "/health") {
      const uptimeMs = Date.now() - startedAt;
      res.writeHead(200, { ...CORS_HEADERS, "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: "ok",
        sessions: sessions.size,
        uptimeSeconds: Math.floor(uptimeMs / 1000),
        startedAt: new Date(startedAt).toISOString(),
        domains: domainPaths,
        metrics: metrics.snapshot(),
        registry: registry.stats(),
      }));
      return;
    }

    const factory = factories[url.pathname];
    if (!factory) {
      jsonError(res, 404, "Not Found");
      return;
    }

    // MCP protocol handling for this domain
    if (req.method === "DELETE") {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      const session = sessionId ? sessions.get(sessionId) : undefined;
      if (session && session.path === url.pathname) {
        if (sessionId) {
          sessions.delete(sessionId);
          registry.remove(sessionId);
          metrics.sessionClosed();
        }
        await session.transport.close();
        await session.server.close();
        res.writeHead(200, CORS_HEADERS);
        res.end();
      } else {
        jsonError(res, 404, "Session not found");
      }
      return;
    }

    if (req.method === "GET") {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      const session = sessionId ? sessions.get(sessionId) : undefined;
      if (session && session.path === url.pathname) {
        if (sessionId) registry.touch(sessionId);
        await session.transport.handleRequest(req, res);
      } else {
        jsonError(res, 400, "Missing or invalid mcp-session-id header");
      }
      return;
    }

    if (req.method === "POST") {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;

      let body: unknown;
      try {
        body = JSON.parse(await readBody(req));
      } catch {
        jsonError(res, 400, "Invalid JSON body");
        return;
      }

      if (sessionId) {
        const session = sessions.get(sessionId);
        if (session && session.path === url.pathname) {
          registry.touch(sessionId);
          const apiKeyId = session.apiKeyId ?? "unknown";
          const orgId = session.orgId ?? "unknown";

          const requestCheck = rateLimiter.checkRequest(apiKeyId);
          if (!requestCheck.allowed) {
            metrics.rateLimitHit();
            setRateLimitHeaders(res, requestCheck.remaining, requestCheck.limit, requestCheck.retryAfterMs);
            jsonError(res, 429, "Rate limit exceeded");
            return;
          }

          try {
            await circuitBreaker.execute(orgId, async () => {
              const callStart = Date.now();
              await session.transport.handleRequest(req, res, body);
              metrics.toolCallRecorded(Date.now() - callStart);
            });
          } catch (err) {
            if (err instanceof CircuitOpenError) {
              metrics.circuitBreakerTripped(orgId);
              setRateLimitHeaders(res, 0, 0, err.retryAfterMs);
              jsonError(res, 503, err.message);
            }
          }
          return;
        }
        jsonError(res, 404, "Session not found. Create a new session with an initialize request.");
        return;
      }

      if (!isInitializeRequest(body)) {
        jsonError(res, 400, "First request must be an MCP initialize request");
        return;
      }

      let authContext: McpAuthContext | undefined;
      if (options?.authenticate) {
        try {
          authContext = await options.authenticate(req, url.pathname);
        } catch (err) {
          const authErr = err as McpAuthError;
          metrics.authFailure();
          const status = authErr.status || 401;
          if (status === 401 && options.oauth) {
            res.setHeader("WWW-Authenticate", `Bearer resource_metadata="${options.oauth.mcpBaseUrl}/.well-known/oauth-protected-resource"`);
          }
          jsonError(res, status, authErr.message || "Authentication failed");
          return;
        }
      }

      const apiKeyId = authContext?.apiKeyId ?? "anonymous";
      const orgId = authContext?.orgId ?? "anonymous";

      const sessionCheck = rateLimiter.checkSessionCreation(apiKeyId, registry.countByKey(apiKeyId));
      if (!sessionCheck.allowed) {
        metrics.rateLimitHit();
        setRateLimitHeaders(res, sessionCheck.remaining, sessionCheck.limit, sessionCheck.retryAfterMs);
        jsonError(res, 429, "Too many active sessions for this API key");
        return;
      }

      if (!registry.canCreateSession(apiKeyId)) {
        jsonError(res, 429, "Maximum concurrent sessions reached for this API key");
        return;
      }

      const mcpServer = factory();
      const thisPath = url.pathname;
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (sid: string) => {
          sessions.set(sid, { server: mcpServer, transport, path: thisPath, apiKeyId, orgId });
          registry.register(sid, apiKeyId, orgId);
          metrics.sessionCreated();
        },
      });

      transport.onclose = () => {
        const sid = transport.sessionId;
        if (sid && sessions.has(sid)) {
          sessions.delete(sid);
          registry.remove(sid);
          metrics.sessionClosed();
        }
      };

      await mcpServer.connect(transport);
      await transport.handleRequest(req, res, body);
      return;
    }

    jsonError(res, 405, "Method not allowed");
  });

  const close = async () => {
    registry.stopSweep();
    for (const session of sessions.values()) {
      await session.transport.close();
      await session.server.close();
    }
    sessions.clear();
    httpServer.close();
    options?.onShutdown?.();
  };

  return { httpServer, sessions, registry, rateLimiter, circuitBreaker, metrics, close };
}
```

- [ ] **Step 3.4: Run transport tests**

Run: `cd mcp-server && bun test src/transport`
Expected: all three tests pass.

- [ ] **Step 3.5: Commit**

```bash
git add mcp-server/src/transport
git commit -m "feat(mcp-server): path-routed HTTP transport with per-domain factories"
```

---

## Task 4: Port tool groups (one task per domain)

Each domain port follows the same pattern:
1. Copy `mcp-<name>/src/tools/` → `mcp-server/src/tools/<name>/`
2. Copy `mcp-<name>/src/tool-helpers.ts` → `mcp-server/src/tools/<name>/tool-helpers.ts` (the per-package helpers, distinct from `shared/tool-helpers.ts`)
3. Copy `mcp-<name>/src/__tests__/` → `mcp-server/src/tools/<name>/__tests__/`
4. Rewrite imports: `@anima-labs/mcp-core` → `../../shared/<module>.ts`
5. Run tests; fix any broken relative imports; commit.

### Task 4a: Port `agent` domain

**Files:**
- Create: `mcp-server/src/tools/agent/` (copy of `mcp-agent/src/tools/`)
- Create: `mcp-server/src/tools/agent/tool-helpers.ts`
- Create: `mcp-server/src/tools/agent/__tests__/tool-registration.test.ts`

- [ ] **Step 4a.1: Copy files**

```bash
cp -R mcp-agent/src/tools               mcp-server/src/tools/agent
cp mcp-agent/src/tool-helpers.ts        mcp-server/src/tools/agent/tool-helpers.ts
cp -R mcp-agent/src/__tests__           mcp-server/src/tools/agent/__tests__
```

- [ ] **Step 4a.2: Rewrite imports**

Run:
```
find mcp-server/src/tools/agent -name "*.ts" -print0 | xargs -0 sed -i '' 's|@anima-labs/mcp-core|../../../shared/index.ts|g'
```

Then create `mcp-server/src/shared/index.ts` if it doesn't exist yet — a barrel re-exporting everything in `shared/`:

```ts
export * from "./api-client.ts";
export * from "./config.ts";
export * from "./tool-helpers.ts";
export * from "./rate-limiter.ts";
export * from "./circuit-breaker.ts";
export * from "./session-registry.ts";
export * from "./metrics.ts";
```

- [ ] **Step 4a.3: Run agent tests**

Run: `cd mcp-server && bun test src/tools/agent`
Expected: all pass. If imports still break, `grep -rn "from \"" src/tools/agent` and fix paths.

- [ ] **Step 4a.4: Create domain factory**

Create `mcp-server/src/tools/agent/factory.ts`:

```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SERVER_INFO as CORE_SERVER_INFO, type ApiClient, type ToolRegistrationOptions } from "../../shared/index.ts";
import { registerAgentTools } from "./agent/index.ts";
import { registerOrganizationTools } from "./organization/index.ts";
import { registerIdentityTools } from "./identity/index.ts";
import { registerRegistryTools } from "./registry/index.ts";
import { registerA2aTools } from "./a2a/index.ts";

const SERVER_INFO = {
  ...CORE_SERVER_INFO,
  name: "anima-mcp-agent",
  version: "0.1.0",
  description: "Anima MCP Server — Agent, organization, identity, registry, and A2A tools",
};

export function buildAgentServer(client: ApiClient): McpServer {
  const server = new McpServer(SERVER_INFO, { capabilities: { tools: {} } });
  const context: ToolRegistrationOptions = {
    server,
    context: { client, hasMasterKey: client.hasMasterKey() },
  };
  registerAgentTools(context);
  registerOrganizationTools(context);
  registerIdentityTools(context);
  registerRegistryTools(context);
  registerA2aTools(context);
  return server;
}
```

- [ ] **Step 4a.5: Commit**

```bash
git add mcp-server/src/tools/agent mcp-server/src/shared/index.ts
git commit -m "feat(mcp-server): port agent tool group"
```

### Task 4c: Port `email` domain

- [ ] **Step 4c.1: Copy**

```bash
cp -R mcp-email/src/tools         mcp-server/src/tools/email
cp mcp-email/src/tool-helpers.ts  mcp-server/src/tools/email/tool-helpers.ts
cp -R mcp-email/src/__tests__     mcp-server/src/tools/email/__tests__
```

Note: `pending-followup.ts` was already moved to `shared/` in Task 2 — rewrite email imports of it to `../../shared/pending-followup.ts`.

- [ ] **Step 4c.2: Rewrite imports**

```bash
find mcp-server/src/tools/email -name "*.ts" -print0 | xargs -0 sed -i '' 's|@anima-labs/mcp-core|../../../shared/index.ts|g'
find mcp-server/src/tools/email -name "*.ts" -print0 | xargs -0 sed -i '' 's|from "../pending-followup.ts"|from "../../shared/pending-followup.ts"|g'
find mcp-server/src/tools/email -name "*.ts" -print0 | xargs -0 sed -i '' 's|from "\.\./pending-followup\.js"|from "../../shared/pending-followup.ts"|g'
```

- [ ] **Step 4c.3: Run tests, create factory, commit**

```
cd mcp-server && bun test src/tools/email
```

Create `mcp-server/src/tools/email/factory.ts`, mirroring 4a.4 with `registerEmailTools` and the correct per-domain SERVER_INFO.

```bash
git add mcp-server/src/tools/email
git commit -m "feat(mcp-server): port email tool group"
```

### Task 4d: Port `phone` domain

- [ ] **Step 4d.1: Copy and rewrite imports**

```bash
cp -R mcp-phone/src/tools         mcp-server/src/tools/phone
cp mcp-phone/src/tool-helpers.ts  mcp-server/src/tools/phone/tool-helpers.ts
cp -R mcp-phone/src/__tests__     mcp-server/src/tools/phone/__tests__
find mcp-server/src/tools/phone -name "*.ts" -print0 | xargs -0 sed -i '' 's|@anima-labs/mcp-core|../../../shared/index.ts|g'
```

- [ ] **Step 4d.2: Run tests, create factory, commit**

```
cd mcp-server && bun test src/tools/phone
```

Create `src/tools/phone/factory.ts`.

```bash
git add mcp-server/src/tools/phone
git commit -m "feat(mcp-server): port phone tool group"
```

### Task 4e: Port `platform` domain

- [ ] **Step 4e.1: Copy and rewrite imports**

```bash
cp -R mcp-platform/src/tools         mcp-server/src/tools/platform
cp mcp-platform/src/tool-helpers.ts  mcp-server/src/tools/platform/tool-helpers.ts
cp -R mcp-platform/src/__tests__     mcp-server/src/tools/platform/__tests__
find mcp-server/src/tools/platform -name "*.ts" -print0 | xargs -0 sed -i '' 's|@anima-labs/mcp-core|../../../shared/index.ts|g'
find mcp-server/src/tools/platform -name "*.ts" -print0 | xargs -0 sed -i '' 's|from "../pending-followup.ts"|from "../../shared/pending-followup.ts"|g'
find mcp-server/src/tools/platform -name "*.ts" -print0 | xargs -0 sed -i '' 's|from "\.\./pending-followup\.js"|from "../../shared/pending-followup.ts"|g'
```

- [ ] **Step 4e.2: Run tests, create factory, commit**

```
cd mcp-server && bun test src/tools/platform
```

Create `src/tools/platform/factory.ts`.

```bash
git add mcp-server/src/tools/platform
git commit -m "feat(mcp-server): port platform tool group"
```

### Task 4f: Port `vault` domain

- [ ] **Step 4f.1: Copy and rewrite imports**

```bash
cp -R mcp-vault/src/tools         mcp-server/src/tools/vault
cp mcp-vault/src/tool-helpers.ts  mcp-server/src/tools/vault/tool-helpers.ts
cp -R mcp-vault/src/__tests__     mcp-server/src/tools/vault/__tests__
find mcp-server/src/tools/vault -name "*.ts" -print0 | xargs -0 sed -i '' 's|@anima-labs/mcp-core|../../../shared/index.ts|g'
```

- [ ] **Step 4f.2: Run tests, create factory, commit**

```
cd mcp-server && bun test src/tools/vault
```

Create `src/tools/vault/factory.ts`.

```bash
git add mcp-server/src/tools/vault
git commit -m "feat(mcp-server): port vault tool group"
```

---

## Task 5: Unified entry point and auth

**Files:**
- Replace: `mcp-server/src/index.ts`
- Create: `mcp-server/src/auth.ts`

- [ ] **Step 5.1: Write failing end-to-end test**

Create `mcp-server/src/__tests__/e2e.test.ts` that boots the full server (all 6 domains, in-memory API client stub), hits `/health`, and confirms `domains` list contains all six. Example:

```ts
import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { buildUnifiedServer } from "../index.ts";

describe("mcp-server e2e", () => {
  let handle: Awaited<ReturnType<typeof buildUnifiedServer>>;
  let baseUrl: string;

  beforeAll(async () => {
    process.env.ANIMA_API_URL = "http://localhost:9999"; // unused in this test
    handle = await buildUnifiedServer({ port: 0 });
    const addr = handle.httpServer.address();
    if (!addr || typeof addr === "string") throw new Error();
    baseUrl = `http://127.0.0.1:${addr.port}`;
  });

  afterAll(async () => {
    await handle.close();
  });

  it("lists all domains on /health", async () => {
    const r = await fetch(`${baseUrl}/health`);
    const body = await r.json();
    expect(body.domains.sort()).toEqual(["/agent", "/email", "/phone", "/platform", "/vault"]);
  });

  it("401s unauthenticated initialize", async () => {
    const r = await fetch(`${baseUrl}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "t", version: "0" } } }),
    });
    expect(r.status).toBe(401);
  });
});
```

- [ ] **Step 5.2: Run test — expect FAIL (no buildUnifiedServer)**

Run: `cd mcp-server && bun test src/__tests__/e2e.test.ts`

- [ ] **Step 5.3: Write `auth.ts`**

Extracted from the duplicate `authenticate` blocks in the 6 old servers:

```ts
// mcp-server/src/auth.ts
import type { IncomingMessage } from "node:http";
import { ApiClient, parseBearerToken } from "./shared/index.ts";
import type { McpAuthContext, McpAuthError } from "./transport/http.ts";

const VALID_KEY_PREFIXES = ["ak_", "mk_", "sk_live_", "sk_test_"];

export function makeAuthenticator(apiUrl: string): (req: IncomingMessage) => Promise<McpAuthContext> {
  // Cache ApiClient per token for the duration of initialize. The transport
  // only calls authenticate once per session (on initialize), so we return a
  // fresh client per call — do not reuse across sessions for different tokens.
  const clientByToken = new Map<string, ApiClient>();

  return async function authenticate(req) {
    const token = parseBearerToken(req);
    if (!token) {
      const err: McpAuthError = { status: 401, message: "Missing Authorization header" };
      throw err;
    }
    if (!VALID_KEY_PREFIXES.some((p) => token.startsWith(p))) {
      const err: McpAuthError = { status: 401, message: "Invalid API key format" };
      throw err;
    }
    let client = clientByToken.get(token);
    if (!client) {
      client = new ApiClient({ baseUrl: apiUrl, apiKey: token });
      clientByToken.set(token, client);
    }
    let orgId = "default";
    try {
      const orgs = await client.get<Array<{ id: string }>>("/orgs");
      if (Array.isArray(orgs) && orgs[0]?.id) orgId = orgs[0].id;
    } catch {
      const err: McpAuthError = { status: 401, message: "Invalid or expired API key" };
      throw err;
    }
    return { apiKeyId: token, orgId, client };
  };
}

// The transport's McpAuthContext needs to grow a `client` field so factories
// can read it without re-creating. See Task 3 addendum.
```

Note: `McpAuthContext` in `transport/http.ts` must gain `client: ApiClient`. Update Task 3's file accordingly and re-run transport tests. (If you skipped that during Task 3, do it now: add `client: ApiClient;` to the interface and plumb it into the `McpSession` struct so factories can pull the bound client per session.)

- [ ] **Step 5.4: Write `src/index.ts`**

```ts
#!/usr/bin/env bun
import { createMcpHttpServer, type DomainFactories } from "./transport/http.ts";
import type { ApiClient } from "./shared/index.ts";
import { loadConfig } from "./shared/index.ts";
import { makeAuthenticator } from "./auth.ts";
import { buildAgentServer } from "./tools/agent/factory.ts";
import { buildEmailServer } from "./tools/email/factory.ts";
import { buildPhoneServer } from "./tools/phone/factory.ts";
import { buildPlatformServer } from "./tools/platform/factory.ts";
import { buildVaultServer } from "./tools/vault/factory.ts";

export async function buildUnifiedServer(opts: { port?: number } = {}) {
  const config = loadConfig();
  const authenticate = makeAuthenticator(config.apiUrl);

  // Client is bound per-session by transport. Factories receive it via a
  // per-session wrapper — see transport's McpAuthContext.client.
  let pending: ApiClient | null = null;
  const wrap = (build: (c: ApiClient) => ReturnType<typeof buildAgentServer>) => () => {
    if (!pending) throw new Error("No authenticated client for session");
    const client = pending;
    pending = null;
    return build(client);
  };

  const factories: DomainFactories = {
    "/agent":    wrap(buildAgentServer),
    "/email":    wrap(buildEmailServer),
    "/phone":    wrap(buildPhoneServer),
    "/platform": wrap(buildPlatformServer),
    "/vault":    wrap(buildVaultServer),
  };

  const mcpBaseUrl = process.env.MCP_BASE_URL ?? "https://mcp.useanima.sh";
  const authServerUrl = process.env.CONSOLE_URL ?? "https://console.useanima.sh";

  const handle = createMcpHttpServer(factories, {
    port: opts.port ?? config.httpPort,
    oauth: { mcpBaseUrl, authServerUrl },
    authenticate: async (req) => {
      const ctx = await authenticate(req);
      pending = ctx.client;
      return { apiKeyId: ctx.apiKeyId, orgId: ctx.orgId, client: ctx.client };
    },
  });

  return handle;
}

async function main() {
  const handle = await buildUnifiedServer();
  handle.httpServer.listen(handle.httpServer.address() ? 0 : (await import("./shared/index.ts")).loadConfig().httpPort, () => {
    const addr = handle.httpServer.address();
    const port = typeof addr === "object" && addr ? addr.port : "?";
    console.error(`Anima MCP server running on http://localhost:${port}`);
    console.error("Domains:", Object.keys((handle as any).factories ?? {}).join(", "));
  });

  const shutdown = async () => { await handle.close(); process.exit(0); };
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

if (import.meta.main) main().catch((err) => { console.error("Fatal:", err); process.exit(1); });
```

- [ ] **Step 5.5: Run e2e test**

Run: `cd mcp-server && bun test src/__tests__/e2e.test.ts`
Expected: both tests pass.

- [ ] **Step 5.6: Full test run**

Run: `cd mcp-server && bun test`
Expected: all tests from all domains plus transport plus shared pass. Total count should equal sum of old per-package test counts recorded in Step 0.3.

- [ ] **Step 5.7: Commit**

```bash
git add mcp-server/src/index.ts mcp-server/src/auth.ts mcp-server/src/__tests__/e2e.test.ts mcp-server/src/transport/http.ts
git commit -m "feat(mcp-server): unified entry point with per-session auth and all 6 domains"
```

---

## Task 6: Local smoke test

- [ ] **Step 6.1: Boot the server locally**

Terminal 1:
```
cd mcp-server && ANIMA_API_URL=https://anima-api-v7ar7whcsq-uc.a.run.app PORT=8080 bun run src/index.ts
```

Expected: server logs `running on http://localhost:8080`.

- [ ] **Step 6.2: Hit /health and verify domains**

Terminal 2:
```
curl -s http://localhost:8080/health | jq '.domains'
```
Expected: `["/agent","/email","/phone","/platform","/vault"]`.

- [ ] **Step 6.3: Drive an MCP session end-to-end with a real key**

Use a `sk_test_…` key from your Anima account. Against `/agent`:

```
export KEY=sk_test_xxx
curl -s -D- -X POST http://localhost:8080/agent \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```

Expected: `HTTP/1.1 200 OK`, `mcp-session-id: <uuid>` header, JSON body with `result.serverInfo.name = "anima-mcp-agent"`.

Capture the session-id, then list tools:
```
curl -s -X POST http://localhost:8080/agent \
  -H "Authorization: Bearer $KEY" \
  -H "mcp-session-id: <uuid>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | jq '.result.tools | length'
```

Expected: count > 0.

Repeat for `/email`, `/phone`, `/platform`, `/vault`. All must initialize cleanly.

- [ ] **Step 6.4: Stop server, note any issues, fix and re-commit**

If any domain fails initialize, diagnose against its factory (likely an import or tool-registrar gap). Fix and commit as `fix(mcp-server): ...`.

---

## Task 7: Deployment artifacts

**Files:**
- Create: `mcp-server/Dockerfile`
- Create: `mcp-server/cloudbuild.yaml`
- Create: `mcp-server/deploy.sh`

- [ ] **Step 7.1: Write `mcp-server/Dockerfile`**

```dockerfile
# Anima MCP Server — unified image
FROM --platform=linux/amd64 oven/bun:1 AS install
WORKDIR /app
COPY package.json bun.lock tsconfig.json ./
RUN bun install --frozen-lockfile

FROM --platform=linux/amd64 oven/bun:1-slim AS runtime
WORKDIR /app
COPY --from=install /app/node_modules ./node_modules
COPY package.json tsconfig.json ./
COPY src ./src

ENV NODE_ENV=production
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD bun -e "fetch('http://127.0.0.1:8080/health').then(r => r.ok ? process.exit(0) : process.exit(1)).catch(() => process.exit(1))"

CMD ["bun", "run", "src/index.ts"]
```

Unlike the old Dockerfile, this one uses `mcp-server/` as its context — no more `--build-arg MCP_SERVER=…` hack.

- [ ] **Step 7.2: Write `cloudbuild.yaml`**

```yaml
substitutions:
  _REGION: us-central1
  _REPO: anima
  _SERVICE: mcp-server

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: E2_HIGHCPU_8

steps:
  - id: build
    name: gcr.io/kaniko-project/executor:latest
    args:
      - --dockerfile=mcp-server/Dockerfile
      - --context=mcp-server
      - --destination=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/mcp-server:$COMMIT_SHA
      - --destination=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/mcp-server:latest
      - --cache=true
      - --cache-repo=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/mcp-server-cache

  - id: deploy
    name: gcr.io/google.com/cloudsdktool/cloud-sdk:latest
    entrypoint: gcloud
    args:
      - run
      - deploy
      - ${_SERVICE}
      - --image=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/mcp-server:$COMMIT_SHA
      - --region=${_REGION}
      - --platform=managed
      - --min-instances=1
      - --max-instances=10
      - --memory=512Mi
      - --cpu=1
      - --port=8080
      - --concurrency=80
      - --allow-unauthenticated
      - --set-env-vars=NODE_ENV=production
      - --set-secrets=ANIMA_API_URL=API_URL:latest

images:
  - ${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/mcp-server:$COMMIT_SHA
```

Memory is 512Mi (vs 256Mi per old service) since all domains load together. `min-instances=1` — the whole point of the refactor.

- [ ] **Step 7.3: Write `deploy.sh`**

```bash
#!/bin/bash
set -euo pipefail
PROJECT_ID="anima-labs"
REGION="us-central1"
REPO="anima"
TAG="${1:-latest}"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/mcp-server:$TAG"

docker build --platform=linux/amd64 -t "$IMAGE" -f mcp-server/Dockerfile mcp-server/
docker push "$IMAGE"
gcloud run deploy mcp-server \
  --image="$IMAGE" --region="$REGION" --project="$PROJECT_ID" \
  --platform=managed --min-instances=1 --max-instances=10 \
  --memory=512Mi --cpu=1 --port=8080 --concurrency=80 \
  --allow-unauthenticated \
  --set-env-vars=NODE_ENV=production \
  --set-secrets=ANIMA_API_URL=API_URL:latest
```

Make it executable: `chmod +x mcp-server/deploy.sh`.

- [ ] **Step 7.4: Commit**

```bash
git add mcp-server/Dockerfile mcp-server/cloudbuild.yaml mcp-server/deploy.sh
git commit -m "feat(mcp-server): Dockerfile, Cloud Build, deploy script"
```

---

## Task 8: First deploy

- [ ] **Step 8.1: Build and push image**

Run:
```
cd .. # back to repo root if needed
./mcp-server/deploy.sh v0.1.0-consolidation
```

Expected: image pushes, Cloud Run deploys, new service URL printed.

- [ ] **Step 8.2: Verify all 6 domains**

Capture the URL (e.g. `https://mcp-server-v7ar7whcsq-uc.a.run.app`). Run the same smoke-test calls from Task 6.3 against it with a real `sk_test_` key. All six domains must initialize and return a non-empty `tools/list`.

- [ ] **Step 8.3: Check warm-start metrics**

Run:
```
curl -s https://mcp-server-v7ar7whcsq-uc.a.run.app/health | jq '.uptimeSeconds, .sessions'
```

Wait 5 minutes, re-run. `uptimeSeconds` should keep climbing (min-instances=1 keeps container warm). If it resets to 0, min-instances didn't take — check service config.

- [ ] **Step 8.4: Update the Anima MCP connector registry pointer**

The Cowork-facing Anima connector today points at `https://mcp-agent-v7ar7whcsq-uc.a.run.app/mcp`. Update wherever the connector definition lives (likely in the Anima console UI or in a registry config) to use `https://mcp-server-v7ar7whcsq-uc.a.run.app/agent`. Repeat per-domain connector definition if there are multiple.

If the connector definition is in this repo, grep for the old URLs first:
```
grep -rn "mcp-agent-v7ar7whcsq\|mcp-email-v7ar7whcsq\|mcp-phone-v7ar7whcsq\|mcp-platform-v7ar7whcsq\|mcp-vault-v7ar7whcsq" . 2>/dev/null | grep -v node_modules
```
and update each hit.

- [ ] **Step 8.5: End-to-end verify from Claude Cowork**

Trigger a tool call against the Anima MCP from Cowork (e.g. `List_Agents`). Confirm it succeeds — the original bug that started this refactor.

- [ ] **Step 8.6: Commit any connector config / URL updates**

```bash
git add <files>
git commit -m "chore: point connector config to unified mcp-server URLs"
```

---

## Task 9: Decommission old infrastructure

Only run this after Task 8 verification passes.

- [ ] **Step 9.1: Delete old Cloud Run services**

```bash
for s in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault; do
  gcloud run services delete "$s" --region=us-central1 --project=anima-labs --quiet
done
```

Expected: each prints `Deleted service [<name>]`.

- [ ] **Step 9.2: Delete old Cloud Build triggers (if any were set up per service)**

```
gcloud builds triggers list --project=anima-labs --format="value(name)" | grep -E "mcp-(agent|email|phone|platform|vault)"
```

For each matching trigger: `gcloud builds triggers delete <name> --project=anima-labs --quiet`.

- [ ] **Step 9.3: Delete old Artifact Registry repositories / images**

```bash
for img in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault; do
  gcloud artifacts docker images list us-central1-docker.pkg.dev/anima-labs/anima/$img --format="value(IMAGE)" 2>/dev/null | while read ref; do
    gcloud artifacts docker images delete "$ref" --delete-tags --quiet 2>/dev/null || true
  done
done
```

The `anima` repository itself stays — other images live there.

- [ ] **Step 9.4: Delete old GitHub repos and local checkouts**

After confirming the new `mcp-server` service is serving production traffic and the `pre-consolidation` tags are in place on each old repo:

```bash
for r in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault mcp-core; do
  gh repo delete anima-labs-ai/$r --yes
done
```

Then delete the local checkouts:
```bash
cd /Users/diyanbogdanov/projects/agenticmail
rm -rf mcp-agent mcp-email mcp-phone mcp-platform mcp-vault mcp-core mcp-deploy
```

**This is irreversible.** The `pre-consolidation` tags are gone with the repos. If you want a forever-reference, push the tags to `mcp-server` as lightweight archive refs before deleting:
```
for d in mcp-agent mcp-email mcp-phone mcp-platform mcp-vault mcp-core; do
  (cd /Users/diyanbogdanov/projects/agenticmail/$d && \
   git bundle create /tmp/$d-archive.bundle --all)
done
# Then commit bundles to mcp-server/archives/ if desired, or store elsewhere.
```
Skip the bundling if you genuinely want a clean break.

- [ ] **Step 9.5: Remove references from other code**

Grep broadly — there are SDKs and docs that likely reference the old URLs or package names:
```
grep -rn "mcp-agent\|mcp-email\|mcp-phone\|mcp-platform\|mcp-vault\|@anima-labs/mcp-core" . 2>/dev/null | grep -v node_modules | grep -v .git/
```

Expected hits live in:
- `anima/apps/*` (API docs, possibly a public registry of MCP URLs)
- `node/`, `python/`, `go/` SDKs (client helpers)
- `docs/`
- Root-level `.md` files

For each, update the reference to the new unified URL + path (e.g. `mcp-email-xxx/mcp` → `mcp-server-xxx/email`). Run the relevant typecheck / test / docs-build after each package update.

- [ ] **Step 9.6: Update `ROADMAP.md` and any deploy docs**

Remove references to per-domain MCP services; describe the consolidated architecture.

- [ ] **Step 9.7: Commit the deletions**

```bash
git add -A
git commit -m "chore: remove legacy per-domain MCP packages and update references"
```

- [ ] **Step 9.8: Final verification**

Run:
```
cd mcp-server && bun test && bun run typecheck
```
Expected: all tests pass, typecheck clean.

From the repo root:
```
grep -rln "mcp-agent\|mcp-email\|mcp-phone\|mcp-platform\|mcp-vault\|@anima-labs/mcp-core" . 2>/dev/null | grep -v node_modules | grep -v .git/ | grep -v .worktrees/
```
Expected: zero hits (outside of `mcp-server/` internals if any).

---

## Task 10: Ship

Since `mcp-server` is a brand-new repo with a fresh history and no existing consumers, we push straight to `main` — there is no legacy branch to rebase against or PR to open for merge approval. Review happens via the per-task spec-and-quality gates already run during execution.

- [ ] **Step 10.1: Push all commits to origin/main**

```
cd /Users/diyanbogdanov/projects/agenticmail/mcp-server
git push -u origin main
```

Expected: GitHub shows all commits from Tasks 1 through 9.

- [ ] **Step 10.2: Create a release tag marking the initial consolidation**

```
git tag -a v0.1.0 -m "Initial consolidation: unified mcp-server replacing 6 per-domain repos"
git push origin v0.1.0
```

- [ ] **Step 10.3: Write a repo README badge/summary block**

Ensure the `mcp-server` README explains what it replaces and links to the archived histories (the git bundles from Step 9.4, if you chose to preserve them). No PR — commit directly to main.

---

## Rollback plan

If the new `mcp-server` service misbehaves post-deploy and you haven't yet done Task 9:
1. Redirect the Anima MCP connector back to `mcp-agent-v7ar7whcsq-uc.a.run.app/mcp` etc.
2. The old Cloud Run services still exist and have `min-instances=0` — they'll cold-start once and resume serving.

If you've already completed Task 9, rollback requires re-deploying the six old services from a pre-consolidation commit. Tag `pre-consolidation` on main before starting Task 9 to make this fast:
```
git tag pre-consolidation origin/main
git push origin pre-consolidation
```

## Out of scope (deliberate non-goals)

- **No backwards-compat aliases.** The old URLs die. This is explicit per spec: "no clients today."
- **No per-domain version pinning.** All tool groups move in lockstep under one package version.
- **No plugin / dynamic tool-group loading.** Factories are compiled in. Shape 1 was chosen over Shape 2 for this reason.
- **No Custom Domain (`mcp.useanima.sh`) wiring.** That cert is broken today; DNS/cert work is a separate plan.

## Self-review checklist (completed by plan author)

1. **Spec coverage:**
   - [x] "Consolidate 6 MCP servers into 1 package" — Tasks 1, 2, 4a–4f
   - [x] "Path-routed endpoints (flat paths)" — Task 3 + Task 5
   - [x] "Delete old packages and Cloud Run services" — Task 9
   - [x] "One Dockerfile, one Cloud Build, one min-instances=1 service" — Tasks 7-8
   - [x] "Fix the Cowork cold-start bug that started this" — Step 8.5 verifies

2. **Placeholder scan:**
   - No "TBD", "implement later", or "similar to Task N" — every file-copy step lists exact source/dest; every factory step points to the exact file to mirror from Task 4a.4; every import rewrite gives the exact sed command.
   - Factory code for domains b/c/d/e/f is marked "mirror 4a.4" — this is the one acceptable DRY concession since the structure is truly identical. If an engineer reads out of order they'll read 4a.4 and know what to build.

3. **Type consistency:**
   - `McpAuthContext` gains `client: ApiClient` in Task 5 (noted inline in Step 5.3); `McpSession` internally does not need it since the client is captured in closure via the `wrap()` helper in `index.ts`.
   - `DomainFactories` = `Record<string, () => McpServer>` — same signature used in Task 3 tests, Task 3 implementation, and Task 5 entry point.
   - `buildAgentServer(client: ApiClient) => McpServer` — this signature repeats for email/phone/platform/vault factories.
