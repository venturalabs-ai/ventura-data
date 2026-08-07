from pathlib import Path

import duckdb
import pytest

from ventura_data.pipeline import DataQualityError, PipelinePaths, run_pipeline, validate_source


def test_pipeline_builds_bronze_silver_gold(tmp_path: Path) -> None:
    source = tmp_path / "events.csv"
    source.write_text(
        "event_id,event_time,category,value\n"
        "a,2026-08-01T00:00:00Z,Sensor,10\n"
        "b,2026-08-01T01:00:00Z,Sensor,20\n"
        "c,2026-08-01T02:00:00Z,Maintenance,5\n",
        encoding="utf-8",
    )
    paths = PipelinePaths(
        source=source,
        bronze=tmp_path / "bronze.parquet",
        silver=tmp_path / "silver.parquet",
        gold=tmp_path / "gold.parquet",
    )
    result = run_pipeline(paths)
    assert result == {"source_rows": 3, "silver_rows": 3, "gold_rows": 2}
    rows = duckdb.connect().execute(
        f"SELECT category, event_count, total_value FROM read_parquet('{paths.gold.as_posix()}') ORDER BY category"
    ).fetchall()
    assert rows == [("maintenance", 1, 5.0), ("sensor", 2, 30.0)]


def test_quality_rejects_duplicate_ids(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text(
        "event_id,event_time,category,value\n"
        "a,2026-08-01T00:00:00Z,Sensor,10\n"
        "a,2026-08-01T01:00:00Z,Sensor,20\n",
        encoding="utf-8",
    )
    with pytest.raises(DataQualityError, match="unique"):
        validate_source(source)


def test_quality_rejects_wrong_schema(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("id,value\na,1\n", encoding="utf-8")
    with pytest.raises(DataQualityError, match="expected columns"):
        validate_source(source)
