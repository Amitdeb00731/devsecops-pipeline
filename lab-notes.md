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

Entries are added here as each phase completes.

