# StoragePulse workspace guidance

- This is a Python 3.10+ Streamlit demo. Keep the application entry point at the workspace root in `app.py`.
- Keep telemetry generation and SQLite persistence in `storagepulse/data.py`; this is seeded synthetic data, not a live storage integration.
- Keep health scoring, Isolation Forest anomaly detection, Random Forest forecasts, and recommendations in `storagepulse/analytics.py`.
- Declare runtime dependencies in `requirements.txt`. Keep tests under `tests/` and run them with `pytest .`.
- Preserve the synthetic-data disclosure in the UI and documentation. Do not imply production monitoring or guaranteed predictions.
- Local launch command: `streamlit run app.py`. See `README.md` for setup and Streamlit Community Cloud deployment steps.
- Deployment setup is documented but requires the owner's GitHub repository and hosting account to publish externally.

## Setup status

- Workspace scaffolded and dashboard implemented.
- Dependency installation and local Streamlit startup verified.
- Automated tests: 6 passed.
- External deployment not performed; hosting account access is not available in this workspace.
