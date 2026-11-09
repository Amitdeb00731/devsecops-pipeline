# Pipeline security report

This report records the delivery pipeline as a control. It lists each gate in the
order it runs, states the control the gate enforces, and for every gate shows the
planted weakness it was proven against, the run that blocked the weakness, and the
remediation that cleared it, with the evidence cited. The gates were built and proven
on the live repository; each is shown failing a known-bad input first and then
passing once the input is fixed, so the evidence proves the control operates rather
than merely exists.

The test application in [`app/`](../app/README.md) is a deliberately insecure
harness. Its weaknesses are planted and documented so each gate has a genuine finding
to catch; the remediation commits remove them, and the final state of the repository
is clean.

## The pipeline at a glance

```
Developer  ->  Pull request  ->  Continuous integration  ->  Artefact  ->  Release gate  ->  main
pre-commit     branch protection   secrets, SAST, SCA, SBOM    image, IaC,    DAST + policy
hooks          review, checks                                  signing        (blocks)
```

The full pipeline, gate-logic and control-mapping diagrams are in
[docs/architecture-diagrams.md](../docs/architecture-diagrams.md).

## Gate by gate

### 1. Change control: branch protection

**Control.** No change reaches `main` without a pull request, one approving review
from a code owner, the required status check passing, a verified signature and linear
history; force pushes are blocked. This is the change-management and
segregation-of-duties control.

**Proven by.** Attempting the actions the control forbids. A direct push to `main` is
rejected by the server citing three rules at once (GH013), and a pull request shows
its checks passing but merging blocked on the required review, which the author
cannot supply for their own change.

**Evidence.** [`evidence/phase1/`](../evidence/phase1/): the Active `protect-main`
ruleset, the blocked direct push, the pull request that cannot merge without an
approver, and a verified signed commit. Full write-up in
[docs/01-pipeline-foundation.md](../docs/01-pipeline-foundation.md).

### 2. Secret scanning

**Control.** A secret cannot be committed, pushed or merged. The control runs in
three places: a pre-commit Gitleaks hook on the developer's machine, GitHub push
protection at the server, and Gitleaks and GitGuardian in continuous integration.

**Weakness.** A hard-coded API token in `app/main.py` and a committed `.env` holding
synthetic AWS credentials.

**Blocked then cleared.** The pre-commit hook rejected the commit, push protection
refused the push with a GH013 violation, and the CI secret scan failed the pull
request. After the token was moved to an environment variable read at runtime and the
branch history purged of the synthetic value, every check passed.

**Evidence.** [`evidence/phase2/`](../evidence/phase2/) (`01`, `02`, `03`, `05`).
Full write-up in [docs/02-secrets-sast.md](../docs/02-secrets-sast.md).

### 3. Static application security testing

**Control.** Human-readable code is analysed for vulnerabilities on every pull
request by CodeQL and Semgrep, with findings raised in the security tab and set as
required status checks in the ruleset.

**Weakness.** A SQL query built by string concatenation in the account-lookup route.

**Blocked then cleared.** CodeQL flagged the injection as a tainted data-flow problem
at the exact line and failed the pull request. The remediation parameterised the
query, after which the check passed. Semgrep's registry rules did not flag this
particular raw pattern where CodeQL's data-flow analysis did, which is the reason the
pipeline runs more than one analyser.

**Evidence.** [`evidence/phase2/`](../evidence/phase2/) (`04`, `05`). Full write-up in
[docs/02-secrets-sast.md](../docs/02-secrets-sast.md).

### 4. Dependency scanning, SBOM and Dependabot

**Control.** Known-vulnerable dependencies are flagged and blocked by pip-audit and
Trivy, a CycloneDX software bill of materials is produced and retained on every
build, and Dependabot raises upgrade pull requests on an ongoing basis.

**Weakness.** PyJWT pinned to 2.3.0, which carries an algorithm-confusion flaw
(CVE-2022-29217) among others.

