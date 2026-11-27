"""
azure_sql.py - Optional Azure SQL Database helper for Azure Data Explorer.

Everything Azure-related lives in this file so app.py stays easy to read.

Credentials are NEVER written in code. They are read, in this order, from:
  1. Streamlit secrets  -> .streamlit/secrets.toml, section [azure_sql]
  2. Environment variables -> AZURE_SQL_SERVER, AZURE_SQL_DATABASE,
                              AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD
"""

import os
import re

import pandas as pd

# Settings we need, mapped to the environment variable that can provide each one.
SETTINGS = {
    "server": "AZURE_SQL_SERVER",
    "database": "AZURE_SQL_DATABASE",
    "username": "AZURE_SQL_USERNAME",
    "password": "AZURE_SQL_PASSWORD",
}

# Values copied from the example file mean "not configured yet".
PLACEHOLDER_HINTS = ("your-", "<", ">")

MAX_ROWS = 5000  # Safety limit so a large table can't freeze the app.

SAMPLE_QUERY = """SELECT TOP (500)
    order_id, order_date, region, city, category, product,
    channel, quantity, unit_price, discount_pct, total_amount
FROM dbo.Sales
WHERE order_date >= '2026-01-01'
ORDER BY order_date;"""

AGGREGATE_QUERY = """SELECT category,
       COUNT(*)          AS orders,
       SUM(quantity)     AS units_sold,
       SUM(total_amount) AS revenue
FROM dbo.Sales
GROUP BY category
ORDER BY revenue DESC;"""

# Words that change data or the database. The app only reads data.
BLOCKED_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "merge", "exec", "execute", "grant", "revoke", "deny", "backup", "restore",
    "shutdown", "openrowset", "opendatasource", "into",
)


def _read_streamlit_secrets():
    """Return the [azure_sql] section from Streamlit secrets, or {} if absent."""
    try:
        import streamlit as st

        if "azure_sql" in st.secrets:
            return dict(st.secrets["azure_sql"])
    except Exception:
        # No secrets.toml file (or it can't be parsed) -> just use env vars.
        pass
    return {}


def _looks_like_placeholder(value):
    lowered = value.lower()
    return any(hint in lowered for hint in PLACEHOLDER_HINTS)


def load_config():
    """
    Collect connection settings without ever exposing the password.

    Returns (config, source, problems):
      config   - dict with server/database/username/password (may be partial)
      source   - "Streamlit secrets", "environment variables", or None
      problems - list of human-friendly messages; empty means ready to connect
    """
    secrets = _read_streamlit_secrets()
    config, used_secrets, used_env = {}, False, False

    for key, env_name in SETTINGS.items():
        value = str(secrets.get(key, "")).strip()
        if value:
            used_secrets = True
        else:
            value = os.environ.get(env_name, "").strip()
            if value:
                used_env = True
        config[key] = value

    if used_secrets and used_env:
        source = "Streamlit secrets + environment variables"
    elif used_secrets:
        source = "Streamlit secrets"
    elif used_env:
        source = "environment variables"
    else:
        source = None

    problems = []
    for key, env_name in SETTINGS.items():
        if not config[key]:
            problems.append(
                f"Missing `{key}` (set it in `.streamlit/secrets.toml` under "
                f"`[azure_sql]`, or as the environment variable `{env_name}`)."
            )
        elif _looks_like_placeholder(config[key]):
            problems.append(
                f"`{key}` still contains a placeholder value. Replace it with "
                "your own Azure SQL details."
            )

    server = config["server"]
    if server and not _looks_like_placeholder(server):
        if server.startswith(("http://", "https://")) or "/" in server:
            problems.append(
                "`server` should be a host name only, for example "
                "`myserver.database.windows.net` (no https:// and no slashes)."
            )
        elif not server.endswith(".database.windows.net"):
            problems.append(
                "`server` usually ends with `.database.windows.net`. Copy the "
                "'Server name' from your database's Overview page in the Azure portal."
            )

    return config, source, problems


def validate_query(query):
    """
    Basic guard: allow a single read-only SELECT (or WITH ... SELECT) statement.
    Returns (clean_query, error_message). error_message is None when valid.

    This is a classroom-level check, not a security boundary. The real
    protection is connecting with a database user that only has read access.
    """
    clean = (query or "").strip()
    while clean.endswith(";"):
        clean = clean[:-1].rstrip()

    if not clean:
        return clean, "Please enter a SQL query."
    if ";" in clean:
        return clean, "Please run one statement at a time (remove the extra `;`)."
    if not re.match(r"^(select|with)\b", clean, re.IGNORECASE):
        return clean, "Only read-only queries that start with SELECT (or WITH) are allowed."

    # Ignore words inside quotes and comments when looking for blocked keywords.
    without_strings = re.sub(r"'[^']*'", "''", clean)
    without_comments = re.sub(r"--[^\n]*|/\*.*?\*/", " ", without_strings, flags=re.DOTALL)
    for word in BLOCKED_KEYWORDS:
        if re.search(rf"\b{word}\b", without_comments, re.IGNORECASE):
            return clean, f"The keyword `{word.upper()}` isn't allowed. This app only reads data."

    return clean, None


def friendly_error(exc):
    """Turn a database error into advice a beginner can act on."""
    text = str(exc)
    lowered = text.lower()
    if "18456" in text or "login failed" in lowered:
        return ("Login failed. Check `username` and `password`. Use the SQL "
                "authentication login you created for the server, not your Azure "
                "portal email address.")
    if "40615" in text or ("client with ip address" in lowered and "not allowed" in lowered):
        return ("Azure blocked your IP address. In the Azure portal open your SQL "
                "server > Networking and add a firewall rule for your current client IP.")
    if "4060" in text or "cannot open database" in lowered:
        return "The database name wasn't found. Check `database` (it is case-sensitive)."
    if "208" in text and "invalid object name" in lowered:
        return ("The table wasn't found. Run `sql/setup_sales_table.sql` in your "
                "database first, or change the table name in your query.")
    if "20009" in text or "unable to connect" in lowered or "adaptive server is unavailable" in lowered:
        return ("Couldn't reach the server. Check the `server` name, your internet "
                "connection, and the server's firewall rules. Some campus or office "
                "networks block port 1433, so try another network if it still fails.")
    if "timeout" in lowered or "timed out" in lowered:
        return ("The connection timed out. A serverless database may be waking up, "
                "so wait about a minute and try again.")
    return "The query couldn't be completed. See the technical details below."


def run_query(config, query):
    """
    Connect to Azure SQL Database, run a read-only query, and return a DataFrame.
    Raises ImportError if the optional driver isn't installed, or the database
    error otherwise (app.py turns it into a friendly message).
    """
    import pymssql  # Optional dependency: pip install -r requirements-azure.txt

    connection = pymssql.connect(
        server=config["server"],
        user=config["username"],
        password=config["password"],
        database=config["database"],
        port=1433,
        login_timeout=20,
        timeout=60,
    )
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        if cursor.description is None:
            return pd.DataFrame()
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS)
        return pd.DataFrame(rows, columns=columns)
    finally:
        connection.close()
