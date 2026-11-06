"""vulnerable-bank-api: a deliberately insecure test harness for the pipeline.

Phase 1 ships a clean skeleton with a health check only, so the pipeline has
something to build and test. The planted weaknesses are added from Phase 2
onwards, each documented in app/README.md with the control it exercises.
"""
from fastapi import FastAPI

app = FastAPI(title="vulnerable-bank-api", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the pipeline and the dynamic test."""
    return {"status": "ok"}
