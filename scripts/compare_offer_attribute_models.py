
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.discrete.conditional_models import ConditionalLogit

ROOT = Path(r"D:\intern\Veylora")
INPUT = ROOT / "data" / "processed" / "offer_level_dataset.csv"
OUTPUT = ROOT / "data" / "processed" / "offer_attribute_model_comparison.csv"

df = pd.read_csv(INPUT)

df = df[df["outcome"].isin(["accepted", "cancelled"])].copy()
df["accepted_binary"] = (df["outcome"] == "accepted").astype(int)

attributes = [
    "MonthlyCost",
    "OfferedAmount",
    "FirstWithdrawalAmount",
]

results = []

for attribute in attributes:
    d = df.copy()

    d[attribute] = pd.to_numeric(d[attribute], errors="coerce")
    d["offer_sequence"] = pd.to_numeric(
        d["offer_sequence"], errors="coerce"
    )

    d = d.dropna(
        subset=[
            "application_id",
            attribute,
            "offer_sequence",
            "accepted_binary",
        ]
    )

    stats = d.groupby("application_id").agg(
        outcome_count=("accepted_binary", "nunique"),
        attribute_count=(attribute, "nunique"),
    )

    valid_ids = stats[
        (stats["outcome_count"] == 2)
        & (stats["attribute_count"] > 1)
    ].index

    d = d[d["application_id"].isin(valid_ids)].copy()

    # Scale each variable by 100 units for interpretability.
    feature = f"{attribute}_per_100"
    d[feature] = d[attribute] / 100.0

    # Use sequence 1 as reference and combine sparse later groups.
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

    X = pd.concat(
        [d[[feature]], sequence_dummies],
        axis=1,
    )

    try:
        model = ConditionalLogit(
            endog=d["accepted_binary"],
            exog=X,
            groups=d["application_id"],
        )

        fitted = model.fit(
            method="bfgs",
            maxiter=1000,
            disp=False,
        )

        coef = fitted.params[feature]
        ci = fitted.conf_int().loc[feature]

        results.append({
            "attribute": attribute,
            "applications": d["application_id"].nunique(),
            "offers": len(d),
            "coefficient_per_100": coef,
            "odds_ratio_per_100": np.exp(coef),
            "ci_lower": np.exp(ci.iloc[0]),
            "ci_upper": np.exp(ci.iloc[1]),
            "p_value": fitted.pvalues[feature],
            "converged": fitted.mle_retvals.get("converged", None)
            if hasattr(fitted, "mle_retvals") else None,
        })

        print(f"\nCompleted: {attribute}")

    except Exception as exc:
        print(f"\nFailed: {attribute}: {exc}")

comparison = pd.DataFrame(results)

if not comparison.empty:
    comparison.to_csv(OUTPUT, index=False)

    print("\nATTRIBUTE MODEL COMPARISON")
    print("-----------------------------------")
    print(comparison.round(5).to_string(index=False))
    print("\nSaved:", OUTPUT)
else:
    print("No models completed successfully.")
