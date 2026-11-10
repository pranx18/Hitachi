import pandas as pd

from storagepulse.analytics import detect_anomalies, forecast_capacity, health_score, recommendations
from storagepulse.data import generate_telemetry


def test_anomaly_detection_returns_boolean_flags():
    history = generate_telemetry(days=45).query("system_id == 'SP-ARRAY-01'")
    result = detect_anomalies(history)
    assert result["is_anomaly"].dtype == bool
    assert result["is_anomaly"].any()


def test_forecast_is_future_monotonic_and_bounded():
    history = generate_telemetry(days=60).query("system_id == 'SP-ARRAY-01'")
    forecast = forecast_capacity(history, days=30)
    assert len(forecast) == 30
    assert forecast["timestamp"].iloc[0] > history["timestamp"].max()
    assert forecast["used_tb"].is_monotonic_increasing
    assert (forecast["used_tb"] <= forecast["capacity_tb"]).all()


def test_health_and_recommendations_have_expected_content():
    history = generate_telemetry(days=45).query("system_id == 'SP-ARRAY-03'")
    latest = history.iloc[-1]
    forecast = forecast_capacity(history, days=30)
    assert 0 <= health_score(latest, 1) <= 100
    items = recommendations(latest, 1, forecast)
    assert items
    assert {"priority", "action", "detail"}.issubset(items[0])


def test_empty_anomaly_input_is_supported():
    empty = pd.DataFrame(columns=["timestamp", "used_tb", "iops", "latency_ms", "throughput_mbps"])
    assert detect_anomalies(empty).empty