**Blocked then cleared.** pip-audit and Trivy both failed the pull request on the
planted dependency. The upgrade to PyJWT 2.15.1, the same version Dependabot
independently proposed, cleared both scanners, and the SBOM recorded the patched
inventory.

**Evidence.** [`evidence/phase3/`](../evidence/phase3/) (`01` to `04`, and the
retained [`app-sbom.cdx.json`](../evidence/phase3/app-sbom.cdx.json)). Full write-up
in [docs/03-dependencies-sbom.md](../docs/03-dependencies-sbom.md).

### 5. Container image scanning

**Control.** The container image is built and scanned by Trivy, which fails the build
on a HIGH or CRITICAL operating-system or language finding.

**Weakness.** A Dockerfile on an end-of-life Debian base, running as root and
unpinned.

**Blocked then cleared.** The scan failed with fourteen HIGH operating-system
findings and three HIGH Python findings. A digest-pinned `python:3.12-slim-bookworm`
base running as a non-root user cleared the scan.

**Evidence.** [`evidence/phase4/`](../evidence/phase4/) (`01`, `02`, `05`). Full
write-up in [docs/04-container-iac.md](../docs/04-container-iac.md).

### 6. Infrastructure-as-code scanning

**Control.** The Terraform is scanned by Checkov as a blocking gate, with Trivy
configuration scanning as a second, reporting source.

**Weakness.** A security group opening the management port to `0.0.0.0/0`.

**Blocked then cleared.** Checkov failed the build on the open ingress rule. The
remediation restricted the ingress to a trusted administrative CIDR, after which the
gate passed.

**Evidence.** [`evidence/phase4/`](../evidence/phase4/) (`04`, `05`). Full write-up
in [docs/04-container-iac.md](../docs/04-container-iac.md).

### 7. Artefact integrity: signing and provenance

**Control.** On the merge to `main`, the image is pushed to the registry, signed
keylessly with cosign using the workflow's OIDC identity, the signature is verified
in the pipeline, and SLSA build provenance is attached, so the artefact's origin is
verifiable. In this build the image scan and the signing run as separate builds of
the same source commit; binding both to a single immutable digest, so the signed
artefact is provably the scanned one, is recorded as a hardening in the
[controls mapping](controls-mapping.md).

**Proven by.** The signing run on `main`. cosign signed the image, `cosign verify`
passed its three checks against the workflow identity and the GitHub Actions issuer,
and the provenance was recorded in the Rekor transparency log, on the repository's
Attestations page and in the registry.

**Evidence.** [`evidence/phase4/`](../evidence/phase4/) (`06` to `09`,
[`signature-verification.txt`](../evidence/phase4/signature-verification.txt) and the
[attestation](../evidence/phase4/attestation-65050745.sigstore.json)), from run
`42484821656`. Full write-up in [docs/04-container-iac.md](../docs/04-container-iac.md).

### 8. Dynamic application security testing

**Control.** The running service is tested at runtime. An OWASP ZAP baseline runs as
the breadth check, and an access-control probe calls the privileged route with no
credentials and records the result. The probe is the authoritative finding.

**Weakness.** A privileged balance-adjustment route with no authorisation check,
which no static analyser flags because the code is syntactically correct.

**Blocked then cleared.** On the planted commit the probe reached the route
unauthenticated (HTTP 200) and recorded a high-severity broken-access-control
finding. After an authorisation check was added that rejects an unauthenticated call
with HTTP 401, the probe was rejected and the finding cleared.

**Evidence.** [`evidence/phase5/`](../evidence/phase5/):
[`blocked-run.txt`](../evidence/phase5/blocked-run.txt) (run `42489671561`),
[`passing-run.txt`](../evidence/phase5/passing-run.txt) (run `42519484769`) and the
[ZAP summary](../evidence/phase5/zap-baseline-summary.txt). Full write-up in
[docs/05-dynamic-policy-gate.md](../docs/05-dynamic-policy-gate.md).

