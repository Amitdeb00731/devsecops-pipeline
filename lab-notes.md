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
