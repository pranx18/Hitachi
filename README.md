# StoragePulse

AI-powered simulated storage monitoring and predictive analytics, delivered as a working Streamlit application. StoragePulse includes a seeded, multi-site telemetry dataset, SQLite persistence, Isolation Forest anomaly detection, Random Forest capacity forecasts, operational alerts, and prioritized recommendations.

> **Demo data:** All telemetry is simulated and deterministic. It is not connected to or suitable for monitoring production storage systems.

## Run locally

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the dashboard with `streamlit run app.py`.
4. Open the local URL printed by Streamlit. The first run seeds `storagepulse.db` with 120 days of synthetic telemetry; the database file is ignored by Git.

To use a different local SQLite location, set the `STORAGEPULSE_DB` environment variable before starting the app.

## Dashboard workflow

- Choose one of six simulated enterprise storage arrays in the sidebar.
- Review its health score, capacity, latency, throughput, and IOPS.
- Inspect performance trends and automatically detected unusual samples.
- Generate or refresh a 30-day capacity forecast and review the predicted headroom.
- Use the prioritized recommendations and alerts to guide follow-up actions.

## Tests

Run `pytest` from the project root.

## Deploy to Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository and select `app.py` as the entry point.
3. Deploy. The dependencies are declared in `requirements.txt`; the dashboard does not require credentials or secrets.

SQLite storage on hosted free tiers may be ephemeral, so the demo database can be reseeded after a restart. For production use, replace simulated telemetry and local SQLite with authenticated collection agents, managed PostgreSQL, access controls, retention policies, and operational monitoring. This repository prepares the application for deployment but cannot publish it without access to the user's hosting account and repository.
