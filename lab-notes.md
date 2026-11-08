# Lab notes: DevSecOps pipeline

The engineering log for Build 3: the decisions and fixes behind the build, in the
order they happened. Each phase adds its own entries as the work is done.

## Decisions

- **CI/CD platform: GitHub Actions.** The portfolio's repositories are already on
  GitHub; Actions is free for public repositories and is a platform a UK bank
  commonly asks about. No self-hosted runner is used.
- **Application stack: Python (FastAPI).** Small, readable, and well covered by the
  scanners (Bandit, Semgrep, pip-audit). Realistic for a bank microservice.
- **Target application: a purpose-built, labelled test harness.** Weaknesses are
  planted and documented rather than borrowed, so the repository is a controlled
  exercise, not careless code.
- **Dynamic-test target: an ephemeral container in the pipeline.** No standing
  cost, fully reproducible. An optional deploy to the Build 2 AWS lab links the
  builds.
- **Registry and signing: GitHub Container Registry and cosign (keyless).** Free,
  and keyless signing avoids storing a private key.

## Standing rules

- No real secrets committed. The only secrets are synthetic values for the
  secret-scanning test, removed afterwards.
- Every gate is proven by failing a known-bad input first, then passing after the
  fix. The failing run is kept as evidence.
- House style held throughout: no em or en dashes, British spelling, no
  placeholders, every claim carried by its evidence.

## Phase log

### Phase 1: pipeline and change-control foundation (2026-11-06)

**Situation.** The repository needed its delivery process to enforce change
management before any scanner was added.

**Task.** Make it impossible to reach `main` without review, passing checks, a
recorded approver and a verified signature.

**Action.** Added a FastAPI application skeleton with a health check and a test, a
baseline GitHub Actions `ci` workflow (ruff and pytest), `CODEOWNERS`, and the
`protect-main` ruleset: required pull request with one approval, dismiss stale
approvals, require Code Owners, require the `build-test` status check, require
signed commits, require linear history, block force pushes, no bypass. Configured
SSH commit signing and registered the signing key on the account.

**Result.** Verified on the live repository: a direct push to `main` is rejected
with all three controls cited (GH013), a pull request shows checks passing but
merging blocked on the required review, and a signed commit shows the Verified
badge. Evidence in `evidence/phase1/`.

**Fixes and lessons.**
- SSH signing produced "No signature" until `user.signingkey` and
  `gpg.ssh.program` were set with Windows paths via `cygpath`; the `~` path did not
  expand for signing.
- A commit shows Unverified until the commit's author email is a verified email on
  the GitHub account, separate from registering the signing key.
- Solo-lab limitation: one required approval plus no self-approval means no pull
  request can merge without an owner bypass. Recorded honestly; a real team has a
  separate approver.

### Phase 2: secrets and static analysis (2026-11-06)

**Situation.** With change control in place, the pipeline needed to catch insecure
code and leaked secrets before they could merge, both on the developer's machine
and in continuous integration.

**Task.** Prove, with a planted weakness, that secret scanning and static analysis
block a bad change and then pass once it is fixed.

**Action.** Added pre-commit hooks (Gitleaks, Bandit), a `security` workflow
(Gitleaks in CI, Semgrep with SARIF to the security tab) and a CodeQL workflow,
and enabled GitHub's native secret scanning and push protection. Planted a
hard-coded token, a `.env` credential, a string-concatenation SQL query and an
unauthenticated admin route in the test app, each labelled in `app/README.md`.

**Result.** Verified on the live repository: the pre-commit hook rejected the
commit, push protection blocked the push of the AWS keys (`GH013`), and the pull
request failed on `secret-scan` and CodeQL while `build-test` stayed green. After
remediation (token to an environment variable, parameterised query, and the branch
rewritten to purge the secret from history), the same pull request passed every
check. Evidence in `evidence/phase2/`.

**Fixes and lessons.**
- A pushed secret is compromised: deleting it in a later commit is not enough,
  because Gitleaks scans the whole history. The fix is to rewrite the branch to a
  clean commit and rotate the secret.
- Push protection catches known provider formats (AWS keys); the pipeline's own
  secret scanning catches generic tokens it does not recognise. Both are needed.
- CodeQL caught the SQL injection where Semgrep's registry rules did not, which is
  the case for running more than one analyser.
- A missing authorisation check is a design flaw that no static analyser flags, so
  it is left in and carried to the Phase 5 dynamic test.
- Pre-commit sets aside unstaged changes before running, so hooks must be run
  against staged files or they scan the previous clean version.

### Phase 3: dependencies, SBOM and supply chain (2026-11-06)

**Situation.** The pipeline could catch insecure code, but not a dependency that
was secure when written and later found vulnerable, and it kept no record of what
each build contained.

**Task.** Prove, with a planted vulnerable dependency, that dependency scanning and
the SBOM flag it and then pass after the upgrade, and that Dependabot keeps the
control running afterwards.

