
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"

wait_path = DATA_DIR / "activity_wait_statistics.csv"
activity_path = DATA_DIR / "activity_counts.csv"
transition_path = DATA_DIR / "activity_transitions.csv"

for path in [wait_path, activity_path, transition_path]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

waits = pd.read_csv(wait_path)
activities = pd.read_csv(activity_path)
transitions = pd.read_csv(transition_path)

print("\n=== WAIT STATISTICS: AVAILABLE COLUMNS ===")
print(waits.columns.tolist())
print(waits.head(3).to_string(index=False))

print("\n=== ACTIVITY COUNTS: AVAILABLE COLUMNS ===")
print(activities.columns.tolist())
print(activities.head(5).to_string(index=False))

print("\n=== MOST FREQUENT TRANSITIONS ===")
print(transitions.head(10).to_string(index=False))
