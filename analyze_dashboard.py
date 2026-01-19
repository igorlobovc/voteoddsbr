import pandas as pd

df = pd.read_csv("mvp/exports/dashboard_summary.csv")

print("\n✅ Total votes by office:")
print(df.groupby("office")["total_votes"].sum())

print("\n✅ Votes by state and round:")
print(df.groupby(["state", "round"])["total_votes"].sum())

print("\n✅ Top 5 races by total votes:")
print(df.sort_values("total_votes", ascending=False).head(5))

# Aggregate votes by office, state, and round
summary = (
    df.groupby(["office", "state", "round"])
    ["total_votes"]
    .sum()
    .reset_index()
    .sort_values("total_votes", ascending=False)
)

# Save the summary for dashboard tools
summary.to_csv("mvp/exports/dashboard_by_office_state_round.csv", index=False)

# Compute total votes per round and merge for percentage share
total_by_round = df.groupby("round")["total_votes"].sum().rename("round_total")
summary = summary.merge(total_by_round, on="round", how="left")
summary["vote_share_pct"] = (summary["total_votes"] / summary["round_total"]) * 100

# Save enriched summary
summary.to_csv("mvp/exports/dashboard_by_office_state_round_with_share.csv", index=False)

print("\n✅ Exported enriched summary with vote shares → mvp/exports/dashboard_by_office_state_round_with_share.csv")
print(summary.head(10))