**Action.** Added a `supply-chain` workflow with three jobs: pip-audit and Trivy
(filesystem mode, HIGH and CRITICAL set to fail the job) as two independent
dependency scanners, and a Syft job that generates a CycloneDX SBOM and retains it
as a build artefact. Added `.github/dependabot.yml` for the pip and github-actions
ecosystems. Refreshed the baseline dependencies to current patched versions so the
only finding would be the planted one, then pinned PyJWT to 2.3.0.

**Result.** Verified on the live repository: `dep-audit` and `dep-trivy` both failed
on PyJWT 2.3.0 while `sbom` and every other gate passed; after upgrading PyJWT to
2.15.1 and committing the retained CycloneDX SBOM, the same pull request passed
every check. Dependabot independently raised the same PyJWT upgrade and bumps for
the pipeline's own Actions. Evidence in `evidence/phase3/`.

**Fixes and lessons.**
- Trivy was first pinned to `aquasecurity/trivy-action@0.24.0`, a tag that does not
  exist, because the action's tags are `v`-prefixed. The job failed at setup in a
  few seconds without scanning, which read as a catch but was not. Corrected to
  `@v0.36.0`. A red check is only evidence once you confirm it failed for the reason
  you intended, not on a broken configuration.
- The baseline has to be clean first. The original FastAPI and Starlette pins were
  themselves flagged by the current advisory database, so they were refreshed to
  patched versions before the single planted CVE was added, otherwise the gate
  could never reach green.
- A conflicted pull request does not run its Actions checks. The planted Phase 3 had
  already merged to `main`, so the remediation branch and `main` had each created
  the workflow file, and the checks sat waiting until the branch was rebuilt on
  current `main`.
- Dependabot activates from the default branch, so once its config reached `main` it
  immediately raised update pull requests. That is the ongoing control working.

### Phase 4: container and infrastructure-as-code security, signing (2026-11-08)

**Situation.** The pipeline scanned source and dependencies, but not the container
image that actually runs or the infrastructure that hosts it, and it could not
prove that the image reaching the registry was the one that passed the gates.

**Task.** Prove, with a planted weak Dockerfile and a planted over-permissive
Terraform rule, that the image scan and the infrastructure-as-code scan block a bad
artefact and then pass once it is fixed, and that the released image is signed and
its provenance recorded.

**Action.** Added a `container-iac` workflow with three jobs. `image-scan` builds the
image and scans it with Trivy (HIGH and CRITICAL with a fix available set to fail the
job). `iac-scan` runs Checkov as the blocking gate over the Terraform, with Trivy in
config mode as a second, report-only scanner that uploads to the security tab
(tfsec is deprecated and folded into Trivy, so it is not used). `sign` runs on the
push to `main` only: it pushes the image to GHCR, signs it keylessly with cosign
using the workflow's OIDC identity, verifies the signature, and attaches SLSA build
provenance with `actions/attest-build-provenance`. Planted a weak base image
(end-of-life Debian, running as root) and a security group opening the management
port to `0.0.0.0/0`.

**Result.** Verified on the live repository from the run logs, not the green ticks
alone. `iac-scan` failed on Checkov `CKV_AWS_24` (ingress 22 open to the world) and
`image-scan` failed with fourteen HIGH operating-system findings and three HIGH
Python findings, each for the intended reason. After remediation, a digest-pinned
`python:3.12-slim-bookworm` base running as a non-root user and the ingress
restricted to a trusted admin CIDR, both gates passed. On the merge to `main` the
`sign` job pushed the image (`sha256:eb064d86…`), cosign signed it, `cosign verify`
passed its three checks against the `container-iac.yml` identity and the GitHub
Actions issuer, and the SLSA provenance was recorded in the Rekor transparency log,
on the repository's Attestations page and in GHCR. Evidence in `evidence/phase4/`.

**Fixes and lessons.**
- A planted base image has to build, or the scanner never runs. The first planted
  base, `python:3.9-slim-buster`, could not install the app (FastAPI 0.162 needs
  Python 3.10 or newer), so the build failed and Trivy errored with no image to
  scan. That is a red check for the wrong reason. Corrected to a base that builds
  but is genuinely vulnerable (`python:3.10-slim-buster`) so the scan actually ran
  and caught the real findings.
- Trivy reported `setuptools` 70.3.0 as vulnerable (CVE-2025-47273) even after the
  installed `setuptools` was upgraded to a patched release. The cause is that Trivy
  also reads pip's bundled CycloneDX SBOM at `pip/_vendor/bom.cdx.json`, which lists
  pip's stripped-down vendored `setuptools` 70.3.0 (only `pkg_resources`, not the
  exploitable code path) regardless of what is installed. Trivy's own "third-party
  SBOM may lead to inaccurate detection" warning points to this. The fix is to
  delete that bundled SBOM in the build so the scan reflects the packages actually
  present.
