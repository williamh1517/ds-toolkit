# ds-toolkit

Data science toolkit built around `clean_csv.py`, a script that cleans a messy
bank-transaction CSV and prints a report of what it fixed.

## What it does

Reads a transaction CSV with the columns `txn_id, date, customer, category,
amount` and writes a cleaned copy:

- **Text** — strips padding and normalizes casing to Title Case
  (`  ACME CORP  ` → `Acme Corp`), restoring acronyms that `str.title()`
  mangles (`Umbrella Llc` → `Umbrella LLC`).
- **Dates** — parses the three formats the raw export mixes (`2026-01-05`,
  `01/06/2026`, `07-Jan-2026`) into a single `YYYY-MM-DD` column.
- **Amounts** — turns `"$1,200.50"` into `1200.5`, keeping negative signs.
- **Duplicates** — drops exact duplicate rows, and warns when a `txn_id`
  repeats on rows that are otherwise different.
- **Missing values** — flags incomplete rows in an `is_incomplete` column, or
  drops them with `--drop-missing`.

## Setup

```sh
git clone <repo-url> ds-toolkit
cd ds-toolkit
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```sh
.venv/bin/python clean_csv.py data/raw/transactions_messy.csv data/clean/transactions_clean.csv
```

```
Reading data/raw/transactions_messy.csv

rows in:                    30
duplicates removed:          2
missing values:              5
  date                       1
  customer                   1
  category                   2
  amount                     1
rows flagged incomplete:     5
rows out:                   28

Wrote data/clean/transactions_clean.csv
```

Add `--drop-missing` to drop incomplete rows instead of flagging them; the
label then reads `rows dropped (missing):`. Unparseable dates or amounts are
blanked and warned about rather than silently guessed.

## Project structure

```
clean_csv.py        the cleaning script
hello.py            environment check (interpreter path, pandas version)
requirements.txt    pinned dependencies (pandas, numpy, ipykernel)
data/raw/           input data, committed, never modified
data/clean/         generated output, ignored by Git
```

## Decisions

- **Date formats are listed explicitly**, not inferred. Letting pandas guess
  would read `01/06/2026` as day-first on some rows and month-first on others,
  producing valid-looking wrong dates instead of an error.
- **Every column is read as text** (`dtype=str`) so nothing is coerced before
  the script has looked at it.
- **Deduplication happens after cleaning**, so rows differing only in spacing
  or casing have collapsed into exact matches and get caught too.
- **A repeated `txn_id` is reported, not resolved.** If two rows share an ID
  but differ otherwise, that is a real conflict for a human to settle.
- **Missing-value counts describe the input file**, while the incomplete-row
  flag is judged after cleaning — so a value that failed to parse counts too.
