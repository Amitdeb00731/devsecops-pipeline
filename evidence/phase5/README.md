# Phase 5 evidence: dynamic testing and the binding policy gate

This phase adds the last and most important control in the pipeline: a release gate
that **fails the build** on a live security finding, rather than reporting on it and
letting the merge proceed. It is proven the same way as every other gate in this
build, by showing it block a known-bad input first and then pass once the weakness is
fixed, so the evidence shows the control working, not merely present.

## The control under test

The test application carried one planted weakness forward to this phase: the
privileged balance-adjustment route `POST /admin/accounts/{account_id}/adjust` had
no authentication or authorisation check. No static analyser flags that as a bug,
because the code is syntactically fine; it is only wrong in its behaviour. That is
exactly the class of defect dynamic testing exists to catch, so it was left for
Phase 5 to prove at runtime.

## How the gate is built

The `release-gate` workflow runs two jobs on every pull request and every push to
`main`.

- **`dast`** deploys the application to an ephemeral target and tests it at runtime.
  It runs an OWASP ZAP baseline scan as the breadth check (non-blocking, reports to
  the run), then an access-control probe that calls the privileged route with no
  credentials and records the result in `dast-findings.json`. The probe is the
  authoritative finding: a 2xx response is a high-severity broken-access-control
  finding, a 401 or 403 is a pass.
- **`policy-gate`** reads the dynamic finding from the `dast` job and evaluates it
  with Conftest against the Rego policy in `policy/release.rego`. The policy denies a
  release on any of three conditions: a high or critical dynamic finding, an unsigned
  artefact, or an unapproved change. In this build the dynamic finding is read from a
  live result; the signature and the approval are enforced earlier, by the `sign` job
  and by branch protection, and are supplied to the gate as asserted preconditions
  rather than re-verified inside it. A deny fails the job, so a failing dynamic control
  blocks the release.

The gate makes the dynamic finding binding; the signature and approval it also
requires are enforced upstream in the pipeline and asserted to the gate as
preconditions. Re-verifying them in the gate against the exact image digest and the
pull-request review state is recorded as a hardening in
[`report/controls-mapping.md`](../../report/controls-mapping.md).

## Before and after, on one pull request

Both states were produced on pull request #19. The only thing that changed between
the two runs was the application; the gate was untouched.

### Before: the gate blocks the live finding

Commit `4c6e8c55`, with the route still unauthenticated. The probe reached the admin
route without credentials and the gate denied the release. See
[`blocked-run.txt`](blocked-run.txt) and screenshot `01-blocked-check.png`.

```
FINDING: admin route reachable unauthenticated (HTTP 200)
wrote dast-findings.json: high_or_critical=1

gate input: { "scans": { "high_or_critical": 1 }, "artifact": { "signed": true }, "change": { "approved": true } }

FAIL - gate-input.json - release - release blocked: 1 high or critical dynamic finding(s)
3 tests, 2 passed, 0 warnings, 1 failure, 0 exceptions
Process completed with exit code 1.
```

The signature and approval preconditions were asserted true; the single control the
gate evaluated from a live result, the dynamic finding, failed the job. The release
was blocked.

### After: the gate allows the remediated change

Commit `26372685`, with an authorisation check added to the route (a valid
`X-Admin-Token` header compared in constant time against `ADMIN_API_TOKEN`, rejecting
a missing or invalid token with HTTP 401, fail-closed when no token is configured).
The probe was now rejected, the finding cleared, and the gate allowed the release.
See [`passing-run.txt`](passing-run.txt) and screenshot `02-passing-checks.png`.

```
OK: admin route rejected the unauthenticated call (HTTP 401)
wrote dast-findings.json: high_or_critical=0

gate input: { "scans": { "high_or_critical": 0 }, "artifact": { "signed": true }, "change": { "approved": true } }

3 tests, 3 passed, 0 warnings, 0 failures, 0 exceptions
```

## Why the probe is the authoritative control

The ZAP baseline is a breadth check. The target is a headless machine-to-machine API
with no browseable root, so the ZAP spider receives HTTP 404 on `/` and its crawl is
shallow; the passive browser-hardening alerts in `.zap/rules.tsv` are accepted (WARN
with reasons) because there is no browser surface for a missing response header to
protect. A spider-driven scan will not, on its own, exercise a specific privileged
route. The access-control probe does exactly that: it calls the known route directly
and asserts the expected authorisation behaviour. ZAP provides breadth and a report;
the probe provides the binding depth, and the policy gate acts on the probe. The ZAP
summary is in [`zap-baseline-summary.txt`](zap-baseline-summary.txt).

## Files in this evidence pack

| File | What it shows |
| --- | --- |
| `blocked-run.txt` | The probe finding and the gate denial, captured from the failing run log |
| `passing-run.txt` | The cleared finding and the gate pass, captured from the passing run log |
| `zap-baseline-summary.txt` | The ZAP breadth-scan summary and why the probe is authoritative |
| `01-blocked-check.png` | The `release-gate / policy-gate` check failing on the pull request |
| `02-passing-checks.png` | The pull request checks all green after the remediation |

The gate itself is `.github/workflows/release-gate.yml`, the policy is
`policy/release.rego`, the probe is `scripts/dast_access_control_check.py`, and the
accepted passive alerts are in `.zap/rules.tsv`.

## Controls mapping

- **NIST SSDF PW.8 (test executable code to identify vulnerabilities):** the dynamic
  test exercises the running service and identifies the broken access control that
  static analysis cannot see.
- **NIST SSDF RV.1 (identify and confirm vulnerabilities on an ongoing basis):** the
  gate runs on every pull request and every push to `main`, so the check is
  continuous, not a one-off.
- **OWASP SAMM, Verification, Security Testing:** automated security testing built
  into the delivery pipeline with a defined pass or fail outcome.
- **Change and release control (SOX-style IT general controls):** the policy gate
  makes the release decision an enforced, auditable rule. The policy expresses the
  release criteria as code: a release must be approved, built from a signed artefact
  and free of high-severity dynamic findings, which is the segregation-of-duties and
  change-management control a bank's auditors test. In this build the gate evaluates
  the dynamic finding directly and takes the signature and approval as preconditions
  enforced earlier in the pipeline.
