#!/usr/bin/env node
/**
 * Agent-surface guard (spec E10).
 *
 * llms.txt is the one file on this site whose entire purpose is to be eaten by
 * a language model. Mintlify builds it from the docs.json navigation PLUS an
 * auto-generated API-reference page for every operation in openapi.json — so
 * anything in that snapshot is taught, verbatim and unreviewed, to every model
 * that ingests our docs.
 *
 * That is how six `pods` endpoints came to be advertised there. Cards were
 * scrapped in May 2026 and pods are explicitly out of scope, and docs#23
 * deleted the pods PROSE pages accordingly — but openapi.json is a committed
 * snapshot refreshed from the monorepo (see README), and the refresh brought
 * the pods paths back with it. Net effect: a human reading the docs learned
 * nothing about pods, while every agent reading llms.txt learned they were a
 * product. Backwards, for an agent-native company.
 *
 * Deleting the paths once does not hold — the next refresh re-adds them. This
 * runs in CI so the reintroduction fails a PR instead of shipping. Same shape
 * as the `grep -r useanima.shs` release lint in the parity spec: the fix is the
 * gate, not the edit.
 *
 * If a scrapped area is ever un-scrapped, delete its entry here in the same PR
 * that ships it.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const openapiPath = join(here, "..", "openapi.json");

/**
 * Path prefixes that must never appear in the published API reference.
 * Keyed by the first path segment, so `/pods/{id}/usage` is caught by `pods`
 * while a legitimate path that merely CONTAINS the word is not: the A2A Agent
 * Card lives at `/agents/{agentId}/card`, and a naive substring match on "card"
 * would fail the build over our own identity feature.
 */
const FORBIDDEN_SEGMENTS = new Map([
	["pods", "pods are explicitly out of scope (OPENSPEC-COMPETITIVE-PARITY-2026-07 non-goals)"],
	["cards", "the cards/card-issuing product was scrapped 2026-05-09"],
	["x402", "x402/MPP crypto billing is explicitly out of scope"],
	["mpp", "x402/MPP crypto billing is explicitly out of scope"],
]);

const spec = JSON.parse(readFileSync(openapiPath, "utf8"));
const paths = Object.keys(spec.paths ?? {});

if (paths.length === 0) {
	console.error("check-agent-surfaces: openapi.json declares no paths — refusing to pass vacuously.");
	process.exit(1);
}

const violations = [];
for (const path of paths) {
	const first = path.split("/").filter(Boolean)[0]?.toLowerCase();
	const reason = first ? FORBIDDEN_SEGMENTS.get(first) : undefined;
	if (reason) {
		violations.push({ path, reason });
	}
}

if (violations.length > 0) {
	console.error("check-agent-surfaces: openapi.json documents scrapped or out-of-scope endpoints.\n");
	for (const { path, reason } of violations) {
		console.error(`  ${path}\n    ${reason}`);
	}
	console.error(
		"\nMintlify generates an API-reference page per operation, and those pages land in" +
			"\nllms.txt — so these would be taught to every model that ingests our docs." +
			"\nRemove them from docs/openapi.json (see README, 'API Reference'). If the area" +
			"\nis genuinely back, drop its entry from FORBIDDEN_SEGMENTS in this script.",
	);
	process.exit(1);
}

console.log(`check-agent-surfaces: ${paths.length} documented paths, no scrapped scope. OK`);
