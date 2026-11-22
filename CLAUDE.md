# ds-toolkit

Data science toolkit: environment setup, Git workflow, and a CSV-cleaning script.

## Environment
- Python 3.14 in `.venv`. Run code with `.venv/bin/python`.
- Install packages with `.venv/bin/pip install <pkg>`, then update `requirements.txt` with `pip freeze`.

## How to run
- `.venv/bin/python clean_csv.py data/raw/transactions_messy.csv data/clean/transactions_clean.csv`
- Add `--drop-missing` to drop incomplete rows instead of flagging them.

## Structure
- `data/raw/`: input data, committed. Never modify.
- `data/clean/`: generated output, ignored by Git.

## Conventions
- pandas for data work. Small, single-purpose functions.
- Plan before coding any change that touches more than one function.
- Keep changes small and explain what each changed file does.

## Git
- Never run git commands. William commits and pushes himself.