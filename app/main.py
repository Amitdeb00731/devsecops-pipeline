"""vulnerable-bank-api: a deliberately insecure test harness for the pipeline.

Phase 2 remediation: the hard-coded token is now read from the environment, and
the account lookup uses a parameterised query. One planted weakness is left in
place on purpose. The admin route below still has no authorisation check, because
no static analyser flags that as a bug; it is the Phase 5 dynamic test that proves
the gap by calling the route without credentials. It is documented in
app/README.md and carried to Phase 5 rather than fixed here.
"""
import os
import sqlite3

from fastapi import FastAPI

app = FastAPI(title="vulnerable-bank-api", version="0.1.0")

# Remediated (secret scanning): the payments API token is read from the
# environment at runtime, so no secret is committed to source.
PAYMENTS_API_KEY = os.environ.get("PAYMENTS_API_KEY", "")

DB_PATH = "bank.db"


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the pipeline and the dynamic test."""
    return {"status": "ok"}


@app.get("/accounts/{account_id}")
def get_account(account_id: str) -> dict[str, object]:
    """Remediated (SQL injection): the query is parameterised, so the driver
    binds the value and it cannot alter the query."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, owner, balance FROM accounts WHERE id = ?",
        (account_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return {"account": row}


@app.post("/admin/accounts/{account_id}/adjust")
def adjust_balance(account_id: str, amount: float) -> dict[str, object]:
    """Planted (missing authorisation), carried to Phase 5: this privileged
    balance adjustment still has no authentication or authorisation check. No
    static analyser flags it, so the Phase 5 dynamic test is what proves the gap
    by calling it without credentials."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (amount, account_id),
    )
    conn.commit()
    conn.close()
    return {"account_id": account_id, "adjusted_by": amount}
