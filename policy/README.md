# Policy as code

Open Policy Agent (Rego) policies evaluated with Conftest. These are the explicit
release decision: the pipeline collects the results of the scans, the signature
check and the approval state into a small JSON document, and the policy here
decides whether the release may proceed.

- `release.rego`: denies a release on a high or critical finding, an unsigned
  image, or a missing code-owner approval (Phase 5).

See [docs/05-dynamic-policy-gate.md](../docs/05-dynamic-policy-gate.md).
