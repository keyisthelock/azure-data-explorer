"""
Azure Data Explorer - a beginner-friendly Streamlit dashboard for DP-900 concepts.

Run it with:   streamlit run app.py

Data sources:
  * Sample CSV            - works immediately, no Azure account needed
  * Azure SQL (optional)  - reads the same table from your own Azure SQL Database
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import azure_sql

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_sales.csv"

# Columns the dashboard needs to draw its charts.
REQUIRED_COLUMNS = ["order_id", "order_date", "region", "category", "quantity", "total_amount"]
NUMERIC_COLUMNS = ["quantity", "unit_price", "discount_pct", "total_amount"]

st.set_page_config(page_title="Azure Data Explorer", page_icon="📊", layout="wide")


# ---------------------------------------------------------------------------
# Data loading and validation
# ---------------------------------------------------------------------------

@st.cache_data
def load_sample_data():
    """Read the bundled CSV file. Cached so it loads only once."""
    return pd.read_csv(SAMPLE_CSV)


def make_numbers_numeric(df):
    """SQL DECIMAL values arrive as Python Decimals; turn them into normal numbers."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col], errors="coerce")
            if df[col].notna().any() and converted.notna().sum() == df[col].notna().sum():
                df[col] = converted
    return df


def prepare_sales_data(df):
    """
    Check that the data has the columns the dashboard needs and clean the types.
    Returns (clean_df, missing_columns, warnings).
    """
    df = make_numbers_numeric(df)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return df, missing, []

    warnings = []
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    bad_rows = df["order_date"].isna() | df["total_amount"].isna() | df["quantity"].isna()
    if bad_rows.any():
        warnings.append(
            f"Skipped {int(bad_rows.sum())} row(s) with a missing or invalid date, "
            "quantity or amount."
        )
        df = df[~bad_rows]

    return df, [], warnings


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def rupees(value):
    return f"₹{value:,.0f}"


def show_filters(df):
    """Sidebar filters for region and category."""
    st.sidebar.subheader("Filters")
    regions = sorted(df["region"].dropna().unique())
    categories = sorted(df["category"].dropna().unique())
    chosen_regions = st.sidebar.multiselect("Region", regions, default=regions)
    chosen_categories = st.sidebar.multiselect("Category", categories, default=categories)
    return df[df["region"].isin(chosen_regions) & df["category"].isin(chosen_categories)]


def show_dashboard(df, source_label):
    """Metrics, charts, preview table and summary statistics for sales data."""
    df = show_filters(df)
    if df.empty:
        st.warning("No rows match the current filters. Select at least one region and one category.")
        return

    st.caption(
        f"Source: **{source_label}** · {len(df):,} rows · "
        f"{df['order_date'].min():%d %b %Y} to {df['order_date'].max():%d %b %Y}"
    )

    # 1. Summary metrics
    revenue = df["total_amount"].sum()
    orders = df["order_id"].nunique()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total revenue", rupees(revenue))
    col2.metric("Orders", f"{orders:,}")
    col3.metric("Average order value", rupees(revenue / orders))
    col4.metric("Units sold", f"{int(df['quantity'].sum()):,}")

    # 2. Charts
    st.subheader("Revenue by month")
    monthly = df.groupby(df["order_date"].dt.strftime("%Y-%m"))["total_amount"].sum()
    monthly.index.name = "Month"
    st.line_chart(monthly.rename("Revenue (₹)"))

    left, right = st.columns(2)
    with left:
        st.subheader("Revenue by category")
        by_category = df.groupby("category")["total_amount"].sum().sort_values(ascending=False)
        by_category.index.name = "Category"
        st.bar_chart(by_category.rename("Revenue (₹)"))
    with right:
        st.subheader("Orders by region")
        by_region = df.groupby("region")["order_id"].nunique().sort_values(ascending=False)
        by_region.index.name = "Region"
        st.bar_chart(by_region.rename("Orders"))

    # 3. Data preview and statistics
    st.subheader("Data preview")
    st.dataframe(df.head(50), hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales.csv",
        mime="text/csv",
    )

    with st.expander("Summary statistics (numeric columns)"):
        numeric = [c for c in NUMERIC_COLUMNS if c in df.columns]
        st.dataframe(df[numeric].describe().T.round(2))
        st.caption("count = rows, mean = average, std = spread, min / 25% / 50% / 75% / max = distribution.")


def show_generic_result(df):
    """Used when an Azure SQL query returns columns other than the sales table's."""
    st.info(
        "Your query worked. The full dashboard needs these columns: "
        + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS)
        + ". Showing the result as a table instead."
    )
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    st.dataframe(df, hide_index=True)
    numeric = df.select_dtypes("number")
    if not numeric.empty:
        with st.expander("Summary statistics (numeric columns)"):
            st.dataframe(numeric.describe().T.round(2))


# ---------------------------------------------------------------------------
# Azure SQL section
# ---------------------------------------------------------------------------

