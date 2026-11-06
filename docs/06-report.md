# Phase 6: Report, scorecard and governance mapping

**Goal:** turn the build into the artefacts a security and controls function
produces: a pipeline security report, a controls mapping for a risk reader, and a
business stakeholder report. Same structure and house style as Builds 1 and 2.

## 6.1 Pipeline security report

`report/pipeline-security-report.md`, written as the record of the pipeline as a
control. Include:

- Each gate in order, what it is, and the control it enforces.
- For each gate, the planted weakness it was proven against, the failing run that
  blocked it, and the remediation that cleared it, with the evidence cited.
- A gate-by-gate scorecard: caught, accepted with a reason, or not applicable.
- The honest statement that passing the gates is assurance of process, not a
  guarantee of secure software.

## 6.2 Controls mapping

`report/controls-mapping.md`, for a technology-risk reader. Map each gate to the
recognised frameworks a bank's controls team uses:

- NIST Secure Software Development Framework (SP 800-218): the PO, PS, PW and RV
  practices each gate satisfies.
- OWASP SAMM and its DevOps profile DSOMM: the security practices and maturity
  level the pipeline demonstrates.
- IT general controls: change management (branch protection and review),
  segregation of duties (CODEOWNERS and the no-self-approval rule), and the audit
  trail (signed commits, retained SBOMs, signed artefacts, pipeline logs).

State the known limitations honestly: a solo lab proves the mechanism of
segregation of duties but not the separate people a real team would have; the
pipeline shows control design, not a certification.

## 6.3 Business report

`report/business-report.md`, a business stakeholder report in corporate language,
framed against UK operational resilience (PRA and FCA) and SOX-style IT general
controls over financially relevant systems: what an insecure or unapproved change
reaching production would mean for a service, which controls hold that risk, and a
layers-of-defence diagram for a business reader.

## 6.4 Housekeeping

- Confirm no real secret, personal data or private key is anywhere in the history,
  not only the current tree (the secret-scanning gate over full history is the
  check).
- Confirm the test application's planted weaknesses are all documented and all
  removed in the final state, so the repository's head is clean.
- Record the final state of each gate in `lab-notes.md`.

## Phase 6 deliverables

- `report/pipeline-security-report.md`, `report/controls-mapping.md`,
  `report/business-report.md`, and a `report/README.md` index.
- A gate-by-gate scorecard and the pipeline diagram.
- Commit: `Phase 6: pipeline security report, controls mapping and business report`.

## House style (carried from Builds 1 and 2)

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
