"""ETL pipeline: raw messy CSVs -> cleaned data -> SQLite database.

Steps:  Extract (read CSV)  ->  Transform (clean + validate)  ->  Load (SQLite)
Run:    python pipeline.py
"""
import logging
import sqlite3

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("pipeline")

DB_PATH = "bank.db"


# ---------- EXTRACT ----------
def extract(path: str) -> pd.DataFrame:
    """Read a CSV file. Fail loudly if the file is missing."""
    try:
        df = pd.read_csv(path, dtype=str)  # read everything as text, clean later
    except FileNotFoundError:
        log.error("File not found: %s (run generate_data.py first)", path)
        raise
    log.info("Extracted %d rows from %s", len(df), path)
    return df


# ---------- TRANSFORM ----------
def parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates written in mixed formats (2024-01-05, 05.01.2024, 05/01/2024)."""
    s = series.str.strip()
    result = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    # try each known format; fill in only the dates that are still missing
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        result = result.fillna(pd.to_datetime(s, format=fmt, errors="coerce"))
    return result


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["full_name"] = df["full_name"].str.strip().str.title()
    df["city"] = df["city"].str.strip().str.title()
    df["signup_date"] = parse_dates(df["signup_date"]).dt.strftime("%Y-%m-%d")

    before = len(df)
    df = df.dropna(subset=["customer_id"]).drop_duplicates(subset="customer_id")
    log.info("Customers: removed %d duplicate/invalid rows", before - len(df))
    return df


def clean_transactions(df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    df = df.copy()
    df["txn_id"] = pd.to_numeric(df["txn_id"], errors="coerce").astype("Int64")
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["txn_date"] = parse_dates(df["txn_date"]).dt.strftime("%Y-%m-%d")
    df["category"] = df["category"].str.strip().str.lower()
    df["status"] = df["status"].str.strip().str.lower()

    # amount: "1,234.50" -> 1234.50 ; "123.4 UZS" -> 123.4 ; "" -> NaN
    df["amount"] = (
        df["amount"]
        .str.replace(",", "", regex=False)
        .str.replace("UZS", "", regex=False)
        .str.strip()
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # 1) duplicates
    before = len(df)
    df = df.drop_duplicates(subset="txn_id")
    log.info("Transactions: removed %d duplicate rows", before - len(df))

    # 2) missing amount / date
    before = len(df)
    df = df.dropna(subset=["amount", "txn_date"])
    log.info("Transactions: removed %d rows with missing amount/date", before - len(df))

    # 3) orphans: customer must exist
    before = len(df)
    df = df[df["customer_id"].isin(valid_customer_ids)]
    log.info("Transactions: removed %d orphan rows (unknown customer)", before - len(df))
    return df


def validate(customers: pd.DataFrame, transactions: pd.DataFrame) -> None:
    """Simple data-quality checks. Raises AssertionError if something is wrong."""
    assert customers["customer_id"].is_unique, "customer_id must be unique"
    assert transactions["txn_id"].is_unique, "txn_id must be unique"
    assert (transactions["amount"] > 0).all(), "amounts must be positive"
    assert transactions["customer_id"].isin(customers["customer_id"]).all(), "orphan transactions found"
    log.info("Validation passed")


# ---------- LOAD ----------
def load(customers: pd.DataFrame, transactions: pd.DataFrame, db_path: str = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        customers.to_sql("customers", conn, if_exists="replace", index=False)
        transactions.to_sql("transactions", conn, if_exists="replace", index=False)
    log.info("Loaded %d customers and %d transactions into %s",
             len(customers), len(transactions), db_path)


def main() -> None:
    customers_raw = extract("customers_raw.csv")
    transactions_raw = extract("transactions_raw.csv")

    customers = clean_customers(customers_raw)
    transactions = clean_transactions(transactions_raw, set(customers["customer_id"]))

    validate(customers, transactions)
    load(customers, transactions)


if __name__ == "__main__":
    main()