from __future__ import annotations

import os
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Ventura Data API", version="0.1.0")


def gold_path() -> Path:
    return Path(os.getenv("VENTURA_DATA_GOLD", "warehouse/gold/category_metrics.parquet"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/categories")
def category_metrics() -> list[dict[str, object]]:
    path = gold_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail="gold dataset not built")
    escaped = path.as_posix().replace("'", "''")
    con = duckdb.connect()
    rows = con.execute(
        f"""
        SELECT category, event_count, total_value, average_value,
               first_event_time, last_event_time
        FROM read_parquet('{escaped}')
        ORDER BY category
        """
    ).fetchall()
    columns = [item[0] for item in con.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]
