# Phase 4: Container and infrastructure-as-code security, and provenance

**Goal:** what reaches production is a scanned, signed artefact. Harden and scan the
container image, scan the infrastructure-as-code, sign the image and verify the
signature in the pipeline, and attach build provenance. An unsigned or unscanned
image must be rejected.

## 4.1 A hardened Dockerfile, planted weak first

Start with a deliberately weak `app/Dockerfile`: a full base image and a process
running as root. Record it in `app/README.md` as a planted weakness. The hardened
version, which the scan drives you to, is:

```dockerfile
FROM python:3.12-slim-bookworm@sha256:<pinned-digest>
RUN useradd --create-home --uid 10001 appuser
WORKDIR /home/appuser/app
COPY --chown=appuser:appuser app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade "setuptools>=78.1.1" "wheel>=0.46.2"
COPY --chown=appuser:appuser app/ .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The base image is pinned by digest, a non-root user runs the process, and the build
tooling is upgraded to patched versions. This is a single-stage image, so pip and the
upgraded build tooling remain present; a multi-stage build that copies only the
runtime into a clean final stage is the further hardening.

## 4.2 Scan the image

Build the image in CI and scan it with Trivy for operating-system and library
vulnerabilities and for misconfiguration:

```yaml
  image-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t app:${{ github.sha }} -f app/Dockerfile .
      - uses: aquasecurity/trivy-action@v0.36.0
        with:
          scan-type: image
          image-ref: app:${{ github.sha }}
          format: sarif
          output: trivy-image.sarif
          severity: HIGH,CRITICAL
          exit-code: "1"
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-image.sarif
```

`exit-code: 1` makes a HIGH or CRITICAL finding fail the job, so the scan is a
gate.

## 4.3 Scan the infrastructure-as-code

The `iac/` directory holds the Terraform the pipeline deploys. Plant one
over-permissive rule first (a security group open to `0.0.0.0/0`, or a public
bucket), documented as deliberate, then scan with Checkov as the blocking gate (with
Trivy configuration scanning as a second, reporting source):

```yaml
  iac-scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: bridgecrewio/checkov-action@v12
        with:
          directory: iac
          output_format: sarif
          output_file_path: checkov.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: checkov.sarif
```

The planted rule is flagged, then tightened, and the scan passes. This is the same
control as the Build 2 posture work, applied before deploy rather than after.

## 4.4 Sign the image and verify

Sign the image keylessly with cosign, using the workflow's OIDC identity, so no
private key is stored:

```yaml
  sign:
    needs: image-scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: sigstore/cosign-installer@v3
      - run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} -f app/Dockerfile .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
          cosign sign --yes ghcr.io/${{ github.repository }}:${{ github.sha }}
```

Then verify in a later step, pinning the certificate identity to this repository's
signing workflow so verification accepts only a signature from that workflow, not any
signer. Proving the control by attempting to verify an unsigned image must fail:

```bash
cosign verify ghcr.io/${{ github.repository }}:${{ github.sha }} \
  --certificate-identity-regexp "^https://github.com/[^/]+/[^/]+/.github/workflows/container-iac.yml@" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Attach build provenance with the GitHub artefact attestation action
(`actions/attest-build-provenance`), which records how and where the image was
built, the SLSA-style provenance a consumer can check.

## Phase 4 deliverables

- A hardened, digest-pinned `app/Dockerfile`.
- The image-scan, iac-scan and sign jobs, with HIGH and CRITICAL set to fail.
- `evidence/phase4/`: the image scan, the IaC findings and fixes, a verified
  signature, a rejected unsigned image, and the provenance attestation.
- Commit: `Phase 4: container and infrastructure-as-code security, signing`.

## Checks before moving on

- A HIGH or CRITICAL image or IaC finding fails the pipeline.
- The image runs as a non-root user from a digest-pinned base.
- A signed image verifies and an unsigned image is rejected.
- Build provenance is attached and can be verified.
- The gate mapping is recorded: SSDF PS.2 and PS.3, OWASP SAMM Operations.

## House style

- No em or en dashes; plain professional prose.
- Every result claim carries its evidence.
- No placeholder text committed.
- British spelling in prose; keep identifiers and commands as they are.
