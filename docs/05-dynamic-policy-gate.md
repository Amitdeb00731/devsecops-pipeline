# Phase 5: Dynamic testing and the policy gate

**Goal:** a release gate that blocks on a failing control, not just a report. Deploy
the application, test it at runtime, and add a policy-as-code gate that fails the
pipeline when a high-severity dynamic finding is present. The gate is proven by a
release that is correctly blocked, then allowed after remediation.

## 5.1 Deploy to an ephemeral target

Run the application inside the workflow so the dynamic test has a live target with no
standing cost. Install it, start it with uvicorn in the background, and wait for the
health endpoint before testing:

```yaml
  dast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r app/requirements.txt
      - name: Start the application
        working-directory: app
        run: |
          nohup uvicorn main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
          for _ in $(seq 1 30); do
            curl -fsS http://localhost:8000/health >/dev/null 2>&1 && break
            sleep 1
          done
```

The optional cloud path deploys the same image into the Build 2 AWS lab under its
existing budget guardrails, which links the builds and shows the pipeline delivering
into a controlled cloud account. The ephemeral in-workflow service is the default so
the build stays free and reproducible.

## 5.2 Dynamic testing: a breadth scan and an authoritative probe

Two runtime checks run against the live service. The ZAP baseline is the breadth
check: it crawls the application as a client would and reports passive issues such as
missing security headers. It runs non-blocking, because a baseline crawl of a headless
API produces advisory warnings rather than a pass or fail verdict on the control under
test:

```yaml
      - name: ZAP baseline scan (breadth, non-blocking)
        run: |
          docker run --rm --network host \
            -v "$GITHUB_WORKSPACE/.zap:/zap/wrk/:rw" \
            ghcr.io/zaproxy/zaproxy:stable \
            zap-baseline.py -t http://localhost:8000 -c rules.tsv -r zap-report.html -I || true
```

The authoritative finding comes from a focused access-control probe. It calls the
privileged route with no credentials and records the result, so the control under
test, whether an unauthenticated caller can reach a privileged operation, is checked
directly rather than inferred from a passive crawl:

```yaml
      - name: Access-control probe (authoritative finding)
        run: python scripts/dast_access_control_check.py
```

The probe writes `dast-findings.json` with the high-or-critical count that the policy
gate reads. The `.zap/rules.tsv` file records which ZAP alerts are enforced and which
are accepted with a reason, in the same honest style as the earlier builds.

## 5.3 The policy gate (policy as code)

The gate is the centrepiece: a single, explicit decision that evaluates the release
criteria and decides whether the release may proceed. Write the policy in Rego and
evaluate it with Conftest (Open Policy Agent).

`policy/release.rego` denies a release on a high or critical finding, an unsigned
artefact or an unapproved change:

```rego
package release

import rego.v1

deny contains msg if {
  input.scans.high_or_critical > 0
  msg := sprintf("release blocked: %d high or critical dynamic finding(s)", [input.scans.high_or_critical])
}

deny contains msg if {
  not input.artifact.signed
  msg := "release blocked: image is not signed"
}

deny contains msg if {
  not input.change.approved
  msg := "release blocked: change not approved by a code owner"
}
```

The gate job reads the dynamic finding from the runtime test and evaluates the policy.
The signature and the approval are enforced earlier in the pipeline, by the signing
job (which signs the image with cosign and verifies the signature) and by branch
protection (which requires a reviewed pull request); they are supplied to the gate as
asserted preconditions here rather than re-verified inside the gate:

```yaml
  policy-gate:
    needs: dast
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: dast-findings
      - name: Assemble the gate input
        run: |
          # The dynamic finding is read from the runtime test. signed and approved are
          # asserted preconditions, enforced by the sign job and by branch protection;
          # re-verifying them in the gate against the exact image digest and the
          # pull-request review state is a recorded hardening.
          HIGH=$(jq '.high_or_critical' dast-findings.json)
          jq -n --argjson high "$HIGH" \
            '{scans: {high_or_critical: $high}, artifact: {signed: true}, change: {approved: true}}' \
            > gate-input.json
      - name: Install Conftest
        run: |
          curl -sSL -o conftest.tar.gz https://github.com/open-policy-agent/conftest/releases/download/v0.56.0/conftest_0.56.0_Linux_x86_64.tar.gz
          tar xzf conftest.tar.gz conftest && sudo mv conftest /usr/local/bin/conftest
      - run: conftest test gate-input.json --policy policy --namespace release
```

If the policy denies, the job fails and the release cannot proceed. This is the
control that makes the dynamic finding binding rather than advisory.

## 5.4 Prove the gate, then allow

1. With a high-severity dynamic finding present, the policy gate fails and the release
   is blocked. Capture the blocked run.
2. Remediate the finding.
3. Re-run. The gate passes and the release proceeds. The blocked and the passing
   runs are the evidence that the control is binding.

## Phase 5 deliverables

- The dast job (ephemeral in-workflow service, optional AWS deploy) and `.zap/rules.tsv`.
- `policy/release.rego` and the policy-gate job.
- `evidence/phase5/`: the ZAP report, the policy, and the pipeline run that blocks
  and then passes.
- Commit: `Phase 5: dynamic testing and the policy gate`.

## Checks before moving on

- The application is deployed and tested at runtime in the pipeline.
- The policy gate blocks a release on a high-severity dynamic finding and allows it
  once the finding is resolved. The policy also denies an unsigned artefact or an
  unapproved change; in this build those two are enforced by the signing job and by
  branch protection and are asserted to the gate as preconditions.
- The accepted ZAP alerts are documented with a reason.
- The gate mapping is recorded: SSDF PW.8 and RV.1, OWASP SAMM Verification.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
