# 📊 Azure Data Explorer

A small, beginner-friendly **Streamlit** web app that explores retail sales data and demonstrates core ideas from **Microsoft Azure Data Fundamentals (DP-900)**.

- **Works immediately** with an included sample CSV. No Azure account or credentials needed.
- **Optionally** reads the same data from **your own Azure SQL Database** using a read-only SQL query.
- Includes a **no-install web version** (`docs/index.html`) with the dashboard, a working **SQL Lab** that runs real SQL in the browser, CSV upload and a DP-900 quiz.

> 🔐 **Security first:** this repository contains **no real credentials**. Every student must use **their own** Azure details, keep them in a local secrets file or environment variables, and **never commit them to GitHub**.

---

## Contents

1. [What this project demonstrates](#1-what-this-project-demonstrates)
2. [Download or clone](#2-download-or-clone-the-repository)
3. [Install the dependencies](#3-install-the-python-dependencies)
4. [Run the app](#4-run-the-app)
5. [Use sample-data mode (no Azure)](#5-use-sample-data-mode-no-azure-needed)
6. [Optional: Azure SQL setup](#6-optional-azure-sql-setup)
7. [Configure secrets locally without committing them](#7-configure-secrets-locally-without-committing-them)
8. [Common errors and fixes](#8-common-errors-and-fixes)
9. [Files and how to customize](#9-project-files-and-how-to-customize-them)

---

## 1. What this project demonstrates

The app loads 240 sample orders (January to June 2026) and shows summary metrics, three charts, a data preview and summary statistics. You can filter by region and category.

| DP-900 concept | Where it appears in this project |
|---|---|
| **Relational data** | Orders are rows in a table with a fixed schema. `order_id` is the primary key. |
| **Tables and data types** | `sql/setup_sales_table.sql` creates `dbo.Sales` with `DATE`, `INT`, `DECIMAL` and `VARCHAR` columns. |
| **SQL: DDL, DML and queries** | `CREATE TABLE` (DDL), `INSERT` (DML), and `SELECT ... WHERE ... ORDER BY` / `GROUP BY` queries. |
| **File-based data** | `data/sample_sales.csv` is delimited text, a common way to move data between systems. |
| **Analytical workloads** | Totals, averages, a trend over time and comparisons between groups. These are the same ideas behind Power BI reports. |
| **Cloud data services (PaaS)** | Azure SQL Database is a managed relational database: Microsoft handles the servers, patching and backups. |
| **Security basics** | Credentials live outside the code, the server firewall restricts access, and a read-only database user is recommended. |

### Web version (no Python needed)

`docs/index.html` is a single self-contained page. Double-click it to open it in any modern browser (it needs internet access to load fonts and the SQL engine). It has four modules:

- **Dashboard:** the same metrics and charts as the Streamlit app, with region, category and channel filters. Switch to **Your CSV** to load your own file. It stays in your browser and is not uploaded anywhere.
- **SQL Lab:** write `SELECT` queries against a `Sales` table (`dbo.Sales` works too) and see the results. It uses [AlaSQL](https://github.com/AlaSQL/alasql), an in-browser SQL engine, and has the same read-only guard as the app.
- **Azure SQL:** how the Streamlit app connects, with placeholder settings only. The web page never connects to Azure and never asks for credentials.
- **DP-900:** the concept map and a short quiz.

To host it for free, you can turn on **GitHub Pages** in your repository (**Settings → Pages → Deploy from a branch → `main` / `/docs`**). This is optional.

---

## 2. Download or clone the repository

You need **Python 3.10 or newer** (3.11 or 3.12 recommended). Check your version:

```powershell
# Windows PowerShell
python --version
```

```bash
# macOS / Linux
python3 --version
```

**Option A: Git clone:**

```bash
git clone https://github.com/keyisthelock/azure-data-explorer.git
cd azure-data-explorer
```

**Option B: Download ZIP.** On the GitHub page click **Code → Download ZIP**, unzip it, and open a terminal inside the unzipped `azure-data-explorer` folder.

---

## 3. Install the Python dependencies

A *virtual environment* keeps this project's packages separate from the rest of your computer.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

You'll see `(.venv)` at the start of your terminal prompt when the environment is active. Run the activate command again each time you open a new terminal.

> Only want the sample data? `requirements.txt` (Streamlit + pandas) is all you need. The Azure SQL driver is installed separately in [step 6](#6-optional-azure-sql-setup).

---

## 4. Run the app

With the virtual environment active, from the project folder (same command on every OS):

```bash
streamlit run app.py
```

Your browser opens at **http://localhost:8501**. If it doesn't, open that address yourself. Press `Ctrl + C` in the terminal to stop the app.

If `streamlit` is "not recognized", use `python -m streamlit run app.py` instead.

**Windows shortcut:** double-click `run_app.bat` in the project folder. On the first run it creates `.venv` and installs the packages, and after that it just starts the app. Then open http://localhost:8501.

---

## 5. Use sample-data mode (no Azure needed)

1. In the left sidebar, keep **Data source → Sample CSV** selected (the default).
2. Explore the page:
   - **Metrics:** total revenue, number of orders, average order value, units sold
   - **Charts:** revenue by month, revenue by category, orders by region
   - **Data preview:** the first 50 rows, plus a button to download the filtered data
   - **Summary statistics:** count, mean, min, max and so on for the numeric columns
3. Use the **Region** and **Category** filters in the sidebar. Every metric and chart updates.
4. Open **"How this project maps to DP-900"** at the top for the concept summary.

---

## 6. Optional: Azure SQL setup

> ⚠️ Nothing in this repository creates Azure resources for you, and the Azure SQL steps below are a guide that you must follow and verify in your own subscription. Azure resources can cost money, so check the pricing and any free offers available to your account (for example Azure for Students, or the Azure SQL Database free offer) before you create anything, and delete resources you no longer need.

### 6.1 Create a database (Azure portal)

1. Sign in to <https://portal.azure.com> and search for **SQL databases → Create**.
2. **Basics:** choose your subscription and a resource group, then enter a database name (e.g. `salesdb`).
3. **Server → Create new:** pick a globally unique server name and a region. For **Authentication**, choose an option that includes **SQL authentication**, and create an admin login and a strong password. Store them in a password manager, **not** in this project.
4. Choose the smallest compute option your budget allows (serverless or Basic is plenty for 240 rows).
5. **Networking:** choose **Public endpoint**, and set **Add current client IP address** to **Yes**.
6. **Review + create → Create**, and wait for the deployment to finish.

### 6.2 Create the table and load the sample rows

1. Open your database in the portal and select **Query editor**. Sign in with your SQL login.
2. Open `sql/setup_sales_table.sql` from this project, paste the whole file into the editor and click **Run**.
   - The script creates `dbo.Sales` and inserts the same 240 rows as the CSV. It is safe to re-run: it drops and recreates the table.
3. The last statement should return `row_count = 240`.

### 6.3 (Recommended) Create a read-only user for the app

The app only reads data, so give it a login that *can only* read. Run this in the Query editor, replacing the placeholder with a strong password of your own:

```sql
CREATE USER dashboard_reader WITH PASSWORD = '<choose-a-strong-password>';
ALTER ROLE db_datareader ADD MEMBER dashboard_reader;
```

Then use `dashboard_reader` as the `username` in step 7.

### 6.4 Install the Azure SQL driver

With your virtual environment active:

```bash
pip install -r requirements-azure.txt
```

This adds [`pymssql`](https://pypi.org/project/pymssql/), a pip-installable SQL Server driver (no separate ODBC install needed).

### 6.5 Add your credentials and connect

1. Configure your secrets as described in [step 7](#7-configure-secrets-locally-without-committing-them).
2. Restart the app (`Ctrl + C`, then `streamlit run app.py`).
3. In the sidebar choose **Azure SQL (optional)**. The **Configuration status** box tells you whether everything was found.
4. Click **Run query**. The sample query is pre-filled:

```sql
SELECT TOP (500)
    order_id, order_date, region, city, category, product,
    channel, quantity, unit_price, discount_pct, total_amount
FROM dbo.Sales
WHERE order_date >= '2026-01-01'
ORDER BY order_date;
```

**What it does:** reads at most 500 rows (`TOP (500)`) from the `dbo.Sales` table, keeps only orders from 1 January 2026 onwards (`WHERE`), and sorts them oldest first (`ORDER BY`). Because it returns the same columns as the CSV, the full dashboard is drawn from cloud data.

The app also shows a `GROUP BY` example that totals revenue per category inside the database. Results with other columns are shown as a table with summary statistics.

**Query rules in the app:** one statement at a time, starting with `SELECT` or `WITH`. Keywords that change data (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `INTO`, and others) are rejected, and at most 5,000 rows are read. This is a classroom-level check. The real protection is the read-only user from step 6.3.

---

## 7. Configure secrets locally without committing them

The app looks for credentials in this order:

1. **Streamlit secrets:** `.streamlit/secrets.toml`, section `[azure_sql]`
2. **Environment variables:** `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, `AZURE_SQL_USERNAME`, `AZURE_SQL_PASSWORD`

There is deliberately **no** page in the app for typing or pasting credentials, and the app never displays your username or password.

### Option A: Streamlit secrets file (recommended)

Copy the example file:

```powershell
# Windows PowerShell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

```bash
# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` in an editor and replace **every** placeholder with your own values:

```toml
[azure_sql]
server   = "your-server-name.database.windows.net"
database = "your-database-name"
username = "your-sql-username"
password = "your-password-here"
```

`server` is the **Server name** on your database's **Overview** page in the portal (it ends in `.database.windows.net`). Leave out `https://`.

### Option B: Environment variables (current terminal only)

```powershell
# Windows PowerShell
$env:AZURE_SQL_SERVER   = "your-server-name.database.windows.net"
$env:AZURE_SQL_DATABASE = "your-database-name"
$env:AZURE_SQL_USERNAME = "your-sql-username"
$env:AZURE_SQL_PASSWORD = "your-password-here"
streamlit run app.py
```

```bash
# macOS / Linux
export AZURE_SQL_SERVER="your-server-name.database.windows.net"
export AZURE_SQL_DATABASE="your-database-name"
export AZURE_SQL_USERNAME="your-sql-username"
export AZURE_SQL_PASSWORD="your-password-here"
streamlit run app.py
```

`.env.example` lists the same variable names for reference. The app does **not** read a `.env` file automatically.

### Before every commit: check that no secret is staged

`.gitignore` already excludes `.streamlit/secrets.toml`, `.env` and similar files. Confirm it:

```bash
git check-ignore -v .streamlit/secrets.toml   # should print the .gitignore rule
git status                                    # secrets.toml must NOT be listed
```

- Never put real values in the `.example` files, the README, code, issues or screenshots.
- **If a password is ever committed or shared by accident:** change it in Azure **immediately** (SQL server → *Reset password*, or `ALTER USER ... WITH PASSWORD` for the read-only user). Deleting the file afterwards is not enough, because it stays in the Git history.

---

## 8. Common errors and fixes

| Problem | Fix |
|---|---|
| `python` / `python3` not recognized | Install Python from <https://www.python.org/downloads/>. On Windows, tick **"Add python.exe to PATH"** during setup, then open a new terminal. |
| PowerShell: *"running scripts is disabled on this system"* when activating | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, then activate again. |
| `streamlit` not recognized | Activate the virtual environment first, or run `python -m streamlit run app.py`. |
| `ModuleNotFoundError: No module named 'streamlit'` (or `pandas`) | Activate the virtual environment, then `pip install -r requirements.txt`. |
| *"Sample file not found"* | Run the command from the project folder and make sure `data/sample_sales.csv` exists. |
| Port 8501 already in use | Stop the other app, or run `streamlit run app.py --server.port 8502`. |
| *"Azure SQL isn't configured yet"* | Create `.streamlit/secrets.toml` (step 7), replace all placeholders, and restart the app. |
| *"The optional Azure SQL driver isn't installed"* | `pip install -r requirements-azure.txt`, then restart the app. |
| `pymssql` fails to install | Upgrade pip (`python -m pip install --upgrade pip`) and try again. If it still fails, use Python 3.11 or 3.12. |
| *"Login failed"* | Check the username and password. Use the SQL login you created, not your Azure portal email. |
| *"Azure blocked your IP address"* | SQL server → **Networking** → add your current client IP as a firewall rule → **Save**. Your IP changes when you change networks. |
| *"Couldn't reach the server"* | Check the server name, then the firewall rule. Some campus networks block port **1433**, so try a phone hotspot. |
| *"The table wasn't found"* | Run `sql/setup_sales_table.sql` in your database (step 6.2). |
| *"The connection timed out"* | A serverless database may be paused. Wait about a minute and click **Run query** again. |

---

## 9. Project files and how to customize them

```
azure-data-explorer/
├── app.py                         # Streamlit UI: data source selector, metrics, charts, Azure SQL page
├── azure_sql.py                   # Reads credentials securely, validates queries, runs them on Azure SQL
├── data/
│   └── sample_sales.csv           # 240 sample orders, used by default
├── docs/
│   └── index.html                 # No-install web version (dashboard, SQL Lab, quiz)
├── sql/
│   └── setup_sales_table.sql      # Creates dbo.Sales in Azure SQL and inserts the same 240 rows
├── .streamlit/
│   ├── config.toml                # Theme settings (no secrets, safe to commit)
│   └── secrets.toml.example       # Placeholder credentials. Copy to secrets.toml (git-ignored)
├── .env.example                   # Placeholder environment variable names
├── .gitignore                     # Keeps secrets.toml, .env and .venv out of Git
├── requirements.txt               # Core packages: streamlit, pandas
├── requirements-azure.txt         # Optional: adds pymssql for Azure SQL mode
├── run_app.bat                    # Windows one-click launcher (sets up .venv, starts the app)
└── README.md
```

**Ideas for customizing:**

- **Use your own CSV:** replace `data/sample_sales.csv`. The dashboard needs these columns: `order_id`, `order_date`, `region`, `category`, `quantity`, `total_amount`. Change `REQUIRED_COLUMNS` in `app.py` if your data is different.
- **Add a chart:** copy one of the `groupby(...)` blocks in `show_dashboard()` in `app.py`. For example, group by `channel` to compare online and in-store sales.
- **Change the default query:** edit `SAMPLE_QUERY` in `azure_sql.py`.
- **Change the theme colour:** edit `primaryColor` in `.streamlit/config.toml`.
- **Extend the DP-900 story:** add an expander on non-relational data (e.g. Azure Cosmos DB) or explain how this data could feed Power BI.
