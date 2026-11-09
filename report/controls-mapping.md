# Controls mapping

This document maps each pipeline gate to the frameworks a technology-risk or controls
function uses: the NIST Secure Software Development Framework, OWASP SAMM and its
DevOps profile DSOMM, and the IT general controls a bank's auditors test. It is a
reader's reference for how the build in this repository satisfies recognised control
objectives. The evidence for each gate is in the
[pipeline security report](pipeline-security-report.md) and under
[`evidence/`](../evidence/).

## NIST Secure Software Development Framework (SP 800-218)

The SSDF groups practices under Prepare the Organization (PO), Protect the Software
(PS), Produce Well-Secured Software (PW) and Respond to Vulnerabilities (RV).

| SSDF practice | How this pipeline satisfies it |
| --- | --- |
| PO.1 Define security requirements | The release criteria are defined as code in `policy/release.rego`: a release must be approved, built from a signed artefact and free of high or critical dynamic findings. |
| PO.3 Implement supporting toolchains | The controls run in an automated GitHub Actions pipeline on every change, not as manual steps. |
| PS.1 Protect code from unauthorised access or tampering | Branch protection requires a reviewed pull request and blocks force pushes; commits must carry a verified signature. |
| PS.2 Provide a mechanism to verify software release integrity | The image is signed with cosign and the signature is verified in the pipeline. |
| PS.3 Archive and protect each release | SBOMs are retained, the artefact is signed, and SLSA build provenance is recorded in a transparency log and on the repository's Attestations page. |
| PW.4 Reuse existing, well-secured software | Dependency scanning and the SBOM track third-party components; known-vulnerable versions are blocked. |
| PW.6 Configure the build process for security | The container image is hardened and scanned, and the infrastructure-as-code is scanned before it could be applied. |
| PW.7 Review and analyse human-readable code | Static analysis (CodeQL, Semgrep) and secret scanning run on every pull request. |
| PW.8 Test executable code to identify vulnerabilities | The dynamic access-control test exercises the running service and finds the defect static analysis cannot. |
| RV.1 Identify and confirm vulnerabilities on an ongoing basis | The scanners run on every pull request and push, and Dependabot raises upgrades continuously. |
| RV.2 Assess, prioritise and remediate vulnerabilities | Each planted finding was triaged and cleared by a named remediation commit. |
| RV.3 Analyse vulnerabilities to identify root causes | The fail-then-fix evidence records the cause of each finding and the change that removed it. |

## OWASP SAMM and DSOMM

Against the OWASP Software Assurance Maturity Model, the pipeline demonstrates
practices across four of the five business functions.

| SAMM function | Practice demonstrated |
| --- | --- |
| Governance | Policy and Compliance: release criteria enforced as code by the policy gate. |
| Design | Security Requirements: the release criteria; Threat Assessment: the documented, planted weakness classes the gates target. |
| Implementation | Secure Build: hardened image, reproducible pipeline, signed artefact; Secure Deployment: signature verification and provenance; Defect Management: tracked findings and remediations. |
| Verification | Security Testing: static analysis and dynamic testing on every change; Requirements-driven Testing: the policy gate checks the defined release criteria. |

Against the DevSecOps Maturity Model (DSOMM), the pipeline implements the core
dimensions a maturing programme is measured on: static analysis depth (two SAST
tools plus secret scanning), dynamic analysis (a runtime access-control test),
software composition analysis with a retained SBOM, hardened build and signed
artefacts with provenance, and consolidation of findings into the security tab with a
blocking policy gate. As a single-service lab it demonstrates the control design of
these dimensions rather than the breadth or operational history a production
programme would accumulate.

## IT general controls

The pipeline is built to satisfy the three IT general control objectives a bank's
auditors test over a change and delivery process.

- **Change management.** No change reaches the default branch without a pull request,
  a passing required status check and a recorded approving review. The control is
  enforced by the `protect-main` ruleset and evidenced in
  [`evidence/phase1/`](../evidence/phase1/).
- **Segregation of duties.** Code Owners are required on a pull request and an author
  cannot approve their own change, so the person who writes a change is not the person
  who approves it. See the limitation below.
- **Audit trail.** Every merged change is traceable: commits carry verified
  signatures, each build retains an SBOM, the released artefact is signed and its
  provenance is recorded in a public transparency log, and the pipeline runs are
  retained logs of what ran and what it decided.

## Known limitations

These are stated plainly so the repository is not read as more than it is.

- **Segregation of duties in a single-person lab.** The ruleset requires a separate
  approver and forbids self-approval, which proves the mechanism. In this lab there
  is one person, so the repository owner is on a documented bypass list to allow
  day-to-day merges while the pull request, review and status-check flow still
  applies. A real team supplies the separate approver the control assumes; this is
  recorded in [`evidence/phase1/`](../evidence/phase1/) rather than presented as a
  full implementation.
- **Release gate inputs.** The policy evaluates three criteria, but in this build only
  the dynamic finding is read from a live result. The signature is enforced by the
  signing job, which signs the image with cosign and verifies the signature against
  the workflow identity, and the approval by branch protection, which requires a
  reviewed pull request. Both are supplied to the gate as asserted preconditions rather
  than re-verified inside the gate. The production hardening is to have the gate read
  the cosign verification result for the exact image digest and the pull-request review
  state from the platform, and to fail closed when either is unavailable.
- **Artefact integrity.** The image is scanned and, on the merge to the default branch,
  built, signed and provenance-attached. In this build the scan and the signing are
  separate builds of the same source commit; binding both to a single immutable digest,
  so the signed artefact is provably the scanned one, is the production hardening.
- **Required status checks.** The `protect-main` ruleset requires the build-and-test
  check and the secret, static-analysis, CodeQL and dependency scans to pass before a
  pull request can merge. The container and infrastructure-as-code scan and the release
  policy gate run on every pull request and every push to the default branch but are
  not in the required-check set, so they report rather than block a merge; adding them
  to the required checks is the further hardening.
- **Control design, not certification.** The build demonstrates how the controls are
  designed and that they operate on this repository. It is not an audit, an
  accreditation or a penetration test, and it does not certify any production system.
- **Scope.** A single service on GitHub-hosted runners. The gates reduce defined
  classes of risk; they do not prove the absence of all vulnerabilities, and a
  production programme would add coverage, operational history and independent review.
