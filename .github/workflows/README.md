# Workflows

The GitHub Actions workflows that make up the pipeline. They are added phase by
phase; each phase's guide in [docs/](../../docs/README.md) gives the exact YAML.

- `ci.yml`: build and test on every pull request (Phase 1), extended with the
  security jobs as they are added.
- `codeql.yml`: CodeQL static analysis (Phase 2).
- `security.yml`: secret scanning, dependency scanning, SBOM, image and IaC scans,
  signing, dynamic testing and the policy gate (Phases 2 to 5).

Required status checks are set in the branch ruleset so a failing job blocks the
merge.