### 9. The release policy gate

**Control.** A policy-as-code gate evaluates the Rego policy in
[`policy/release.rego`](../policy/release.rego) with Conftest. The policy denies a
release on any of three conditions: a high or critical dynamic finding, an unsigned
artefact, or an unapproved change. In this build the gate reads the dynamic finding
directly from the runtime test. The signature and the approval are enforced earlier
in the pipeline, by the signing job (cosign signs and verifies the image) and by
branch protection (a required, reviewed pull request), and are supplied to the gate
as asserted preconditions rather than re-verified inside the gate; re-verifying them
against the exact image digest and the pull-request review state is recorded as a
hardening in the [controls mapping](controls-mapping.md). A deny fails the build, so
a failing dynamic control blocks the release rather than being reported on and merged
anyway.

**Blocked then cleared.** On the planted commit the gate denied the release
(`release blocked: 1 high or critical dynamic finding(s)`, one of three policy tests
failing, build exit 1). After the remediation the finding cleared and all three
policy tests passed, so the gate allowed the release. The gate itself was unchanged
between the two runs; only the application changed.

**Evidence.** [`evidence/phase5/`](../evidence/phase5/):
[`blocked-run.txt`](../evidence/phase5/blocked-run.txt) and
[`passing-run.txt`](../evidence/phase5/passing-run.txt). Full write-up in
[docs/05-dynamic-policy-gate.md](../docs/05-dynamic-policy-gate.md).

## Scorecard

Each planted weakness and the control that catches it, with the final state of the
repository. "Caught and fixed" means the gate blocked the weakness and the
remediation cleared it; "Enforced" means a control that is active on every change
rather than a one-off finding.

| # | Gate | Control type | Weakness proven against | Outcome |
| --- | --- | --- | --- | --- |
| 1 | Branch protection | Change control | Unreviewed or unsigned change to `main` | Enforced |
| 2 | Secret scanning | Prevent and detect | Hard-coded token; committed `.env` | Caught and fixed |
| 3 | SAST (CodeQL, Semgrep) | Detect | SQL injection by string concatenation | Caught and fixed |
| 4 | Dependency scan, SBOM, Dependabot | Detect and track | PyJWT 2.3.0 (CVE-2022-29217) | Caught and fixed |
| 5 | Image scanning (Trivy) | Detect | End-of-life base, running as root | Caught and fixed |
| 6 | IaC scanning (Checkov, Trivy) | Detect | Management port open to `0.0.0.0/0` | Caught and fixed |
| 7 | Signing and provenance (cosign, SLSA) | Integrity | Unsigned, unverifiable artefact | Enforced |
| 8 | DAST (ZAP, access-control probe) | Detect | Privileged route with no authorisation | Caught and fixed |
| 9 | Release policy gate (OPA, Conftest) | Enforce | A release that fails any release criterion | Enforced |

All seven planted application weaknesses are in the **Fixed** state in the final
repository, as recorded in [app/README.md](../app/README.md). No planted weakness
remains in the head of the default branch.

## What this does and does not prove

Passing these gates is assurance of process, not a guarantee of secure software. The
pipeline proves that a defined set of controls runs on every change and that an
insecure or unapproved change is blocked rather than merely reported. It does not
prove the absence of every vulnerability: a scanner finds the classes of defect it
knows, a dynamic test exercises the paths it is given, and a policy gate enforces the
criteria it is told to enforce. The release gate's binding check in this build is the
dynamic finding; the signature and approval it also requires are enforced elsewhere
in the pipeline and asserted to the gate, as set out in the controls mapping. The
value is that the controls are automatic, consistent and evidenced, so security and
approval are properties of the delivery process rather than of any one person
remembering to check. The known limitations of the lab, in particular the
single-person segregation-of-duties accommodation, the asserted gate preconditions
and the separate scan and signing builds, are stated in
[controls-mapping.md](controls-mapping.md).
