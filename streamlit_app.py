# ==========================================================
# GRAPH 1: WORLD CUP MATCH TRENDS BY YEAR
# Chart Type: Line Chart
# ==========================================================

matches_per_year = matches.groupby("Year").size().sort_index()

plt.figure(figsize=(10, 5))
plt.plot(
    matches_per_year.index,
    matches_per_year.values,
    marker="o",
    linewidth=2
)

plt.title("World Cup Match Trends by Year")
plt.xlabel("World Cup Year")
plt.ylabel("Number of Matches")
plt.grid(True, alpha=0.3)
save_chart("01_match_trends_by_year.png")


# ==========================================================
# GRAPH 2: TEAM PARTICIPATION IN WORLD CUPS
# Chart Type: Line Chart
# ==========================================================

team_participation = []

for year, group in matches.groupby("Year"):
    teams = set(group["Team 1"].dropna())
    teams.update(group["Team 2"].dropna())

    team_participation.append({
        "Year": year,
        "Teams": len(teams)
    })

participation_df = pd.DataFrame(team_participation).sort_values("Year")

plt.figure(figsize=(10, 5))
plt.plot(
    participation_df["Year"],
    participation_df["Teams"],
    marker="o",
    linewidth=2
)

plt.title("Team Participation in World Cups")
plt.xlabel("World Cup Year")
plt.ylabel("Number of Participating Teams")
plt.grid(True, alpha=0.3)
save_chart("02_team_participation.png")


# ==========================================================
# GRAPH 3: MOST FREQUENTLY PARTICIPATING TEAMS
# Chart Type: Horizontal Bar Chart
# ==========================================================

team1 = matches["Team 1"].dropna()
team2 = matches["Team 2"].dropna()

team_appearances = pd.concat(
    [team1, team2],
    ignore_index=True
).value_counts()

team_appearances = team_appearances.sort_values().tail(15)

plt.figure(figsize=(10, 7))
team_appearances.plot(kind="barh")

plt.title("Most Frequently Participating Teams")
plt.xlabel("Total Match Appearances")
plt.ylabel("Team")
save_chart("03_team_participation_ranking.png")


# ==========================================================
# GRAPH 4: TEAM-WISE AVERAGE RUNS COMPARISON
# Chart Type: Horizontal Bar Chart
# ==========================================================

team1_scores = matches[
    ["Team 1", "Total Score for Team 1"]
].rename(columns={
    "Team 1": "Team",
    "Total Score for Team 1": "Runs"
})

team2_scores = matches[
    ["Team 2", "Total Score for Team 2"]
].rename(columns={
    "Team 2": "Team",
    "Total Score for Team 2": "Runs"
})

team_scores = pd.concat(
    [team1_scores, team2_scores],
    ignore_index=True
)

team_scores["Runs"] = pd.to_numeric(
    team_scores["Runs"],
    errors="coerce"
)

average_scores = (
    team_scores.dropna(subset=["Team", "Runs"])
    .groupby("Team")["Runs"]
    .mean()
    .sort_values()
    .tail(15)
)

plt.figure(figsize=(10, 7))
average_scores.plot(kind="barh")

plt.title("Team-wise Average Runs Comparison")
plt.xlabel("Average Runs per Match")
plt.ylabel("Team")
save_chart("04_average_runs_comparison.png")


# ==========================================================
# GRAPH 5: AVERAGE TEAM SCORES ACROSS YEARS
# Chart Type: Area Chart
# ==========================================================

yearly_team_scores = pd.concat([
    matches[["Year", "Total Score for Team 1"]].rename(
        columns={"Total Score for Team 1": "Runs"}
    ),
    matches[["Year", "Total Score for Team 2"]].rename(
        columns={"Total Score for Team 2": "Runs"}
    )
], ignore_index=True)

yearly_team_scores["Runs"] = pd.to_numeric(
    yearly_team_scores["Runs"],
    errors="coerce"
)

average_runs_by_year = (
    yearly_team_scores.dropna(subset=["Year", "Runs"])
    .groupby("Year")["Runs"]
    .mean()
    .sort_index()
)

