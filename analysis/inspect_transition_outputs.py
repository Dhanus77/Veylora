
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

files = [
    "lifecycle_transition_gaps.csv",
    "lifecycle_transition_summary.csv",
    "case_level_dataset.csv",
    "case_variant_mapping.csv",
]

for filename in files:
    path = DATA_DIR / filename
    print("\n" + "=" * 75)
    print(f"FILE: {filename}")

    if not path.exists():
        print("NOT FOUND:", path)
        continue

    df = pd.read_csv(path)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print(df.head(3).to_string(index=False))
