"""Health scoring, anomaly detection, forecasting, and action recommendations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor

FEATURES = ["used_tb", "iops", "latency_ms", "throughput_mbps"]


def health_score(latest: pd.Series, anomaly_count: int = 0) -> int:
    """Calculate an explainable 0–100 health score from the latest sample."""
    utilization = float(latest["used_tb"]) / float(latest["capacity_tb"])
    capacity_score = np.clip((0.93 - utilization) / 0.53, 0, 1) * 100
    latency_score = np.clip((35 - float(latest["latency_ms"])) / 30, 0, 1) * 100
    anomaly_score = max(0, 100 - anomaly_count * 14)
    return int(round(0.55 * capacity_score + 0.30 * latency_score + 0.15 * anomaly_score))


def detect_anomalies(history: pd.DataFrame, contamination: float = 0.04) -> pd.DataFrame:
    """Flag unusual performance samples with a per-system Isolation Forest."""
    if history.empty:
        return history.assign(is_anomaly=pd.Series(dtype=bool))
    result = history.sort_values("timestamp").copy()
    features = result[FEATURES].astype(float)
    model = IsolationForest(n_estimators=160, contamination=contamination, random_state=17)
    result["is_anomaly"] = model.fit_predict(features) == -1
    return result


def forecast_capacity(history: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """Forecast daily used capacity using a Random Forest and recent growth floor."""
    if days < 1:
        raise ValueError("days must be positive")
    data = history.sort_values("timestamp").reset_index(drop=True)
    if len(data) < 14:
        raise ValueError("at least 14 telemetry samples are required")

    used = data["used_tb"].astype(float).to_numpy()
    capacity = float(data["capacity_tb"].iloc[-1])
    utilization = used / capacity
    rows: list[list[float]] = []
    targets: list[float] = []
    for index in range(7, len(used)):
        recent_growth = float(np.mean(np.diff(used[index - 7:index + 1])))
        rows.append([float(index), used[index], float(utilization[index]), recent_growth])
        targets.append(float(used[index + 1]) if index + 1 < len(used) else float(used[index]))

    # Train against one-step-ahead values, excluding the last row without a known target.
    features = np.asarray(rows[:-1])
    target = np.asarray(used[8:])
    model = RandomForestRegressor(n_estimators=180, min_samples_leaf=3, random_state=17)
    model.fit(features, target)

    recent_deltas = np.diff(used[-15:])
    positive_growth = recent_deltas[recent_deltas > 0]
    growth_floor = float(np.median(positive_growth)) if len(positive_growth) else 0.0
    current = float(used[-1])
    forecast_rows: list[dict[str, object]] = []
    last_date = pd.Timestamp(data["timestamp"].iloc[-1])
    for offset in range(1, days + 1):
        recent_growth = float(np.mean(np.diff(used[-8:]))) if len(used) > 1 else 0.0
        model_prediction = float(model.predict(np.array([[len(data) + offset - 1, current, current / capacity, recent_growth]]))[0])
        predicted_growth = max(model_prediction - current, growth_floor * 0.75, 0.0)
        predicted_growth = min(predicted_growth, capacity * 0.02)
        current = min(capacity, current + predicted_growth)
        forecast_rows.append({
            "timestamp": last_date + pd.Timedelta(offset, unit="D"),
            "used_tb": round(current, 2),
            "capacity_tb": capacity,
            "utilization_pct": round(current / capacity * 100, 2),
            "kind": "Forecast",
        })

    return pd.DataFrame(forecast_rows)


def recommendations(latest: pd.Series, anomalies: int, forecast: pd.DataFrame) -> list[dict[str, str]]:
    """Return prioritized, human-readable actions based on current and forecast state."""
    capacity = float(latest["capacity_tb"])
    used = float(latest["used_tb"])
    utilization = used / capacity
    final_utilization = float(forecast["utilization_pct"].iloc[-1]) if not forecast.empty else utilization * 100
    actions: list[dict[str, str]] = []

    if utilization >= 0.85 or final_utilization >= 90:
        actions.append({"priority": "High", "action": "Plan a capacity expansion", "detail": f"Current use is {utilization:.0%}; forecast reaches {final_utilization:.1f}% within 30 days."})
    elif utilization >= 0.72 or final_utilization >= 80:
        actions.append({"priority": "Medium", "action": "Review capacity allocation", "detail": f"Usage is trending toward {final_utilization:.1f}%. Reclaim stale snapshots and review tiering."})
    else:
        actions.append({"priority": "Low", "action": "Maintain capacity watch", "detail": f"Projected utilization remains near {final_utilization:.1f}% over the next 30 days."})

    if float(latest["latency_ms"]) >= 20:
        actions.append({"priority": "High", "action": "Investigate storage latency", "detail": "Check controller load, queue depth, and the busiest workloads."})
    elif float(latest["latency_ms"]) >= 12:
        actions.append({"priority": "Medium", "action": "Review workload placement", "detail": "Current response time is elevated; rebalance high-IOPS workloads if needed."})

    if anomalies:
        actions.append({"priority": "Medium", "action": "Review detected anomalies", "detail": f"{anomalies} unusual samples were found in the selected system's telemetry."})
    if not any(item["action"] == "Review workload placement" for item in actions) and float(latest["latency_ms"]) < 12:
        actions.append({"priority": "Low", "action": "Verify recovery readiness", "detail": "Confirm recent snapshots and a restore test are available for this system."})
    return actions