def azure_sql_page():
    st.header("Azure SQL Database (optional)")
    st.markdown(
        "Read data from **your own** Azure SQL Database. Credentials are loaded from "
        "`.streamlit/secrets.toml` or environment variables. They are never typed into "
        "this page, shown on screen, or stored in the code."
    )

    config, source, problems = azure_sql.load_config()

    with st.container(border=True):
        st.markdown("#### 🔐 Configuration status")
        if problems:
            st.error("Azure SQL isn't configured yet, so this mode can't connect.")
            for problem in problems:
                st.markdown(f"- {problem}")
            st.markdown(
                "**How to fix:** copy `.streamlit/secrets.toml.example` to "
                "`.streamlit/secrets.toml`, fill in your own values, then restart the app. "
                "See *Optional: Azure SQL setup* in the README."
            )
            st.info("Tip: switch to **Sample CSV** in the sidebar to explore the dashboard without Azure.")
            return
        st.success(f"Configuration found (from {source}).")
        st.markdown(f"- **Server:** `{config['server']}`\n- **Database:** `{config['database']}`")
        st.caption("The username and password are loaded but deliberately not displayed.")

    st.markdown("#### Sample SQL query")
    st.markdown(
        "This query reads up to **500 rows** (`TOP (500)`) from the `dbo.Sales` table, keeps "
        "only orders from 2026 onwards (`WHERE`), and sorts them by date (`ORDER BY`). "
        "It returns the same columns as the sample CSV, so the full dashboard can be drawn."
    )
    with st.expander("Another example: an aggregate query (GROUP BY)"):
        st.code(azure_sql.AGGREGATE_QUERY, language="sql")
        st.caption(
            "This one totals orders and revenue per category inside the database. "
            "It is an analytical query, so its result is shown as a table."
        )

    query = st.text_area("SQL query (read-only SELECT)", value=azure_sql.SAMPLE_QUERY, height=180)

    if st.button("Run query", type="primary"):
        clean_query, error = azure_sql.validate_query(query)
        if error:
            st.warning(error)
            return
        with st.spinner("Connecting to Azure SQL Database..."):
            try:
                st.session_state["azure_result"] = azure_sql.run_query(config, clean_query)
            except ImportError:
                st.error(
                    "The optional Azure SQL driver isn't installed. Run "
                    "`pip install -r requirements-azure.txt` and restart the app."
                )
                return
            except Exception as exc:
                st.session_state.pop("azure_result", None)
                st.error(azure_sql.friendly_error(exc))
                with st.expander("Technical details"):
                    st.code(f"{type(exc).__name__}: {exc}")
                return

    result = st.session_state.get("azure_result")
    if result is None:
        return
    if result.empty:
        st.info("The query ran successfully but returned no rows.")
        return

    st.divider()
    data, missing, warnings = prepare_sales_data(result)
    if missing:
        show_generic_result(data)
        return
    for message in warnings:
        st.warning(message)
    if data.empty:
        st.warning("No valid rows to chart after cleaning the data.")
        return
    show_dashboard(data, "Azure SQL Database")


# ---------------------------------------------------------------------------
# DP-900 explanation
# ---------------------------------------------------------------------------

def show_dp900_concepts():
    with st.expander("📘 How this project maps to DP-900 (Azure Data Fundamentals)"):
        st.markdown(
            """
| DP-900 concept | Where you see it in this app |
|---|---|
| **Relational data** | Sales are stored as rows and columns with a fixed schema. Each row is one order and `order_id` is the primary key. |
| **Tables & data types** | `sql/setup_sales_table.sql` creates `dbo.Sales` with `DATE`, `INT`, `DECIMAL` and `VARCHAR` columns. |
| **SQL queries (DQL)** | The Azure SQL page runs `SELECT ... WHERE ... ORDER BY` and `GROUP BY` queries. |
| **DDL vs DML** | The setup script uses DDL (`CREATE TABLE`) and DML (`INSERT`). The app itself only reads data. |
| **File-based data** | The sample CSV is delimited text, a common format for moving data before it is loaded into a database. |
| **Analytics & visualization** | Totals, averages, trends over time and group comparisons, like a mini Power BI report. |
| **Cloud data services (PaaS)** | Azure SQL Database is a managed service: Microsoft runs the servers, patching and backups. |
| **Security** | Credentials stay in secrets or environment variables, and the server firewall controls who can connect. |
"""
        )


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main():
    st.title("📊 Azure Data Explorer")
    st.markdown(
        "A small dashboard that explores retail sales data, either from a local **CSV file** "
        "or from **Azure SQL Database**, to demonstrate core ideas from "
        "*Microsoft Azure Data Fundamentals (DP-900)*."
    )
    show_dp900_concepts()

    st.sidebar.header("Data source")
    source = st.sidebar.radio(
        "Choose where to read data from",
        ["Sample CSV", "Azure SQL (optional)"],
        help="Sample CSV works without any Azure account.",
    )

    if source == "Sample CSV":
        try:
            raw = load_sample_data()
        except FileNotFoundError:
            st.error(f"Sample file not found: `{SAMPLE_CSV}`. Make sure the `data` folder was downloaded.")
            return
        except Exception as exc:
            st.error(f"Couldn't read the sample CSV: {exc}")
            return

        data, missing, warnings = prepare_sales_data(raw)
        if missing:
            st.error("The CSV is missing required columns: " + ", ".join(f"`{c}`" for c in missing))
            return
        for message in warnings:
            st.warning(message)
        st.header("Sample sales data")
        show_dashboard(data, "data/sample_sales.csv")
    else:
        azure_sql_page()


main()
