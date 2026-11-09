# Architecture diagrams

A high-level visual overview of the DevSecOps pipeline: the delivery flow, the gate
logic, the change-control model, and the mapping from each gate to the control it
enforces. All diagrams render natively on GitHub.

## 1. The pipeline, end to end

A change moves left to right through the gates. A failed gate sends it back to the
author; only a scanned, signed, approved build reaches production.

```mermaid
flowchart LR
  DEV["Developer<br/>pre-commit: Gitleaks, Bandit"]
  PR["Pull request<br/>branch protection, code-owner review"]
  SAST["Secrets and SAST<br/>Gitleaks, Semgrep, CodeQL"]
  SCA["Dependencies and SBOM<br/>pip-audit, Trivy, Syft"]
  ART["Container and IaC, sign<br/>Trivy, Checkov, cosign"]
  GATE{"Policy gate<br/>all checks pass?"}
  PROD["Production<br/>signed, scanned build"]
  BACK["Back to the author<br/>fix and push"]

  DEV --> PR --> SAST --> SCA --> ART --> GATE
  GATE -->|yes| PROD
  GATE -->|no| BACK
  BACK --> PR
```

## 2. The gate logic

The policy gate evaluates three release criteria and any single failure blocks the
release. In this build the high or critical finding is read from the runtime test;
the signature and approval states are enforced earlier by the signing job and by
branch protection and are asserted to the gate as preconditions, as set out in the
[controls mapping](../report/controls-mapping.md).

```mermaid
flowchart TB
  IN["Gate input: scan results, signature state, approval state"]
  C1{"High or critical<br/>findings?"}
  C2{"Image signed?"}
  C3{"Approved by a<br/>code owner?"}
  BLOCK["Release blocked"]
  ALLOW["Release allowed"]

  IN --> C1
  C1 -->|yes| BLOCK
  C1 -->|no| C2
  C2 -->|no| BLOCK
  C2 -->|yes| C3
  C3 -->|no| BLOCK
  C3 -->|yes| ALLOW
```

## 3. Change control and segregation of duties

No change reaches the main branch without review, a passing build and a recorded
approver who is not the author.

```mermaid
flowchart LR
  A["Author<br/>signed commit on a branch"]
  PR["Pull request"]
  CHK["Required checks<br/>build, secret, SAST, deps"]
  REV["Code-owner review<br/>not the author"]
  MAIN["main branch<br/>linear, protected"]

  A --> PR --> CHK --> REV --> MAIN
  REV -. "changes requested" .-> A
```

## 4. Gate to control

Each gate maps to a recognised secure-development practice and an IT general
control.

```mermaid
flowchart LR
  subgraph GATES["Pipeline gates"]
    G1["Change control"]
    G2["Secrets and SAST"]
    G3["Dependencies and SBOM"]
    G4["Container and IaC, signing"]
    G5["Dynamic and policy gate"]
  end
  subgraph CTRL["Controls and frameworks"]
    SSDF["NIST SSDF<br/>PO, PS, PW, RV"]
    SAMM["OWASP SAMM and DSOMM"]
    ITGC["IT general controls<br/>change, SoD, audit trail"]
  end
  G1 --> ITGC
  G2 --> SSDF
  G3 --> SAMM
  G4 --> SSDF
  G5 --> SAMM
  G1 --> SSDF
```
