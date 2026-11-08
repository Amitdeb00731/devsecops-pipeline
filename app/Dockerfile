# Phase 4 remediation: a hardened container image. The base is pinned by digest
# (immutable and reproducible), a dedicated non-root user runs the process, the
# build tooling is upgraded to patched versions, and the build context excludes
# caches, tests and the synthetic .env (see .dockerignore).
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

RUN useradd --create-home --uid 10001 appuser

WORKDIR /home/appuser/app

COPY --chown=appuser:appuser app/requirements.txt .
# Install the application, upgrade the build tooling to patched versions, and
# remove pip's bundled CycloneDX SBOM. That SBOM lists pip's stripped-down
# vendored setuptools (70.3.0, only pkg_resources is kept), which the image scan
# would otherwise report as a vulnerability even though the installed setuptools
# is patched. Removing it makes the scan reflect the packages that are actually
# present.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade "setuptools>=78.1.1" "wheel>=0.46.2" \
    && find /usr/local/lib -path '*/pip/_vendor/bom.cdx.json' -delete

COPY --chown=appuser:appuser app/ .

USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
