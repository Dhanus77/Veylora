
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.discrete.conditional_models import ConditionalLogit

ROOT = Path(r"D:\intern\Veylora")
INPUT = ROOT / "data" / "processed" / "offer_level_dataset.csv"
OUTPUT = ROOT / "data" / "processed" / "three_attribute_model.csv"

df = pd.read_csv(INPUT)

df = df[df["outcome"].isin(["accepted", "cancelled"])].copy()
df["accepted_binary"] = (df["outcome"] == "accepted").astype(int)

attributes = [
    "MonthlyCost",
    "OfferedAmount",
    "NumberOfTerms",
]

for col in attributes + ["offer_sequence"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["application_id", *attributes,
            "offer_sequence", "accepted_binary"]
)

stats = df.groupby("application_id").agg(
    outcomes=("accepted_binary", "nunique"),
    **{
        f"{col}_count": (col, "nunique")
        for col in attributes
    },
)

valid = stats[
    (stats["outcomes"] == 2)
    & (stats["MonthlyCost_count"] > 1)
    & (stats["OfferedAmount_count"] > 1)
    & (stats["NumberOfTerms_count"] > 1)
].index

d = df[df["application_id"].isin(valid)].copy()

print("COMMON SAMPLE")
print("Applications:", d["application_id"].nunique())
print("Offers:", len(d))

for col in attributes:
    d[f"{col}_per_100"] = d[col] / 100.0

d["sequence_group"] = np.where(
    d["offer_sequence"] >= 4,
    "4+",
    d["offer_sequence"].astype(int).astype(str),
)

sequence_dummies = pd.get_dummies(
    d["sequence_group"],
    prefix="sequence",
    drop_first=True,
    dtype=float,
)

feature_columns = [
    "MonthlyCost_per_100",
    "OfferedAmount_per_100",
    "NumberOfTerms_per_100",
]

X = pd.concat(
    [d[feature_columns], sequence_dummies],
    axis=1,
)

model = ConditionalLogit(
    endog=d["accepted_binary"],
    exog=X,
    groups=d["application_id"],
)

result = model.fit(
    method="bfgs",
    maxiter=2000,
    disp=False,
    full_output=True,
)

print("\nTHREE-ATTRIBUTE CONDITIONAL LOGIT")
print(result.summary())

rows = []

for col in feature_columns:
    coef = result.params[col]
    ci = result.conf_int().loc[col]

    rows.append({
        "attribute": col,
        "coefficient": coef,
        "odds_ratio": np.exp(coef),
        "ci_lower": np.exp(ci.iloc[0]),
        "ci_upper": np.exp(ci.iloc[1]),
        "p_value": result.pvalues[col],
    })

comparison = pd.DataFrame(rows)
comparison.to_csv(OUTPUT, index=False)

print("\nATTRIBUTE RESULTS")
print(comparison.round(5).to_string(index=False))
print("\nSaved:", OUTPUT)
print(
    "\nReminder: observational association only; "
    "this model does not identify causal effects."
)
