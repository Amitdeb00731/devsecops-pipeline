# vulnerable-bank-api (deliberately insecure test harness)

> **This application is intentionally insecure. It exists only to give the
> pipeline's security gates something real to catch.** Do not deploy it anywhere
> public, and do not reuse its code. Every weakness is planted on purpose, listed
> below with the control it exercises, and removed by a named remediation commit.

A small FastAPI service that mimics a trivial account-lookup microservice. It is
the subject the `devsecops-pipeline` gates run against.

## Planted weaknesses

Each is added deliberately so a gate can be proven, then fixed. The table is kept
current as the phases proceed.

| Weakness | Gate it exercises | Phase | Status |
| --- | --- | --- | --- |
| Hard-coded secret in source | Secret scanning (Gitleaks) | 2 | Planned |
| `.env` with a fake credential committed | Secret scanning, push protection | 2 | Planned |
| SQL built by string concatenation | Static analysis (Semgrep, CodeQL) | 2 | Planned |
| Route with no authorisation check | Static analysis, dynamic testing | 2, 5 | Planned |
| Outdated dependency with a known CVE | Dependency scan, SBOM | 3 | Planned |
| Dockerfile running as root, unpinned base | Image scan (Trivy) | 4 | Planned |
| Over-permissive Terraform rule | IaC scan (Checkov, tfsec) | 4 | Planned |

The synthetic secret used for the secret-scanning test is never a real credential
and is rotated out as part of the Phase 2 remediation.

## Layout (built out from Phase 1)

```
app/
  main.py          the FastAPI service
  requirements.txt pinned dependencies
  Dockerfile       hardened in Phase 4
  bandit.yaml      Bandit configuration
  tests/           tests the pipeline runs
```
