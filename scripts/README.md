# Scripts

Utility scripts live here as the project grows.

## Available Scripts

- `seed_synthetic_production.py` - load `data/samples/synthetic_mixed_production.json` through the backend ingestion pipeline.
- `run_synthetic_evaluation.py` - seed the synthetic production and run retrieval plus answer benchmarks.

Run from the repository root:

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-phase-7
backend\.venv\Scripts\python.exe scripts\seed_synthetic_production.py
backend\.venv\Scripts\python.exe scripts\run_synthetic_evaluation.py
```

## Planned Scripts

- Run ingestion over a local folder.
- Rebuild embeddings.