- GHCR rejected the first push with `error from registry: denied` even though the
  login succeeded and every layer uploaded. Modern `docker build` (BuildKit with the
  containerd image store) attaches a provenance attestation by default, which makes
  the pushed artefact an OCI index, and GHCR denied that index on the first push to a
  new package. The layers uploading first proved write access, so it was the artefact
  shape, not a permission. The fix is to build a single plain image manifest
  (`docker buildx build --provenance=false --sbom=false --load`); provenance is still
  attached separately by the `attest-build-provenance` step, so nothing is lost.

### Phase 5: dynamic testing and the binding policy gate (2026-11-08)

**Situation.** Every gate so far reads code, dependencies or artefacts at rest. None
of them exercises the running service, and none of them actually blocks a release:
they report, and a human merges. The application still carried one planted weakness
that no static analyser can see, a privileged balance-adjustment route with no
authorisation check, and the pipeline had no control that would stop an unapproved or
insecure release from reaching production.

**Task.** Prove, on one pull request, that a dynamic test finds the broken access
control at runtime and that a policy-as-code gate fails the build on it, then passes
once the route is fixed. Bind the gate to three controls at once: the dynamic finding,
the Phase 4 signature and the Phase 1 approval.

**Action.** Added a `release-gate` workflow with two jobs. `dast` starts the
application on an ephemeral target, runs an OWASP ZAP baseline as the non-blocking
breadth check, then runs an access-control probe that calls the privileged route with
no credentials and records the result in `dast-findings.json`. `policy-gate` assembles
that finding together with the signature and approval facts into one document and
evaluates it with Conftest against `policy/release.rego`, which denies a release on a
high or critical dynamic finding, an unsigned artefact or an unapproved change. A deny
fails the job.

**Result.** Verified on the live repository from the run logs, not the green ticks
alone. On the planted commit the probe reached the admin route unauthenticated
(HTTP 200), the gate input carried `high_or_critical: 1` with signature and approval
both true, and Conftest returned `release blocked: 1 high or critical dynamic
finding(s)` (3 tests, 1 failure, exit 1), so the release was blocked on the single
failing control. After the remediation added a constant-time admin-token check that
rejects an unauthenticated call with HTTP 401, the probe was rejected, the finding
cleared to `high_or_critical: 0`, and Conftest passed all three tests, so the gate
allowed the release. The gate was untouched between the two runs; only the application
changed. Evidence in `evidence/phase5/`.

**Fixes and lessons.**
- The ZAP baseline alone is not enough for a headless API. The target has no
  browseable root, so the ZAP spider gets HTTP 404 on `/` and its crawl is shallow,
  and the passive header alerts do not apply because there is no browser surface. A
  spider will not reliably exercise a specific privileged route. The access-control
  probe, which calls the known route directly and asserts the authorisation
  behaviour, is the authoritative control; ZAP provides breadth and a report, the
  probe provides the binding depth, and the gate acts on the probe.
- The probe is a measurement, not the decision. It exits non-zero only when the target
  cannot be reached or returns an unexpected status, so a broken target can never be
  mistaken for a passing control. The binding release decision belongs to the policy
  gate, which keeps the test and the enforcement separate and auditable.
- The dynamic finding has to be provable on a pull request, where the signing job does
  not run. Running the application directly with uvicorn, rather than the signed GHCR
  image, lets the same dynamic test and gate run on every pull request, so the control
  is exercised on the change itself and not only after a merge to `main`.
- The probe targets a constant, in-pipeline URL and uses an HTTP client rather than a
  shelled-out request, so the static analysers already in the pipeline (CodeQL,
  Bandit) do not flag the test itself as a request-forgery or insecure-call finding.
  The gate that catches weaknesses must not introduce one.

### Phase 6: report, scorecard and governance mapping (2026-11-08)

**Situation.** With all nine gates built and proven, the build needed the artefacts a
security and controls function produces from a pipeline: a technical record, a mapping
to recognised frameworks, and a business case.

**Task.** Write the pipeline security report, the controls mapping and the business
report, each citing the evidence already captured, and confirm the repository's final
state is clean.

**Action.** Added `report/pipeline-security-report.md` (each gate in order, the
control it enforces, the weakness it was proven against with the failing and passing
runs cited, and a gate-by-gate scorecard), `report/controls-mapping.md` (NIST SSDF,
OWASP SAMM and DSOMM, and the change-management, segregation-of-duties and
audit-trail IT general controls, with the lab's limitations stated), and
`report/business-report.md` (framed against UK operational resilience and SOX-style
IT general controls, with a layers-of-defence diagram). Reconciled two index entries
that had drifted from the as-built: the IaC gate shipped as Checkov and Trivy rather
than tfsec, and the Phase 6 scorecard lives under `report/` rather than `evidence/`.

**Result.** The final state of each gate is recorded in the scorecard. All seven
planted application weaknesses are in the Fixed state in `app/README.md`, and no
planted weakness remains in the head of the default branch. The secret-scanning gate
runs over the full history, so the one synthetic secret used for the Phase 2 test was
purged from the branch history rather than deleted in a later commit. Build 3 is
complete.
