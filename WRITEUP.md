# Havn: Design & Architecture Writeup

## Overview
Havn was conceived as a privacy-first, local-only personal data analysis platform. The goal was to build a system that acts as a "second brain" for your quantitative life—merging disjointed datasets (Spotify, GitHub, Google Takeout, Apple Health) to find non-obvious correlations without ever sacrificing privacy.

## Architectural Decisions

### Storage: DuckDB over SQLite
While SQLite is the traditional choice for local-first apps, we chose **DuckDB**. The core querying workload of Havn involves scanning time-series data, aggregating by day/week, and performing statistical comparisons across wide tables. DuckDB is a columnar OLAP database built exactly for this purpose, drastically outperforming SQLite on time-series aggregations and window functions.

### The Correlation Engine
The engine goes beyond a simple Pearson correlation (which assumes linear relationships). 
- **Spearman Rank Correlation**: Added to capture monotonic but non-linear relationships robustly against outliers (e.g., occasional days with 10x normal commits).
- **Lagged Cross-Correlation**: Implemented via `statsmodels`. Many life events have delayed effects (e.g., poor sleep today affects focus *tomorrow*). We test time shifts up to 14 days in both directions to see if one metric reliably predicts another.
- **Changepoint Detection**: Implemented a simultaneous rolling mean shift algorithm. Instead of just finding static correlations, we look for days where the trend in *both* metrics shifted dramatically, signaling a potential lifestyle change or external event.

### Privacy & Provenance
Privacy is enforced architecturally. The backend is a standard FastAPI app, but it makes zero outbound HTTP requests for data analysis. The only exception is the GitHub connector, which uses a user-provided PAT to fetch their own data directly from the official API. 

**Provenance**: Every ingested record gets a deterministic UUID (`uuid5`) based on its source, original timestamp, and properties. This guarantees that if you re-ingest an export, we won't duplicate data, and we can always trace an insight back to the exact JSON/CSV row it came from.

### Caveats & Non-Technical Explanations
A major risk with quantitative self-analysis is false confidence. If we test 100 pairs of variables, 5 will show a correlation just by random chance (p < 0.05). To mitigate this:
1. We enforce a minimum threshold of overlapping data points.
2. The UI explicitly labels every insight with a caveat: *"Correlation does not imply causation."*
3. We present the `p-value` and `r-value` plainly, explaining what they mean in context rather than assuming statistical literacy.

## What was Descoped
- **Complex NLP over text exports (like emails or chat logs)**: Analyzing text requires either cloud LLM APIs (violating the local-first rule) or heavy local models (creating a huge hardware barrier). We restricted email ingestion to metadata (timestamps) to keep the app lightweight and strictly local.
- **Real-time Sync**: The platform relies on manual point-in-time export dumps. Automated background sync would require storing OAuth tokens locally and managing background daemons, which significantly complicates the installation footprint.

## Worked Example: Synthetic Correlation
During end-to-end testing, we generated a synthetic dataset simulating 30 days of life. We planted a hidden rule: on days where the user was in "Focus Mode", they listened to ~15 tracks of "Focus Beats" on Spotify and made ~10 commits on GitHub. On normal days, they listened to ~2 tracks and made ~2 commits.

When Havn processed this data, the Insights Feed automatically surfaced this correlation without any prompt:
- **Finding**: `spotify.listen` vs `github.commit`
- **Result**: `r = 0.82` (Spearman)
- **Explanation**: A strong statistically significant relationship was found, indicating that listening to Focus Beats heavily correlates with high GitHub activity.
