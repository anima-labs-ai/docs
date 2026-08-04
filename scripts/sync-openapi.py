#!/usr/bin/env python3
"""Pull the live OpenAPI spec and write it here if it differs.

`docs/openapi.json` is GENERATED in the anima monorepo from the oRPC contracts
and was copied across by hand. Nothing failed when the copy was skipped, so the
spec integrators read went stale twice — once documenting 2 dead routes while
missing 19 live ones, then again on schemas, where annual billing was
purchasable while the published checkout had no `interval` field to ask for it
with. anima#470 added a canary that NOTICES the drift; this closes the loop by
doing the copy.

The source is the deployed API's own `GET /openapi.json`, which `server.ts`
builds from the same contracts and the same `openapi-metadata.ts` as the static
generator — verified byte-for-byte identical as parsed JSON. It is public, so
this needs no cross-repo token: the workflow writes only to its own repository.

Exit codes: 0 = in sync (nothing written), 10 = updated, 1 = refused.
A refusal is never a silent pass — see the guards below.
"""

import json
import os
import sys
import time
import urllib.request

SPEC_URL = os.environ.get("OPENAPI_SOURCE_URL", "https://api.useanima.sh/openapi.json")
TARGET = os.environ.get("OPENAPI_TARGET", "docs/openapi.json")

# A truncated response, an error page behind a 200, or a misrouted host would
# all parse as "some JSON" and quietly blank the published spec. These are the
# floor: the real document carries ~212 paths, so 100 leaves ample room for
# legitimate route removals while refusing anything that looks like a stub.
MIN_PATHS = 100
EXPECTED_TITLE = "Anima API"


def fail(message: str) -> "None":
    print(f"REFUSED: {message}", file=sys.stderr)
    sys.exit(1)


def fetch(url: str) -> str:
    last = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                # `status` is None for non-HTTP schemes (file://), which is what
                # the guard tests use as a source. Only enforce it when the
                # protocol actually reports one.
                status = getattr(response, "status", None)
                if status is not None and status != 200:
                    raise RuntimeError(f"HTTP {status}")
                return response.read().decode("utf-8")
        except Exception as error:  # noqa: BLE001 - reported, not swallowed
            last = error
            if attempt < 3:
                time.sleep(attempt * 2)
    fail(f"could not fetch {url} after 3 attempts: {last}")


def main() -> int:
    raw = fetch(SPEC_URL)

    try:
        live = json.loads(raw)
    except json.JSONDecodeError as error:
        fail(f"{SPEC_URL} did not return JSON: {error}")

    # Guards. Each one exists because passing it wrong would publish a broken
    # spec to real integrators, and none of them can be satisfied by an error
    # page or a partial read.
    if not isinstance(live, dict) or "openapi" not in live:
        fail("fetched document has no `openapi` key — not an OpenAPI spec")
    title = live.get("info", {}).get("title")
    if title != EXPECTED_TITLE:
        fail(f"fetched spec is titled {title!r}, expected {EXPECTED_TITLE!r}")
    paths = live.get("paths")
    if not isinstance(paths, dict) or len(paths) < MIN_PATHS:
        fail(f"fetched spec has {len(paths or {})} paths, below the {MIN_PATHS} floor")

    try:
        with open(TARGET, encoding="utf-8") as handle:
            current = json.load(handle)
    except FileNotFoundError:
        current = None

    if current == live:
        print(f"in sync: {len(paths)} paths, nothing to write")
        return 0

    # Match the generator's formatting exactly (`JSON.stringify(spec, null, 2)`
    # plus a trailing newline) so the only diff is real content.
    with open(TARGET, "w", encoding="utf-8") as handle:
        json.dump(live, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    def operations(spec):
        if not spec:
            return set()
        return {
            f"{method.upper()} {path}"
            for path, methods in spec.get("paths", {}).items()
            for method, op in methods.items()
            if isinstance(op, dict) and "responses" in op
        }

    before, after = operations(current), operations(live)
    added, removed = sorted(after - before), sorted(before - after)

    print(f"updated {TARGET}: {len(before)} -> {len(after)} operations")
    for op in added:
        print(f"  + {op}")
    for op in removed:
        print(f"  - {op}")

    # Written to the step summary so the PR body can quote it.
    summary = []
    if added:
        summary.append(f"**Added ({len(added)})**\n" + "\n".join(f"- `{o}`" for o in added))
    if removed:
        summary.append(f"**Removed ({len(removed)})**\n" + "\n".join(f"- `{o}`" for o in removed))
    if not added and not removed:
        summary.append("No routes added or removed — schema or description changes only.")
    with open("/tmp/openapi-sync-summary.md", "w", encoding="utf-8") as handle:
        handle.write("\n\n".join(summary) + "\n")

    return 10


if __name__ == "__main__":
    sys.exit(main())
