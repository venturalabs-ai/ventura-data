from pathlib import Path

from fastapi.testclient import TestClient

from ventura_data.api import app
from ventura_data.pipeline import PipelinePaths, run_pipeline


def test_api_reads_gold_dataset(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "events.csv"
    source.write_text(
        "event_id,event_time,category,value\n"
        "a,2026-08-01T00:00:00Z,Sensor,10\n",
        encoding="utf-8",
    )
    gold = tmp_path / "gold.parquet"
    run_pipeline(
        PipelinePaths(
            source=source,
            bronze=tmp_path / "bronze.parquet",
            silver=tmp_path / "silver.parquet",
            gold=gold,
        )
    )
    monkeypatch.setenv("VENTURA_DATA_GOLD", str(gold))
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/metrics/categories")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["category"] == "sensor"
    assert payload[0]["event_count"] == 1


def test_api_reports_missing_gold(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VENTURA_DATA_GOLD", str(tmp_path / "missing.parquet"))
    response = TestClient(app).get("/metrics/categories")
    assert response.status_code == 503
