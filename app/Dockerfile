# PLANTED (Phase 4): this Dockerfile is deliberately weak so the image scan can be
# shown failing. The base image is an end-of-life Debian buster release pinned only
# by a floating tag, and the process runs as root. The hardened version is landed in
# the Phase 4 remediation commit: a digest-pinned slim base and a non-root user.
FROM python:3.10-slim-buster

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
