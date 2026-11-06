# Build 3 execution guides: DevSecOps pipeline

Step-by-step guides for each phase of the `devsecops-pipeline` build. The plan and
the rationale are in the Build 3 plan document; these are the how-to. The build
turns a software delivery pipeline into the place a bank's change and security
controls are enforced automatically.

| Phase | Guide | Output |
| --- | --- | --- |
| 1 | [Pipeline and change-control foundation](01-pipeline-foundation.md) | Branch protection, CODEOWNERS, signed commits, baseline workflow |
| 2 | [Secrets and static analysis](02-secrets-sast.md) | Pre-commit hooks, Gitleaks, Semgrep, CodeQL, SARIF to the security tab |
| 3 | [Dependencies, SBOM and supply chain](03-dependencies-sbom.md) | pip-audit, Dependabot, Trivy, a CycloneDX SBOM with Syft |
| 4 | [Container and infrastructure-as-code](04-container-iac.md) | Hardened image, Trivy, Checkov, tfsec, cosign signing and verification |
| 5 | [Dynamic testing and the policy gate](05-dynamic-policy-gate.md) | OWASP ZAP, Open Policy Agent gate that blocks the release |
| 6 | [Report, scorecard and governance](06-report.md) | Pipeline security report, controls mapping, business summary |

For a high-level visual overview, see
[architecture-diagrams.md](architecture-diagrams.md): the pipeline flow, the gate
logic, and the mapping from gate to control.

The build runs on a single public GitHub repository with GitHub Actions, free for
public repositories, and open-source scanners on GitHub-hosted runners. The test
application in `app/` is deliberately insecure, documented as such, so each gate
has a genuine finding to catch and then fix. Follow the phases in order; each ends
with evidence committed and a short list of checks before moving on.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers, commands and tool names as they are.
