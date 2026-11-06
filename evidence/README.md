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
- `phase5/`: the ZAP report, the policy, the pipeline run that blocks and then
  passes.
- `phase6/`: the gate-by-gate scorecard.

Raw scanner dumps, if kept, go under a `raw/` subfolder, which is git-ignored.
