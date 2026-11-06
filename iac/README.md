# Infrastructure as code

The Terraform the pipeline scans and, optionally, deploys. It starts with one
planted over-permissive rule so the infrastructure-as-code gate can be proven, then
is tightened.

Scanned by Checkov and tfsec in the pipeline (Phase 4). The optional cloud deploy
in Phase 5 targets the Build 2 AWS lab under its existing budget guardrails. See
[docs/04-container-iac.md](../docs/04-container-iac.md).
