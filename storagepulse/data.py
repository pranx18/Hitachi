"""Generate and persist deterministic, simulated enterprise storage telemetry."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEMS: dict[str, dict[str, float | str]] = {
    "SP-ARRAY-01": {"site": "Ashburn · Primary", "capacity_tb": 480, "start_util": 0.72, "daily_growth": 0.0017, "latency": 4.8, "iops": 52000, "throughput": 1380},
    "SP-ARRAY-02": {"site": "Ashburn · Archive", "capacity_tb": 960, "start_util": 0.58, "daily_growth": 0.0011, "latency": 8.5, "iops": 31000, "throughput": 920},
    "SP-ARRAY-03": {"site": "Dallas · Primary", "capacity_tb": 720, "start_util": 0.81, "daily_growth": 0.0019, "latency": 12.2, "iops": 44000, "throughput": 1140},
    "SP-ARRAY-04": {"site": "Frankfurt · Primary", "capacity_tb": 640, "start_util": 0.66, "daily_growth": 0.0014, "latency": 6.1, "iops": 38000, "throughput": 1050},
    "SP-ARRAY-05": {"site": "Singapore · Edge", "capacity_tb": 320, "start_util": 0.76, "daily_growth": 0.0020, "latency": 15.0, "iops": 22000, "throughput": 610},
    "SP-ARRAY-06": {"site": "London · Backup", "capacity_tb": 1200, "start_util": 0.49, "daily_growth": 0.0009, "latency": 10.1, "iops": 27000, "throughput": 760},
}

COLUMNS = ["system_id", "site", "timestamp", "capacity_tb", "used_tb", "iops", "latency_ms", "throughput_mbps"]


def generate_telemetry(days: int = 120, seed: int = 42) -> pd.DataFrame:
    """Return seeded daily telemetry for six simulated storage arrays."""
    if days < 14:
        raise ValueError("days must be at least 14 to support trend analysis")

    records: list[dict[str, object]] = []
    end_date = pd.Timestamp.now().normalize()
    for system_number, (system_id, config) in enumerate(SYSTEMS.items()):
        rng = np.random.default_rng(seed + system_number)
        capacity = float(config["capacity_tb"])
        used = capacity * float(config["start_util"])
        growth = float(config["daily_growth"])
        timestamps = pd.date_range(end=end_date, periods=days, freq="D")

        for day, timestamp in enumerate(timestamps):
            daily_growth = capacity * growth * rng.normal(1.0, 0.22)
            if day:
                used = min(capacity * 0.96, used + daily_growth)
            utilization = used / capacity
            iops = max(1000, float(config["iops"]) * (0.9 + utilization * 0.15) * rng.normal(1.0, 0.045))
            latency = max(1.0, float(config["latency"]) * (0.82 + utilization * 0.6) * rng.normal(1.0, 0.07))
            throughput = max(80, float(config["throughput"]) * (0.93 + utilization * 0.1) * rng.normal(1.0, 0.05))

            # Add a few known synthetic incidents so the anomaly workflow is visible in the demo.
            if day == days - 9 and system_number in (0, 2, 4):
                latency *= 3.8
                iops *= 1.65
            if day == days - 24 and system_number in (1, 3):
                throughput *= 0.42

            records.append({
                "system_id": system_id,
                "site": str(config["site"]),
                "timestamp": timestamp,
                "capacity_tb": capacity,
                "used_tb": round(used, 2),
                "iops": round(iops, 1),
                "latency_ms": round(latency, 2),
                "throughput_mbps": round(throughput, 1),
            })

    return pd.DataFrame.from_records(records, columns=COLUMNS)


def load_telemetry(database_path: str | Path | None = None) -> pd.DataFrame:
    """Load persisted demo telemetry, seeding a local SQLite database on first run."""
    path = Path(database_path or os.getenv("STORAGEPULSE_DB", "storagepulse.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        count = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'").fetchone()
        if count is None:
            generate_telemetry().to_sql("telemetry", connection, if_exists="replace", index=False)
        return pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp, system_id", connection, parse_dates=["timestamp"])
