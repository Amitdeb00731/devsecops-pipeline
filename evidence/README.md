# Evidence

Per-phase evidence that each gate works. The pattern, carried from Builds 1 and 2,
is to show the control blocking a known-bad input first, then passing after the
fix, so the evidence proves the gate operates rather than merely exists.

- `phase1/`: the branch-protection ruleset, a blocked direct push, a pull request
  that cannot merge without an approver, a verified signed commit.
- `phase2/`: the failing run that blocks the planted secret and injection, the
  passing run after remediation, the findings in the security tab.
- `phase3/`: the dependency vulnerability report before and after the upgrade, the
  SBOM, the Dependabot configuration.
- `phase4/`: the image and IaC scans and fixes, a verified signature, a rejected
  unsigned image, the provenance attestation.
- `phase5/`: the dynamic test and the policy gate, the pipeline run that blocks and
  then passes, and the ZAP baseline summary.

The Phase 6 reports, including the gate-by-gate scorecard, are in
[`report/`](../report/README.md) rather than here, since they draw on the evidence
from every phase.

Raw scanner dumps, if kept, go under a `raw/` subfolder, which is git-ignored.
