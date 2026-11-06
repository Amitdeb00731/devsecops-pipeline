# Phase 1: Pipeline and change-control foundation

**Goal:** a repository where the delivery process itself enforces change
management, before any scanner is added. No change reaches the main branch without
review, passing checks and a recorded approver. This is the change-management and
segregation-of-duties control a bank's auditors test, implemented as code.

## 1.1 Create the repository and the test application skeleton

1. Create a public repository `devsecops-pipeline` on GitHub, owned by your
   account.
2. Add the FastAPI test application under `app/` (built out in Phase 2). For now a
   minimal service and a health check are enough to give the pipeline something to
   build:

   ```
   app/
     main.py          a FastAPI app with a /health endpoint
     requirements.txt pinned dependencies
     tests/           a trivial test so the build has something to run
   ```

3. Commit on a branch, not on `main`, so the first pull request exercises the
   controls you set up below.

## 1.2 Protect the main branch

Branch protection is the control. In **Settings, Branches, Add branch ruleset**
for `main`, enable:

- **Require a pull request before merging**, with at least one approving review.
- **Dismiss stale approvals when new commits are pushed**, so an approval always
  matches the code that merges.
- **Require review from Code Owners** (set up in 1.3).
- **Require status checks to pass** (the checks are added from Phase 2; the list
  grows as gates are added).
- **Require branches to be up to date before merging.**
- **Require linear history**, so the audit trail is a straight line of reviewed
  commits.
- **Require signed commits** (set up in 1.4).
- **Do not allow bypassing the above settings**, including for administrators, so
  the control holds for everyone.
- **Restrict deletions** and **block force pushes.**

The segregation-of-duties point is that the author of a change cannot approve their
own pull request, and the control cannot be bypassed by the person who owns the
repository.

## 1.3 CODEOWNERS for mandatory reviewers

Add `.github/CODEOWNERS`:

```
# Every change needs a review from the code owner.
*                 @Amitdeb00731
/.github/         @Amitdeb00731
/policy/          @Amitdeb00731
/iac/             @Amitdeb00731
```

In a real team these would be different people or teams per path, which is the
segregation-of-duties control: the person who changes a security policy is not the
person who approves it. In a solo lab, the control is documented and the mechanism
is proven; the write-up states the difference honestly.

## 1.4 Signed commits

1. Create a signing key (SSH signing is the simplest and is free):

   ```bash
   ssh-keygen -t ed25519 -C "signing key for devsecops-pipeline"
   git config --global gpg.format ssh
   git config --global user.signingkey ~/.ssh/id_ed25519.pub
   git config --global commit.gpgsign true
   ```

2. Add the public key to GitHub as a **Signing key** (Settings, SSH and GPG keys),
   separate from any authentication key.
3. From now on every commit is signed, and the branch rule rejects an unsigned
   commit. Verified commits show a green **Verified** badge, which is the integrity
   control on the change itself.

Never commit the private key. The `.gitignore` already excludes `*.key` and
`*.pem`; the signing key lives only in `~/.ssh`.

## 1.5 The baseline workflow

Add `.github/workflows/ci.yml`, the workflow every later phase extends. At this
stage it lints and tests on every pull request, so "passing checks" means
something before the security gates arrive:

```yaml
name: ci
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r app/requirements.txt
      - run: pip install ruff pytest
      - run: ruff check app
      - run: pytest app/tests -q
```

Set the job as a **required status check** in the branch ruleset once it has run
once, so a failing build blocks the merge.

## Phase 1 deliverables

- The branch protection ruleset on `main`.
- `.github/CODEOWNERS` and the signed-commit configuration.
- `.github/workflows/ci.yml` running on every pull request.
- `evidence/phase1/`: the ruleset, a screenshot of a blocked direct push to `main`,
  a pull request that cannot merge without an approver, and a verified signed
  commit.
- Commit: `Phase 1: pipeline and change-control foundation`.

## Checks before moving on

- A direct push to `main` is rejected.
- A pull request cannot be merged without a passing build and an approving review.
- Commits show as **Verified**.
- The mapping is recorded: branch protection and review to the change-management
  ITGC, CODEOWNERS to segregation of duties, signed commits to change integrity.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
