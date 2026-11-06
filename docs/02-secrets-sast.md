# Phase 2: Secrets and static application security testing

**Goal:** insecure code and leaked secrets caught before they merge, both on the
developer's machine and in continuous integration. Each gate is proven by a planted
weakness that it blocks, then fixed so the gate passes.

## 2.1 Build out the test application with planted weaknesses

The `app/` service is a small FastAPI account-lookup API. It carries a short,
documented set of planted weaknesses, each listed in `app/README.md` with the
control it exercises. For this phase:

- A hard-coded secret in the source (an API token assigned to a constant), for the
  secret-scanning gate.
- A `.env` file with a fake credential committed by mistake, for the same gate.
- A SQL query built by string concatenation and a route with no authorisation
  check, for static analysis.

`app/README.md` states plainly that these are deliberate and lists the commit that
removes each one, so the repository reads as a controlled test harness.

## 2.2 Pre-commit hooks (shift-left to the developer)

Add `.pre-commit-config.yaml` so weaknesses are caught before a commit is even
created:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "app/bandit.yaml"]
```

Install with `pip install pre-commit && pre-commit install`. A commit that contains
the hard-coded secret is now rejected locally. This is defence in depth: the same
checks run in CI, so a developer who skips the hook is still caught.

## 2.3 Secret scanning in CI

Add a job to `.github/workflows/ci.yml` (or a dedicated `security.yml`) that scans
the full history, not just the diff, so a secret added in an earlier commit is
found:

```yaml
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Also enable GitHub's native **secret scanning** and **push protection** in
Settings, Code security: push protection blocks a known secret pattern at push
time, before it ever reaches the server.

## 2.4 Static analysis: Semgrep and CodeQL

Two static analysers, run on every pull request, with results sent to the
repository's security tab as SARIF so findings are tracked, not just printed.

Semgrep, with the registry rulesets for Python and for secrets:

```yaml
  sast-semgrep:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/python
            p/security-audit
            p/secrets
```

CodeQL, GitHub's own analyser, added through the **CodeQL** starter workflow
(`.github/workflows/codeql.yml`) with the `python` language pack and the
`security-extended` query suite. It finds the SQL injection as a tainted data-flow
problem. The missing authorisation check is a design flaw rather than a data-flow
bug, so it is flagged by Semgrep's audit rules where one matches and is proven end
to end by the Phase 5 dynamic test, which calls the unprotected route and shows it
succeed without credentials. Recording this honestly matters: a static analyser
finds the injection reliably, but authorisation gaps are best confirmed by exercising
the running application.

## 2.5 Prove the gate, then fix

1. Open a pull request that still contains the planted secret and the injection
   flaw. Capture the failing run: Gitleaks blocks the secret in continuous
   integration, and CodeQL flags the SQL injection as a tainted data-flow alert.
   The missing-authorisation route is not flagged here, because no static analyser
   treats it as a bug; that gap is carried to the Phase 5 dynamic test.
2. Remediate: move the secret to an environment variable read at runtime, and
   parameterise the query so the driver binds the value. The missing-authorisation
   route is deliberately left in place for Phase 5.
3. A secret that reached the server is treated as compromised, so removing it in a
   later commit is not enough: it must be purged from the branch history and the
   secret rotated. Here the branch is rewritten to a single clean commit with no
   secret in any commit, and the synthetic value is discarded. Gitleaks then
   re-scans the whole history and passes.
4. Re-run. The pull request now passes, and the security tab shows the findings
   resolved. Both the failing and the passing runs are evidence.

## Phase 2 deliverables

- `.pre-commit-config.yaml` and `app/bandit.yaml`.
- The secret-scan, Semgrep and CodeQL jobs, set as required status checks.
- `evidence/phase2/`: the failing run that blocks the bad commit, the passing run
  after remediation, and the findings in the security tab.
- Commit: `Phase 2: secrets and static analysis`.

## Checks before moving on

- A commit containing a secret is blocked locally and in CI.
- The SQL injection and the missing authorisation check are found by static
  analysis and fixed.
- Findings appear in the security tab and are marked resolved after the fix.
- The gate mapping is recorded: SSDF PW.4, PW.7 and PW.8.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
