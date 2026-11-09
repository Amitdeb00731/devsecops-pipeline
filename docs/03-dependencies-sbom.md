# Phase 3: Dependencies, SBOM and supply-chain assurance

**Goal:** know and control what the application depends on. Scan dependencies for
known vulnerabilities, produce and retain a software bill of materials (SBOM), and
flag and upgrade a known-vulnerable dependency. This is the supply-chain control
that a leaked or outdated dependency would otherwise defeat.

## 3.1 Plant the vulnerable dependency

First refresh the existing dependencies to current patched versions, so the scan
starts from a clean baseline and the only finding is the one we plant. Then pin one
dependency in `app/requirements.txt` to a version with a known CVE. This lab pins
`pyjwt==2.3.0`, which carries an algorithm-confusion flaw (CVE-2022-29217) among
others and is a natural dependency for a service that would issue JSON Web Tokens.
Record it in `app/README.md` as a deliberate weakness with the control it exercises.
The scanners below must flag it; the upgrade commit must clear it.

## 3.2 Dependency scanning in CI

Two scanners, so a finding does not depend on a single source.

pip-audit, against the Python advisory database:

```yaml
  dep-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pip-audit
      - run: pip-audit -r app/requirements.txt
```

Trivy, in filesystem mode, which also reads the lockfile and reports severity:

```yaml
  dep-trivy:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@v0.36.0
        with:
          scan-type: fs
          scan-ref: app
          format: sarif
          output: trivy-deps.sarif
          severity: HIGH,CRITICAL
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-deps.sarif
```

The planted CVE appears in both. Set a threshold so a HIGH or CRITICAL finding
fails the job once the lab's baseline is clean, which turns the scan into a gate
rather than a report.

## 3.3 Dependabot

Add `.github/dependabot.yml` so new vulnerable dependencies are raised as pull
requests automatically, which is the ongoing control after the one-off scan:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /app
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

The second entry pins and updates the Actions themselves, so the pipeline's own
supply chain is covered, not only the application's.

## 3.4 Software bill of materials

Generate an SBOM with Syft in CycloneDX format and retain it as a build artefact,
so every release has a recorded inventory of what it contains:

```yaml
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anchore/sbom-action@v0
        with:
          path: app
          format: cyclonedx-json
          output-file: sbom/app-sbom.cdx.json
      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom/app-sbom.cdx.json
```

Scan the SBOM itself with Grype (`anchore/scan-action`) so the inventory is checked
against vulnerability data, not just produced. A licence check (for example
`pip-licenses`) records the licences in use, which is the control a bank applies to
avoid unacceptable open-source licences.

## 3.5 Prove the gate, then fix

1. Capture the scan with the planted CVE present: pip-audit and Trivy both flag it,
   the SBOM lists the vulnerable version.
2. Upgrade the dependency to a patched version. Re-run.
3. The scans are clean, the SBOM lists the patched version, and Dependabot's policy
   is in place. The before and after reports are evidence.

## Phase 3 deliverables

- The dep-audit, dep-trivy and sbom jobs, with HIGH and CRITICAL set to fail.
- `.github/dependabot.yml`.
- `sbom/app-sbom.cdx.json`, retained.
- `evidence/phase3/`: the vulnerability report before and after the upgrade, the
  SBOM, and the Dependabot configuration.
- Commit: `Phase 3: dependencies, SBOM and supply chain`.

## Checks before moving on

- The planted CVE is flagged by both scanners and cleared by the upgrade.
- An SBOM is produced in CycloneDX format and retained with the build.
- Dependabot raises updates for the application and the Actions.
- The gate mapping is recorded: SSDF PW.4 and RV.1, OWASP SAMM Supply Chain.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
