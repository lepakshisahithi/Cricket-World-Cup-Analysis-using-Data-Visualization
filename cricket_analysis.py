"""
Historical Performance Analysis of the Indian Cricket Team in ICC World Cups
Dataset: world_cup_score.csv

Run:
    python cricket_analysis.py

The program creates charts in the output_graphs folder.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "world_cup_score.csv"
OUTPUT_DIR = PROJECT_DIR / "output_graphs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load the dataset
df = pd.read_csv(DATA_FILE)

# Clean text columns
for column in ["Winner", "Team 1", "Team 2", "Match Detail"]:
    if column in df.columns:
        df[column] = df[column].astype("string").str.strip()

# The CSV has multiple rows per match (over-by-over records).
# Keep one record for each match using the available match identifiers.
match_keys = [c for c in ["Year", "Match Number", "Match Detail"] if c in df.columns]
matches = df.drop_duplicates(subset=match_keys, keep="first").copy()

# Convert score fields to numeric values
score_columns = [
    "Total Score for Team 1",
    "Total Score for Team 2",
]
for column in score_columns:
    matches[column] = pd.to_numeric(matches[column], errors="coerce")

print("Dataset loaded successfully.")
print(f"Over-level rows: {len(df):,}")
print(f"Unique match records used: {len(matches):,}")
print(f"Years available: {sorted(matches['Year'].dropna().unique().tolist())}")


def save_chart(filename):
    """Save the current chart and show it."""
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()


# GRAPH 1: Number of matches by year
matches_per_year = matches.groupby("Year").size().sort_index()
plt.figure(figsize=(9, 5))
matches_per_year.plot(kind="bar")
plt.title("Number of World Cup Matches by Year")
plt.xlabel("Year")
plt.ylabel("Number of Matches")
plt.xticks(rotation=0)
save_chart("01_matches_by_year.png")


# Find matches involving India. The dataset uses team abbreviations such as IND.
india_matches = matches[
    (matches["Team 1"].str.upper() == "IND") |
    (matches["Team 2"].str.upper() == "IND")
].copy()

# GRAPH 2: India's match outcomes
# Winner values in the dataset are full team names (for example, India).
india_matches["Winner_clean"] = india_matches["Winner"].str.strip().str.lower()
india_matches["Result"] = india_matches["Winner_clean"].map(
    lambda winner: "Win" if winner == "india" else (
        "Other / no result" if pd.isna(winner) or winner in
        ["nan", "no result", "abandoned", "tied"] else "Loss"
    )
)
outcome_counts = india_matches["Result"].value_counts().reindex(
    ["Win", "Loss", "Other / no result"], fill_value=0
)
plt.figure(figsize=(8, 5))
outcome_counts.plot(kind="bar")
plt.title("India's World Cup Match Outcomes")
plt.xlabel("Match Result")
plt.ylabel("Number of Matches")
plt.xticks(rotation=0)
save_chart("02_india_wins_losses.png")


# GRAPH 3: India's wins by year
india_wins = india_matches[india_matches["Winner_clean"] == "india"]
wins_by_year = india_wins.groupby("Year").size().sort_index()
plt.figure(figsize=(9, 5))
wins_by_year.plot(kind="bar")
plt.title("India's World Cup Wins by Year")
plt.xlabel("Year")
plt.ylabel("Number of Wins")
plt.xticks(rotation=0)
save_chart("03_india_wins_by_year.png")


# GRAPH 4: Top 10 teams by average total team score per match
team1_scores = matches[["Team 1", "Total Score for Team 1"]].rename(
    columns={"Team 1": "Team", "Total Score for Team 1": "Runs"}
)
team2_scores = matches[["Team 2", "Total Score for Team 2"]].rename(
    columns={"Team 2": "Team", "Total Score for Team 2": "Runs"}
)
team_scores = pd.concat([team1_scores, team2_scores], ignore_index=True)
team_scores["Runs"] = pd.to_numeric(team_scores["Runs"], errors="coerce")
average_scores = (
    team_scores.dropna(subset=["Team", "Runs"])
    .groupby("Team")["Runs"].mean()
    .sort_values(ascending=False)
    .head(10)
)
plt.figure(figsize=(10, 6))
average_scores.sort_values().plot(kind="barh")
plt.title("Top 10 Teams by Average Runs per Match")
plt.xlabel("Average Runs")
plt.ylabel("Team")
save_chart("04_top_teams_average_runs.png")


# GRAPH 5: India's average runs by year
def india_score(row):
    if str(row["Team 1"]).strip().upper() == "IND":
        return row["Total Score for Team 1"]
    if str(row["Team 2"]).strip().upper() == "IND":
        return row["Total Score for Team 2"]
    return float("nan")

india_matches["India Runs"] = india_matches.apply(india_score, axis=1)
india_matches["India Runs"] = pd.to_numeric(india_matches["India Runs"], errors="coerce")
average_india_runs = india_matches.groupby("Year")["India Runs"].mean().dropna().sort_index()
plt.figure(figsize=(9, 5))
average_india_runs.plot(kind="line", marker="o")
plt.title("India's Average Runs per Match by Year")
plt.xlabel("Year")
plt.ylabel("Average Runs")
plt.grid(True)
save_chart("05_india_average_runs_by_year.png")



# GRAPH 6: Pie chart of India's match outcomes
pie_counts = outcome_counts[outcome_counts > 0]
if not pie_counts.empty:
    plt.figure(figsize=(7, 7))
    pie_counts.plot(kind="pie", autopct="%1.1f%%", startangle=90)
    plt.title("India's World Cup Match Outcomes (Share)")
    plt.ylabel("")
    save_chart("06_india_outcomes_pie.png")


# GRAPH 7: Scatter plot comparing the two teams' total scores
score_comparison = matches[
    ["Total Score for Team 1", "Total Score for Team 2"]
].dropna()
if not score_comparison.empty:
    plt.figure(figsize=(7, 5))
    plt.scatter(
        score_comparison["Total Score for Team 1"],
        score_comparison["Total Score for Team 2"],
        alpha=0.6
    )
    plt.title("Team 1 Score vs Team 2 Score")
    plt.xlabel("Team 1 Total Runs")
    plt.ylabel("Team 2 Total Runs")
    plt.grid(True, alpha=0.3)
    save_chart("07_team_scores_scatter.png")


# GRAPH 8: Histogram showing the distribution of team totals
all_team_runs = pd.concat(
    [
        matches["Total Score for Team 1"],
        matches["Total Score for Team 2"]
    ],
    ignore_index=True
).dropna()
if not all_team_runs.empty:
    plt.figure(figsize=(8, 5))
    plt.hist(all_team_runs, bins=15, edgecolor="black")
    plt.title("Distribution of Team Scores")
    plt.xlabel("Total Runs")
    plt.ylabel("Number of Team Innings")
    save_chart("08_team_score_histogram.png")


# GRAPH 9: Box plot comparing score distributions for both teams
if not score_comparison.empty:
    plt.figure(figsize=(7, 5))
    plt.boxplot(
        [
            score_comparison["Total Score for Team 1"],
            score_comparison["Total Score for Team 2"]
        ],
        tick_labels=["Team 1", "Team 2"]
    )
    plt.title("Distribution of Scores: Team 1 vs Team 2")
    plt.xlabel("Team")
    plt.ylabel("Total Runs")
    save_chart("09_team_scores_boxplot.png")


# Save useful summary tables as CSV files
matches_per_year.rename("Number of Matches").to_csv(OUTPUT_DIR / "matches_by_year.csv")
outcome_counts.rename("Number of Matches").to_csv(OUTPUT_DIR / "india_match_outcomes.csv")
wins_by_year.rename("India Wins").to_csv(OUTPUT_DIR / "india_wins_by_year.csv")
average_scores.rename("Average Runs").to_csv(OUTPUT_DIR / "team_average_runs.csv")
average_india_runs.rename("Average India Runs").to_csv(OUTPUT_DIR / "india_average_runs_by_year.csv")

print("\nIndia's match outcomes:")
print(outcome_counts)
print("\nIndia's wins by year:")
print(wins_by_year)
print("\nCharts and summary tables saved in:", OUTPUT_DIR)
print("Note: Verify tournament formats and match records before interpreting all years as the same World Cup format.")
