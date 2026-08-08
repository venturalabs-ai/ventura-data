import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import duckdb

REQUIRED_COLUMNS = ("event_id", "event_time", "category", "value")


@dataclass(frozen=True)
class PipelinePaths:
    source: Path
    bronze: Path
    silver: Path
    gold: Path


class DataQualityError(ValueError):
    pass


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def validate_source(path: Path) -> int:
    if not path.exists():
        raise DataQualityError(f"source file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise DataQualityError(
                f"expected columns {REQUIRED_COLUMNS}, got {tuple(reader.fieldnames or ())}"
            )
        rows = list(reader)
    if not rows:
        raise DataQualityError("source dataset is empty")
    ids = [row["event_id"].strip() for row in rows]
    if any(not item for item in ids):
        raise DataQualityError("event_id must not be empty")
    if len(ids) != len(set(ids)):
        raise DataQualityError("event_id must be unique")
    for row in rows:
        if not row["event_time"].strip() or not row["category"].strip():
            raise DataQualityError("event_time and category are required")
        try:
            float(row["value"])
        except ValueError as exc:
            raise DataQualityError(f"value must be numeric for event_id={row['event_id']}") from exc
    return len(rows)


def run_pipeline(paths: PipelinePaths) -> dict[str, int]:
    source_rows = validate_source(paths.source)
    for path in (paths.bronze, paths.silver, paths.gold):
        _ensure_parent(path)

    con = duckdb.connect()
    source = paths.source.as_posix().replace("'", "''")
    bronze = paths.bronze.as_posix().replace("'", "''")
    silver = paths.silver.as_posix().replace("'", "''")
    gold = paths.gold.as_posix().replace("'", "''")

    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv_auto('{source}', header=true, all_varchar=true)
        ) TO '{bronze}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )

    con.execute(
        f"""
        COPY (
            SELECT
                trim(event_id) AS event_id,
                CAST(event_time AS TIMESTAMPTZ) AS event_time,
                lower(trim(category)) AS category,
                CAST(value AS DOUBLE) AS value
            FROM read_parquet('{bronze}')
            WHERE trim(event_id) <> ''
              AND trim(category) <> ''
        ) TO '{silver}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )

    silver_rows = con.execute(f"SELECT count(*) FROM read_parquet('{silver}')").fetchone()[0]
    if silver_rows != source_rows:
        raise DataQualityError(
            f"row-count contract failed: source={source_rows}, silver={silver_rows}"
        )

    con.execute(
        f"""
        COPY (
            SELECT
                category,
                count(*) AS event_count,
                round(sum(value), 4) AS total_value,
                round(avg(value), 4) AS average_value,
                min(event_time) AS first_event_time,
                max(event_time) AS last_event_time
            FROM read_parquet('{silver}')
            GROUP BY category
            ORDER BY category
        ) TO '{gold}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    gold_rows = con.execute(f"SELECT count(*) FROM read_parquet('{gold}')").fetchone()[0]
    return {"source_rows": source_rows, "silver_rows": silver_rows, "gold_rows": gold_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ventura Data bronze/silver/gold pipeline")
    parser.add_argument("source", type=Path)
    parser.add_argument("--warehouse", type=Path, default=Path("warehouse"))
    args = parser.parse_args()
    result = run_pipeline(
        PipelinePaths(
            source=args.source,
            bronze=args.warehouse / "bronze" / "events.parquet",
            silver=args.warehouse / "silver" / "events.parquet",
            gold=args.warehouse / "gold" / "category_metrics.parquet",
        )
    )
    print(result)


if __name__ == "__main__":
    main()
