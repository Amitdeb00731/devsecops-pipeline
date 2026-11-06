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
