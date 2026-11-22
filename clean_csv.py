"""Clean a messy bank-transaction CSV and report what was fixed.

Usage:
    python clean_csv.py data/raw/transactions_messy.csv data/clean/transactions_clean.csv
    python clean_csv.py --drop-missing data/raw/transactions_messy.csv data/clean/transactions_clean.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = ["txn_id", "date", "customer", "category", "amount"]

# str.title() lowercases acronyms ("UMBRELLA LLC" -> "Umbrella Llc"); put them back.
ACRONYMS = {"Llc": "LLC"}

# Every date format the raw export uses. Parsed explicitly rather than inferred:
# letting pandas guess would read 01/06/2026 as day-first on some rows and
# month-first on others, giving valid-looking wrong dates instead of an error.
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input_path", help="messy CSV to read")
    parser.add_argument("output_path", help="cleaned CSV to write")
    parser.add_argument(
        "--drop-missing",
        action="store_true",
        help="drop rows with missing values instead of flagging them in is_incomplete",
    )
    return parser.parse_args()


def clean_text(series):
    """Strip padding, normalize casing to Title Case, restore acronyms."""
    series = series.str.strip().str.title()
    for mangled, correct in ACRONYMS.items():
        # \b so only the whole word is replaced, not names that merely contain it.
        series = series.str.replace(rf"\b{mangled}\b", correct, regex=True)
    return series


def clean_dates(series):
    """Parse each known date format in turn and combine the results."""
    parsed = pd.to_datetime(series, format=DATE_FORMATS[0], errors="coerce")
    for fmt in DATE_FORMATS[1:]:
        parsed = parsed.combine_first(pd.to_datetime(series, format=fmt, errors="coerce"))
    return parsed


def clean_amounts(series):
    """Turn "$1,200.50" into 1200.5. The character class excludes "-" so
    negative amounts keep their sign."""
    stripped = series.str.replace(r"[$,\s]", "", regex=True)
    return pd.to_numeric(stripped, errors="coerce").round(2)


def count_unparsed(before, after):
    """Values that held something but failed to convert (blanks don't count)."""
    return int((before.notna() & after.isna()).sum())


def report(stats):
    """Print the summary block."""
    print(f"{'rows in:':<26}{stats['rows_in']:>4}")
    print(f"{'duplicates removed:':<26}{stats['duplicates_removed']:>4}")
    print(f"{'missing values:':<26}{int(stats['missing'].sum()):>4}")
    for column, count in stats["missing"].items():
        if count:
            print(f"  {column:<24}{count:>4}")
    incomplete_label = (
        "rows dropped (missing):" if stats["drop_missing"] else "rows flagged incomplete:"
    )
    print(f"{incomplete_label:<26}{stats['rows_incomplete']:>4}")
    print(f"{'rows out:':<26}{stats['rows_out']:>4}")

    for label, count in (("date", stats["bad_dates"]), ("amount", stats["bad_amounts"])):
        if count:
            print(f"\nwarning: {count} {label} value(s) could not be parsed, set to blank")
    if stats["duplicate_ids"]:
        ids = ", ".join(stats["duplicate_ids"])
        print(f"\nwarning: txn_id still repeats after cleaning: {ids}")


def main():
    args = parse_args()
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    if not input_path.is_file():
        sys.exit(f"error: no such file: {input_path}")

    print(f"Reading {input_path}\n")
    # dtype=str: read every column as text so nothing is coerced before we look at it.
    df = pd.read_csv(input_path, dtype=str)

    absent = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if absent:
        sys.exit(f"error: {input_path} is missing column(s): {', '.join(absent)}")

    rows_in = len(df)
    # Counted before cleaning, so the report describes the input file.
    missing = df.isna().sum()

    df["txn_id"] = df["txn_id"].str.strip()
    df["customer"] = clean_text(df["customer"])
    df["category"] = clean_text(df["category"])

    dates = clean_dates(df["date"])
    bad_dates = count_unparsed(df["date"], dates)
    df["date"] = dates

    amounts = clean_amounts(df["amount"])
    bad_amounts = count_unparsed(df["amount"], amounts)
    df["amount"] = amounts

    # Dedupe after cleaning: rows differing only in spacing or casing have
    # collapsed into exact matches by now, so they get caught too.
    rows_before_dedupe = len(df)
    df = df.drop_duplicates()
    duplicates_removed = rows_before_dedupe - len(df)

    # A txn_id repeating on rows that are otherwise different is a real conflict,
    # so say so rather than dropping one of them.
    duplicate_ids = sorted(df.loc[df["txn_id"].duplicated(), "txn_id"].dropna().unique())

    # Judged on the cleaned frame, so a date or amount that failed to parse
    # counts as missing too, not just a cell that was blank to begin with.
    incomplete = df[EXPECTED_COLUMNS].isna().any(axis=1)
    rows_incomplete = int(incomplete.sum())
    if args.drop_missing:
        df = df.loc[~incomplete]
    else:
        df["is_incomplete"] = incomplete

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, date_format="%Y-%m-%d")

    report(
        {
            "Rows read": rows_in,
            "duplicates_removed": duplicates_removed,
            "missing": missing,
            "rows_out": len(df),
            "rows_incomplete": rows_incomplete,
            "drop_missing": args.drop_missing,
            "bad_dates": bad_dates,
            "bad_amounts": bad_amounts,
            "duplicate_ids": duplicate_ids,
        }
    )
    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
