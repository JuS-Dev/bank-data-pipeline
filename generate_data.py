"""Generate MESSY synthetic banking data (customers + transactions).

All data is fake. The mess is on purpose: the pipeline's job is to clean it.
Run: python generate_data.py
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

FIRST = ["Aziz", "Malika", "Jasur", "Dilnoza", "Bekzod", "Nilufar", "Sardor", "Madina", "Otabek", "Zarina"]
LAST = ["Karimov", "Rakhimova", "Tursunov", "Yusupova", "Aliyev", "Sultanova", "Nazarov", "Ismoilova"]
CITIES = ["Tashkent", "Samarkand", "Bukhara", "Andijan"]
CATEGORIES = ["groceries", "transfer", "utilities", "salary", "transport", "restaurant"]
STATUSES = ["completed", "pending", "failed"]


def messy_date(d: date) -> str:
    """Return the same date in a random format."""
    fmt = random.choice(["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"])
    return d.strftime(fmt)


def messy_text(s: str) -> str:
    """Random extra spaces / upper / lower case."""
    s = random.choice([s, s.upper(), s.lower(), f"  {s} "])
    return s


def make_customers(n=30):
    rows = []
    for cid in range(1, n + 1):
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        signup = date(2022, 1, 1) + timedelta(days=random.randint(0, 900))
        rows.append([cid, messy_text(name), messy_text(random.choice(CITIES)), messy_date(signup)])
    rows.append(rows[3][:])  # duplicate customer row
    return rows


def make_transactions(n=300, n_customers=30):
    rows = []
    for tid in range(1, n + 1):
        cid = random.randint(1, n_customers)
        d = date(2024, 1, 1) + timedelta(days=random.randint(0, 600))
        amount = round(random.uniform(5, 2500), 2)
        # messy amounts: thousands separators, currency text, blanks
        r = random.random()
        if r < 0.15:
            amount_str = f"{amount:,.2f}"          # "1,234.50"
        elif r < 0.22:
            amount_str = f"{amount} UZS"           # "123.4 UZS"
        elif r < 0.27:
            amount_str = ""                        # missing
        else:
            amount_str = str(amount)
        rows.append([tid, cid, messy_date(d), amount_str,
                     messy_text(random.choice(CATEGORIES)), random.choice(STATUSES)])
    rows.append(rows[10][:])                       # duplicate transaction
    rows.append([999, 777, "2024-05-05", "100.0", "transfer", "completed"])  # orphan customer
    return rows


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    write_csv("customers_raw.csv", ["customer_id", "full_name", "city", "signup_date"], make_customers())
    write_csv("transactions_raw.csv",
              ["txn_id", "customer_id", "txn_date", "amount", "category", "status"], make_transactions())
    print("Created customers_raw.csv and transactions_raw.csv")
