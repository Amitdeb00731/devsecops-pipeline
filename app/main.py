"""vulnerable-bank-api: a deliberately insecure test harness for the pipeline.

Phase 2 remediation: the hard-coded token is now read from the environment, and
the account lookup uses a parameterised query. Phase 5 remediation: the admin
balance-adjustment route below now enforces an authorisation check. The last
planted weakness, the unauthenticated privileged route, was carried to Phase 5 so
the dynamic test could prove the gap by calling it without credentials; this
commit closes it, so the probe records no finding and the release gate allows the
change. It is documented in app/README.md.
"""
import contextlib
import hmac
import os
import sqlite3

from fastapi import FastAPI, Header, HTTPException

# Remediated (secret scanning): the payments API token is read from the
# environment at runtime, so no secret is committed to source.
PAYMENTS_API_KEY = os.environ.get("PAYMENTS_API_KEY", "")

# The admin token for the privileged route is read from the environment. The route
# is fail-closed: if no token is configured, every call is rejected.
ADMIN_API_TOKEN = os.environ.get("ADMIN_API_TOKEN", "")

DB_PATH = "bank.db"


def init_db() -> None:
    """Create the demo schema and seed one account if the database is empty.

    This is test-harness setup, not application logic: it makes the service
    runnable for the Phase 5 dynamic test without a separate seed step.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, owner TEXT, balance REAL)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO accounts (id, owner, balance) VALUES (?, ?, ?)",
            ("1", "demo", 1000.0),
        )
        conn.commit()
    finally:
        conn.close()


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="vulnerable-bank-api", version="0.1.0", lifespan=lifespan)


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
def adjust_balance(
    account_id: str,
    amount: float,
    x_admin_token: str = Header(default=""),
) -> dict[str, object]:
    """Remediated (broken access control), proven by the Phase 5 dynamic test:
    this privileged balance adjustment now requires a valid admin token supplied in
    the X-Admin-Token header, compared in constant time against the ADMIN_API_TOKEN
    environment value. A missing or invalid token is rejected with HTTP 401, so the
    unauthenticated dynamic probe records no finding and the release gate allows the
    change. The route is fail-closed: with no token configured, every call is
    rejected."""
    if not ADMIN_API_TOKEN or not hmac.compare_digest(x_admin_token, ADMIN_API_TOKEN):
        raise HTTPException(status_code=401, detail="missing or invalid admin token")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (amount, account_id),
    )
    conn.commit()
    conn.close()
    return {"account_id": account_id, "adjusted_by": amount}
