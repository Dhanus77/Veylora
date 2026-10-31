
from pathlib import Path
import pm4py
import pandas as pd

# Locate the project and dataset
PROJECT_DIR = Path(__file__).resolve().parent
LOG_PATH = PROJECT_DIR / "data" / "raw" / "sampled-log.xml"

print("=" * 60)
print("BPI 2017 EVENT LOG INSPECTION")
print("=" * 60)

if not LOG_PATH.exists():
    print(f"ERROR: Dataset not found:\n{LOG_PATH}")
    print("Check the filename and folder location.")
    raise SystemExit(1)

print(f"\nDataset: {LOG_PATH.name}")
print(f"File size: {LOG_PATH.stat().st_size / (1024 * 1024):.2f} MB")
print("\nReading event log. This may take a little time...")

# Read XES/XML event log
log = pm4py.read_xes(str(LOG_PATH))
df = pm4py.convert_to_dataframe(log)

print("\n--- BASIC STATISTICS ---")
print(f"Total events: {len(df):,}")

if "case:concept:name" in df.columns:
    print(f"Unique cases: {df['case:concept:name'].nunique():,}")
else:
    print("Case ID column not found under the expected name.")

print("\n--- COLUMNS / ATTRIBUTES ---")
for column in df.columns:
    print(f"- {column}")

print("\n--- SAMPLE RECORDS ---")
print(df.head(5).to_string(index=False))

if "concept:name" in df.columns:
    print("\n--- MOST COMMON ACTIVITIES ---")
    print(df["concept:name"].value_counts().head(15).to_string())

if "time:timestamp" in df.columns:
    print("\n--- TIMESTAMP RANGE ---")
    timestamps = pd.to_datetime(df["time:timestamp"], errors="coerce")
    print(f"Earliest: {timestamps.min()}")
    print(f"Latest:   {timestamps.max()}")
    print(f"Missing timestamps: {timestamps.isna().sum():,}")

print("\n--- MISSING VALUES ---")
print(df.isna().sum().to_string())

print("\nInspection complete.")
