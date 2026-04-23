import duckdb
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "master.duckdb"


def find_pdf(license_id: str, region: str) -> str | None:
    for candidate in (DATA_DIR / "pdf" / region).glob(f"{license_id}*.pdf"):
        return str(candidate)
    return None


def load_csv(path: Path, region: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df["source_region"] = region
    df["pdf_path"] = df["License ID"].apply(lambda lid: find_pdf(lid, region))
    df["pdf_indexed"] = False
    return df


def build():
    eu = load_csv(DATA_DIR / "table/EU_ALL.csv", "EU")
    us = load_csv(DATA_DIR / "table/US_ALL.csv", "US")

    for col in [c for c in us.columns if c not in eu.columns]:
        eu[col] = None
    for col in [c for c in eu.columns if c not in us.columns]:
        us[col] = None

    master = pd.concat([eu, us], ignore_index=True)

    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS licenses")
    con.execute("CREATE TABLE licenses AS SELECT * FROM master")
    con.close()

    print(f"total: {len(master)} | EU: {len(eu)} | US: {len(us)}")


if __name__ == "__main__":
    build()
