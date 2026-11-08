# Phase 4 remediation: a hardened container image. The base is pinned by digest
# (immutable and reproducible), a dedicated non-root user runs the process, the
# build tooling is upgraded to patched versions, and the build context excludes
# caches, tests and the synthetic .env (see .dockerignore).
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

RUN useradd --create-home --uid 10001 appuser

WORKDIR /home/appuser/app

COPY --chown=appuser:appuser app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/ .

USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