plt.figure(figsize=(10, 5))
plt.fill_between(
    average_runs_by_year.index,
    average_runs_by_year.values,
    alpha=0.4
)
plt.plot(
    average_runs_by_year.index,
    average_runs_by_year.values,
    marker="o"
)

plt.title("Average Team Scores Across Years")
plt.xlabel("World Cup Year")
plt.ylabel("Average Team Runs")
plt.grid(True, alpha=0.3)
save_chart("05_average_scores_by_year.png")


# ==========================================================
# GRAPH 6: INDIA'S MATCH OUTCOME DISTRIBUTION
# Chart Type: Pie Chart
# ==========================================================

india_matches = matches[
    (matches["Team 1"].str.upper() == "IND") |
    (matches["Team 2"].str.upper() == "IND")
].copy()

india_matches["Winner_clean"] = (
    india_matches["Winner"]
    .astype("string")
    .str.strip()
    .str.lower()
)

india_matches["Result"] = india_matches["Winner_clean"].map(
    lambda winner: (
        "Win" if winner == "india"
        else "Other / No Result"
        if pd.isna(winner) or winner in
        ["nan", "no result", "abandoned", "tied"]
        else "Loss"
    )
)

outcome_counts = india_matches["Result"].value_counts().reindex(
    ["Win", "Loss", "Other / No Result"],
    fill_value=0
)

pie_counts = outcome_counts[outcome_counts > 0]

if not pie_counts.empty:
    plt.figure(figsize=(7, 7))
    plt.pie(
        pie_counts.values,
        labels=pie_counts.index,
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("India's World Cup Match Outcome Distribution")
    save_chart("06_india_outcome_distribution.png")


# ==========================================================
# GRAPH 7: RELATIONSHIP BETWEEN TEAM SCORES
# Chart Type: Scatter Plot
# ==========================================================

score_comparison = matches[
    ["Total Score for Team 1", "Total Score for Team 2"]
].copy()

score_comparison = score_comparison.apply(
    pd.to_numeric,
    errors="coerce"
).dropna()

if not score_comparison.empty:
    plt.figure(figsize=(8, 6))

    plt.scatter(
        score_comparison["Total Score for Team 1"],
        score_comparison["Total Score for Team 2"],
        alpha=0.6
    )

    plt.title("Relationship Between Team 1 and Team 2 Scores")
    plt.xlabel("Team 1 Runs")
    plt.ylabel("Team 2 Runs")
    plt.grid(True, alpha=0.3)

    save_chart("07_team_score_relationship.png")


# ==========================================================
# GRAPH 8: DISTRIBUTION OF WORLD CUP TEAM SCORES
# Chart Type: Histogram
# ==========================================================

all_team_runs = pd.concat(
    [
        matches["Total Score for Team 1"],
        matches["Total Score for Team 2"]
    ],
    ignore_index=True
)

all_team_runs = pd.to_numeric(
    all_team_runs,
    errors="coerce"
).dropna()

if not all_team_runs.empty:
    plt.figure(figsize=(9, 5))

    plt.hist(
        all_team_runs,
        bins=15,
        edgecolor="black"
    )

    plt.title("Distribution of World Cup Team Scores")
    plt.xlabel("Total Runs")
    plt.ylabel("Frequency")

    save_chart("08_team_score_distribution.png")


# ==========================================================
# GRAPH 9: COMPARISON OF TEAM SCORE DISTRIBUTIONS
# Chart Type: Violin Plot
# ==========================================================

team1_runs = pd.to_numeric(
    matches["Total Score for Team 1"],
    errors="coerce"
).dropna()

team2_runs = pd.to_numeric(
    matches["Total Score for Team 2"],
    errors="coerce"
).dropna()

if not team1_runs.empty and not team2_runs.empty:
    plt.figure(figsize=(8, 6))

    plt.violinplot(
        [team1_runs.values, team2_runs.values],
        showmeans=True,
        showmedians=True
    )

    plt.xticks([1, 2], ["Team 1", "Team 2"])
    plt.title("Comparison of Team Score Distributions")
    plt.xlabel("Team")
    plt.ylabel("Total Runs")

    save_chart("09_team_score_violin_plot.png")


print("\nAll nine updated charts have been generated.")
print("Charts saved in:", OUTPUT_DIR)