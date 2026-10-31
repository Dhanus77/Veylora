
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.discrete.conditional_models import ConditionalLogit


ROOT = Path(r"D:\intern\Veylora")
INPUT = ROOT / "data" / "processed" / "offer_level_dataset.csv"

df = pd.read_csv(INPUT)

df = df[df["outcome"].isin(["accepted", "cancelled"])].copy()
df["accepted_binary"] = (df["outcome"] == "accepted").astype(int)

df["MonthlyCost"] = pd.to_numeric(df["MonthlyCost"], errors="coerce")
df["offer_sequence"] = pd.to_numeric(
    df["offer_sequence"], errors="coerce"
)

df = df.dropna(
    subset=["application_id", "MonthlyCost",
            "offer_sequence", "accepted_binary"]
)

# Keep applications with both outcomes and cost variation.
stats = df.groupby("application_id").agg(
    outcome_count=("accepted_binary", "nunique"),
    cost_count=("MonthlyCost", "nunique"),
)

valid_ids = stats[
    (stats["outcome_count"] == 2) &
    (stats["cost_count"] > 1)
].index

d = df[df["application_id"].isin(valid_ids)].copy()

# Cost effect per 100 monetary units.
d["MonthlyCost_per_100"] = d["MonthlyCost"] / 100.0

# Use sequence 1 as the reference category.
# Combine sparse later sequences into sequence 4+.
d["sequence_group"] = np.where(
    d["offer_sequence"] >= 4,
    "4+",
    d["offer_sequence"].astype(int).astype(str)
)

sequence_dummies = pd.get_dummies(
    d["sequence_group"],
    prefix="sequence",
    drop_first=True,
    dtype=float,
)

X = pd.concat(
    [d[["MonthlyCost_per_100"]], sequence_dummies],
    axis=1,
)

y = d["accepted_binary"]
groups = d["application_id"]

print("SEQUENCE-ADJUSTED CONDITIONAL LOGIT")
print("-----------------------------------")
print("Applications:", d["application_id"].nunique())
print("Offers:", len(d))
print("Features:", list(X.columns))

model = ConditionalLogit(
    endog=y,
    exog=X,
    groups=groups,
)

result = model.fit(
    method="bfgs",
    maxiter=1000,
    disp=False,
)

print("\nMODEL SUMMARY")
print(result.summary())

coef = result.params["MonthlyCost_per_100"]
p_value = result.pvalues["MonthlyCost_per_100"]
ci = result.conf_int().loc["MonthlyCost_per_100"]

print("\nMONTHLY COST RESULT")
print("-----------------------------------")
print("Coefficient:", round(coef, 6))
print("P-value:", round(p_value, 6))
print("Odds ratio:", round(np.exp(coef), 4))
print(
    "95% odds-ratio CI:",
    (round(np.exp(ci.iloc[0]), 4),
     round(np.exp(ci.iloc[1]), 4))
)

print("\nLIMITATIONS")
print(
    "This is an observational association among resolved offers. "
    "Sequence adjustment does not remove all time-varying or "
    "offer-level confounding and does not establish causality."
)
