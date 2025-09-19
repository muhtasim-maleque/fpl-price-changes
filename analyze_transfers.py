"""
analyze_transfers.py
--------------------
- This script compares the last two transfer snapshots (logged by track_transfers.py)
- calculates transfer deltas per hour
- estimates progress towards a price rise/drop threshold
- saves the Top 10 risers/fallers into a predictions log CSV
- creates a summary snapshot of top 20 risers/fallers, overwritten each run

Note:
Calculation logic is simple at this stage:
- only compares the last two snapshots of transfer data.
- assumes a fixed threshold (default: 100k net transfers) for price changes.
- to be enhanced later, e.g. rolling averages or dynamic thresholds etc.
"""

import pandas as pd
from datetime import datetime, timezone

# Input (transfers log) and output (predictions) file paths
CSV_FILE = "fpl_transfers_log.csv"
PRED_FILE = "fpl_predictions_log.csv"
SUMMARY_FILE = "fpl_summary.csv"

# Simple assumption ~100k net transfers trigger a price change
# Will need to be refined later 
THRESHOLD = 100000  

# Load full transfer log (contains all players, multiple timestamps)
df = pd.read_csv(CSV_FILE)

# Identify two most recent snapshots
latest_times = df["timestamp"].unique()
latest_times.sort()
if len(latest_times) < 2:
    raise ValueError("Need at least two snapshots to analyze trends.")

# Compare the last 2 snapshots
t1, t2 = latest_times[-2], latest_times[-1]
print(f"Comparing snapshots: {t1} -> {t2}")

# Get player states for each snapshot
df1 = df[df["timestamp"] == t1].set_index("id")   # earlier snapshot
df2 = df[df["timestamp"] == t2].set_index("id")   # later snapshot

# Merge on player id to calculate deltas
merged = df2.join(df1, lsuffix="_new", rsuffix="_old")

# Calculate raw deltas in transfers between the two snapshots
merged["delta_in"] = merged["transfers_in_event_new"] - merged["transfers_in_event_old"]
merged["delta_out"] = merged["transfers_out_event_new"] - merged["transfers_out_event_old"]

# Net delta = transfers in - transfers out
# Positive net_delta = more transfers in (potential price rise)
# Negative net_delta = more transfers out (potential price drop)
merged["net_delta"] = merged["delta_in"] - merged["delta_out"]

# In case runs are not always 1h apart, e.g. runs may be 30 minutes apart or 3 hours apart
# Normalize deltas by time elapsed (in hours) to account for uneven run intervals
t1_dt = pd.to_datetime(t1)
t2_dt = pd.to_datetime(t2)
hours_elapsed = (t2_dt - t1_dt).total_seconds() / 3600

# Estimate rate of transfer per hour
merged["delta_in_per_hr"] = merged["delta_in"] / hours_elapsed
merged["delta_out_per_hr"] = merged["delta_out"] / hours_elapsed
merged["net_delta_per_hr"] = merged["net_delta"] / hours_elapsed

# Estimate progress towards price change thresholds
# Example: if net_delta_per_hr = 25,000 and threshold = 100,000,
# rise_progress = 0.25 (about 25% progress towards a rise if this rate continues)
merged["rise_progress"] = (merged["net_delta_per_hr"].clip(lower=0) / THRESHOLD).round(2)
merged["drop_progress"] = ((-merged["net_delta_per_hr"]).clip(lower=0) / THRESHOLD).round(2)

# Reconstruct player names and costs for reporting
merged["name"] = merged["first_name_new"] + " " + merged["second_name_new"]
merged["now_cost"] = merged["now_cost_new"]

# Select Top 10 risers and fallers
top_risers = merged.nlargest(10, "rise_progress")[[
    "name", "now_cost", "net_delta_per_hr", "rise_progress"
]]
top_droppers = merged.nlargest(10, "drop_progress")[[
    "name", "now_cost", "net_delta_per_hr", "drop_progress"
]]

# Display results in terminal
print("\n=== Top 10 Rising Candidates ===")
print(top_risers.to_string(index=False))
print("\n=== Top 10 Falling Candidates ===")
print(top_droppers.to_string(index=False))

# Add timestamp column to log predictions
ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
top_risers["timestamp"] = ts
top_risers["type"] = "riser"

top_droppers["timestamp"] = ts
top_droppers["type"] = "faller"

# Combine risers & fallers into one DataFrame
predictions = pd.concat([top_risers, top_droppers])

# Append predictions to a separate CSV log
# If the file doesn't exist, create it with headers
if not pd.io.common.file_exists(PRED_FILE):
    predictions.to_csv(PRED_FILE, index=False)
    print(f"Created {PRED_FILE} with {len(predictions)} rows.")
else:
    predictions.to_csv(PRED_FILE, mode="a", header=False, index=False)
    print(f"Appended predictions to {PRED_FILE}.")

# Create clean price change summary CSV
summary = predictions.copy()

# Combine rise/drop into one Progress column
summary["Progress"] = summary["rise_progress"].fillna(0) - summary["drop_progress"].fillna(0)

# Rename columns for clarity
summary = summary.rename(columns={
    "name": "Name",
    "now_cost": "Price",
    "net_delta_per_hr": "Hourly Change",
    "timestamp": "Timestamp"
})

# Keep only clean columns
summary = summary[["Name", "Price", "Hourly Change", "Progress", "Timestamp"]]

# Pick top 20 risers and fallers by progress
summary = summary.reindex(summary["Progress"].abs().sort_values(ascending=False).index)
summary = summary.head(20)

# Round values 
summary["Price"] = summary["Price"].round(1)          # prices like 7.5
summary["Hourly Change"] = summary["Hourly Change"].round(0)  # integer transfers per hour
summary["Progress"] = summary["Progress"].round(2)    # percentage of threshold, 2 decimals

# Save (overwrite each run)
summary.to_csv(SUMMARY_FILE, index=False)
print(f"Updated {SUMMARY_FILE} with {len(summary)} entries.")
