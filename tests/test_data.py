from storagepulse.data import SYSTEMS, generate_telemetry, load_telemetry


def test_generated_data_contains_all_systems_and_expected_columns():
    data = generate_telemetry(days=30)
    assert set(data["system_id"]) == set(SYSTEMS)
    assert len(data) == 30 * len(SYSTEMS)
    assert {"capacity_tb", "used_tb", "latency_ms", "iops", "throughput_mbps"}.issubset(data.columns)
    assert (data["used_tb"] <= data["capacity_tb"]).all()


def test_sqlite_seeds_once_and_returns_data(tmp_path):
    database = tmp_path / "telemetry.sqlite"
    first = load_telemetry(database)
    second = load_telemetry(database)
    assert len(first) == len(second)
    assert first["system_id"].nunique() == len(SYSTEMS)
