# Phase 5: Dynamic testing and the policy gate

**Goal:** a release gate that blocks on a failing control, not just a report. Deploy
the application, test it at runtime, and add a policy-as-code gate that fails the
pipeline when a high-severity finding or a missing approval is present. The gate is
proven by a release that is correctly blocked, then allowed after remediation.

## 5.1 Deploy to an ephemeral target

Run the signed image from Phase 4 as a service inside the workflow, so the dynamic
test has a live target with no standing cost:

```yaml
  dast:
    needs: sign
    runs-on: ubuntu-latest
    services:
      app:
        image: ghcr.io/${{ github.repository }}:${{ github.sha }}
        ports:
          - 8000:8000
    steps:
      - uses: actions/checkout@v4
```

The optional cloud path deploys the same image into the Build 2 AWS lab (the ECS or
App Runner target under its existing budget guardrails), which links the builds and
shows the pipeline delivering into a controlled cloud account. The ephemeral
container is the default so the build stays free and reproducible.

## 5.2 Dynamic testing with OWASP ZAP

Run the ZAP baseline scan against the running service. It exercises the application
as a client would and reports runtime issues the static analysers cannot see, such
as missing security headers or the authorisation gap in a live request:

```yaml
      - name: ZAP baseline scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: http://localhost:8000
          rules_file_name: .zap/rules.tsv
          fail_action: true
```

`fail_action: true` makes a confirmed finding fail the job. The `.zap/rules.tsv`
file records which alerts are enforced and which are accepted with a reason, in the
same honest style as the earlier builds.

## 5.3 The policy gate (policy as code)

The gate is the centrepiece: a single, explicit decision that reads the evidence
from the earlier stages and decides whether the release may proceed. Write the
policy in Rego and evaluate it with Conftest (Open Policy Agent).

`policy/release.rego` denies a release when any gate failed or an approval is
missing:

```rego
package release

deny[msg] {
  input.scans.high_or_critical > 0
  msg := sprintf("release blocked: %d high or critical findings", [input.scans.high_or_critical])
}

deny[msg] {
  not input.change.approved
  msg := "release blocked: change not approved by a code owner"
}

deny[msg] {
  not input.artifact.signed
  msg := "release blocked: image is not signed"
}
```

A gate job collects the results of the scans, the signature check and the approval
state into a small JSON document and evaluates it:

```yaml
  policy-gate:
    needs: [dast]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: curl -L -o conftest.tar.gz https://github.com/open-policy-agent/conftest/releases/download/v0.56.0/conftest_0.56.0_Linux_x86_64.tar.gz && tar xzf conftest.tar.gz
      - run: ./conftest test gate-input.json --policy policy
```

If the policy denies, the job fails and the release cannot proceed. This is the
control that makes every earlier scan binding rather than advisory.

## 5.4 Prove the gate, then allow

1. With a high-severity finding present, or the approval missing, the policy gate
   fails and the release is blocked. Capture the blocked run.
2. Remediate the finding and obtain the approval.
3. Re-run. The gate passes and the release proceeds. The blocked and the passing
   runs are the evidence that the control is binding.

## Phase 5 deliverables

- The dast job (ephemeral container, optional AWS deploy) and `.zap/rules.tsv`.
- `policy/release.rego` and the policy-gate job.
- `evidence/phase5/`: the ZAP report, the policy, and the pipeline run that blocks
  and then passes.
- Commit: `Phase 5: dynamic testing and the policy gate`.

## Checks before moving on

- The application is deployed and tested at runtime in the pipeline.
- The policy gate blocks a release on a high-severity finding, a missing signature
  or a missing approval, and allows it once each is resolved.
- The accepted ZAP alerts are documented with a reason.
- The gate mapping is recorded: SSDF PW.8 and RV.1, OWASP SAMM Verification.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
