"""
track_transfers.py
------------------
Pull latest FPL player data and append to CSV with timestamp.
Plan is to run this hourly to build a history of transfers for price change analysis.
"""

import requests
import pandas as pd
from datetime import datetime, timezone
import os

BASE = "https://fantasy.premierleague.com/api/"
CSV_FILE = "fpl_transfers_log.csv"

# Fetch player data from API
bootstrap = requests.get(BASE + "bootstrap-static/").json()
players = pd.DataFrame(bootstrap['elements'])

# Keep only fields relevant to transfer/price tracking
players = players[[
    "id", "first_name", "second_name", "now_cost",
    "transfers_in_event", "transfers_out_event", "selected_by_percent"
]]

# Add timestamp in UTC 
players["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# Convert now_cost from tens of millions to actual £m
players["now_cost"] = players["now_cost"] / 10

# Reorder columns
players = players[[
    "timestamp", "id", "first_name", "second_name", "now_cost",
    "transfers_in_event", "transfers_out_event", "selected_by_percent"
]]

# Append to log or create file if it doesn't exist
if not os.path.isfile(CSV_FILE):
    players.to_csv(CSV_FILE, index=False)
    print(f"Created {CSV_FILE} with {len(players)} players.")
else:
    players.to_csv(CSV_FILE, mode="a", header=False, index=False)
    print(f"Appended snapshot to {CSV_FILE}.")