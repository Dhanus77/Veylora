
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.discrete.conditional_models import ConditionalLogit

ROOT = Path(r"D:\intern\Veylora")
INPUT = ROOT / "data" / "processed" / "offer_level_dataset.csv"
OUTPUT = ROOT / "data" / "processed" / "cost_amount_model_comparison.csv"

df = pd.read_csv(INPUT)

df = df[df["outcome"].isin(["accepted", "cancelled"])].copy()

for col in ["MonthlyCost", "OfferedAmount", "offer_sequence"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["accepted_binary"] = (df["outcome"] == "accepted").astype(int)

df = df.dropna(
    subset=[
        "application_id",
        "MonthlyCost",
        "OfferedAmount",
        "offer_sequence",
    ]
)

# Select applications with both outcomes and variation
# in both attributes.
stats = df.groupby("application_id").agg(
    outcome_count=("accepted_binary", "nunique"),
    cost_count=("MonthlyCost", "nunique"),
    amount_count=("OfferedAmount", "nunique"),
)

valid_ids = stats[
    (stats["outcome_count"] == 2)
    & (stats["cost_count"] > 1)
    & (stats["amount_count"] > 1)
].index

d = df[df["application_id"].isin(valid_ids)].copy()

d["MonthlyCost_per_100"] = d["MonthlyCost"] / 100
d["OfferedAmount_per_100"] = d["OfferedAmount"] / 100

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

print("COMMON SAMPLE")
print("------------------------------")
print("Applications:", d["application_id"].nunique())
print("Offers:", len(d))

specifications = {
    "Model A: MonthlyCost + sequence": [
        "MonthlyCost_per_100"
    ],
    "Model B: MonthlyCost + OfferedAmount + sequence": [
        "MonthlyCost_per_100",
        "OfferedAmount_per_100",
    ],
}

results = []

for model_name, attributes in specifications.items():
    X = pd.concat(
        [d[attributes], sequence_dummies],
        axis=1,
    )

    model = ConditionalLogit(
        endog=d["accepted_binary"],
        exog=X,
        groups=d["application_id"],
    )

    fitted = model.fit(
        method="bfgs",
        maxiter=2000,
        disp=False,
        full_output=True,
    )

    print(f"\n{model_name}")
    print("------------------------------")
    print(fitted.summary())

    for attribute in attributes:
        coef = fitted.params[attribute]
        ci = fitted.conf_int().loc[attribute]

        results.append({
            "model": model_name,
            "attribute": attribute,
            "applications": d["application_id"].nunique(),
            "offers": len(d),
            "coefficient": coef,
            "odds_ratio": np.exp(coef),
            "ci_lower": np.exp(ci.iloc[0]),
            "ci_upper": np.exp(ci.iloc[1]),
            "p_value": fitted.pvalues[attribute],
        })

comparison = pd.DataFrame(results)
comparison.to_csv(OUTPUT, index=False)

print("\nCOMPARISON")
print("------------------------------")
print(comparison.round(5).to_string(index=False))
print("\nSaved:", OUTPUT)
