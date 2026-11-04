"""One-off: copy every row from the old Postgres database into a SQLite file.

    cd cms
    uv sync --extra migrate
    DATABASE_URL=sqlite:///./cms.db uv run alembic upgrade head
    uv run python -m scripts.copy_postgres_to_sqlite \
        postgresql+psycopg://cms:cms@localhost:5432/cms sqlite:///./cms.db

The target must already have the schema (alembic upgrade head) and be empty.
Ids are copied as-is, so foreign keys and the static site's links stay valid.
Row counts are compared at the end; any mismatch exits non-zero.
"""

import sys

from sqlalchemy import create_engine, func, insert, select, text

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db import Base


def main(source_url: str, target_url: str) -> int:
    source = create_engine(source_url)
    target = create_engine(target_url)
    tables = Base.metadata.sorted_tables  # parents before children

    with target.connect() as conn:
        for table in tables:
            if conn.scalar(select(func.count()).select_from(table)):
                sys.exit(f"target table {table.name} is not empty; aborting")

    with source.connect() as src, target.begin() as dst:
        if target.dialect.name == "sqlite":
            dst.execute(text("PRAGMA foreign_keys=OFF"))
        for table in tables:
            rows = [dict(r._mapping) for r in src.execute(select(table))]
            if rows:
                dst.execute(insert(table), rows)
            print(f"{table.name}: {len(rows)} rows")

    bad = 0
    with source.connect() as src, target.connect() as dst:
        for table in tables:
            a = src.scalar(select(func.count()).select_from(table))
            b = dst.scalar(select(func.count()).select_from(table))
            if a != b:
                bad += 1
                print(f"MISMATCH {table.name}: source {a}, target {b}")
    print("OK: all row counts match" if not bad else f"{bad} table(s) differ")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
