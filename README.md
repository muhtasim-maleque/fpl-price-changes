# fpl-price-changes

A simple tool to track FPL Price Changes

---

## Scripts

- **`track_transfers.py`**  
  - Pulls latest FPL player data (transfers in/out, ownership %, price) and appends to `fpl_transfers_log.csv` with a timestamp.
  - Initial plan is to run this regualrly to build a dataset for analysis.

- **`analyze_transfers.py`**  
  - Compares the two most recent snapshots in the transfers log and estimates hourly transfer deltas.  
  - Outputs a simple rise/fall prediction and appends results to `fpl_predictions_log.csv`.

---

## Data

- **`fpl_transfers_log.csv`** – record of raw player transfers (will grow over time)  
- **`fpl_predictions_log.csv`** – calculation results (predicted risers and fallers)

Both CSVs are included in the repo as a starting reference.
Since they will grow over time, may want to `.gitignore` them later and keep only a smaller sample version for reference.

---

## Execution

On macOS/Linux, schedule the scripts with `cron` to run automatically (hourly for now):

```bash
0 * * * * /opt/homebrew/bin/python3 /path/to/track_transfers.py >> /path/to/cron.log 2>&1
5 * * * * /opt/homebrew/bin/python3 /path/to/analyze_transfers.py >> /path/to/cron.log 2>&1
```

- First job logs player transfers at the start of every hour.
- Second job analyzes changes 5 minutes later.
- Output and errors are appended to cron.log.
---
## Future plans
- Refine calculation logic (not just compare last 2 snapshots)
- Add actual price changes to the scripts for backtesting
- Automate with GitHub Actions or GitLab CI
- Add a web dashboard or UI
