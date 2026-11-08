#!/usr/bin/env python3
"""Phase 5 dynamic access-control probe.

Calls the privileged balance-adjustment route without any credentials and records
whether it is reachable. In the planted state the route has no authorisation check,
so the unauthenticated call succeeds (HTTP 2xx), which is a high-severity broken
access control finding. After the remediation the route rejects the call (HTTP 401)
and the probe records no finding. The result is written to dast-findings.json, which
the policy gate reads to decide whether the release may proceed.

This is a measurement step. It exits non-zero only when the target cannot be reached
or returns an unexpected status, so that a broken target can never be mistaken for a
passing control. The binding release decision belongs to the policy gate, not here.
"""
import json
import sys

import httpx

# A constant, in-pipeline target: the ephemeral service started by the dast job.
TARGET = "http://localhost:8000/admin/accounts/1/adjust?amount=100"

findings = []
status = None
try:
    response = httpx.post(TARGET, timeout=10.0)
    status = response.status_code
except httpx.HTTPError as exc:
    print(f"probe error: could not reach the target: {exc}", file=sys.stderr)

if status is not None and 200 <= status < 300:
    findings.append(
        {
            "id": "broken-access-control",
            "severity": "high",
            "route": "POST /admin/accounts/{account_id}/adjust",
            "detail": f"privileged route reachable without authentication (HTTP {status})",
        }
    )
    print(f"FINDING: admin route reachable unauthenticated (HTTP {status})")
elif status in (401, 403):
    print(f"OK: admin route rejected the unauthenticated call (HTTP {status})")
else:
    print(f"probe inconclusive: unexpected status {status}", file=sys.stderr)
    sys.exit(1)

high_or_critical = sum(1 for finding in findings if finding["severity"] in ("high", "critical"))
result = {"high_or_critical": high_or_critical, "findings": findings}

with open("dast-findings.json", "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)

print(f"wrote dast-findings.json: high_or_critical={high_or_critical}")
