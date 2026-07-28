# Havn

Havn is a local-first, privacy-preserving personal data platform. It ingests export dumps from the services you already use (Google Takeout, Spotify, Apple Health, GitHub, bank CSVs, etc.), normalizes them into a single queryable local database (DuckDB), and lets you discover cross-service correlations about your own life.

## Features
- **100% Local-First**: No data ever leaves your machine. Your personal data stays in your local DuckDB database.
- **Insights Feed**: Automatically surfaces statistically significant correlations across different data sources without you needing to know what to ask.
- **Format-Agnostic Ingestion**: Built to handle messy, inconsistently versioned data dumps with graceful degradation.
- **Explainable Findings**: Every correlation explains the statistical method used (Pearson, Spearman, Lagged cross-correlation) and clearly caveats that correlation does not imply causation.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+

### Backend Setup
1. Open a terminal and navigate to the `backend` directory.
2. Install the required packages:
   ```bash
   pip install fastapi uvicorn duckdb pandas scipy statsmodels python-multipart icalendar requests
   ```
3. Run the backend server:
   ```bash
   python main.py
   ```
   The backend API will start at `http://127.0.0.1:8000`.

### Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the displayed local URL (usually `http://localhost:5173`) in your browser.

## Architecture Overview
- **Ingestion Layer (Connectors)**: Python plugins in `backend/connectors/`. Each parses raw files (JSON, XML, CSV) and yields standardized `events` and `metrics`.
- **Storage Layer**: A local DuckDB instance (`havn.duckdb`). DuckDB was chosen for its blazing fast analytical query capabilities on time-series data.
- **Correlation Engine**: Python module (`engine.py`) leveraging `scipy` and `statsmodels` to perform time-series alignment, cross-correlation, and changepoint detection.
- **Frontend**: A React application styled with vanilla CSS, built for rich aesthetics (glassmorphism, dark mode).

## Adding a New Connector
This project is extensible by design. To add a new connector:
1. Create a new Python file in `backend/connectors/`.
2. Inherit from `BaseConnector` defined in `base.py`.
3. Implement the `name()` and `run()` methods. The `run()` method should parse the file and return a dictionary containing lists of `events`, `metrics`, and `entities`.

## Privacy Guarantee
Havn enforces privacy in code. The backend makes zero outbound network requests for any operation involving user data files. The GitHub connector only makes authenticated requests to the official GitHub API to fetch your own commits, storing them locally. No telemetry or analytics SDKs are used.
