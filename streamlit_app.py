import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Cricket World Cup Analysis",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Cricket World Cup Analysis")
st.subheader(
    "Interactive Data Visualization and Team Performance Dashboard"
)

st.write(
    "Explore team performance, match outcomes, win percentages, "
    "and scoring patterns across Cricket World Cup years."
)

# ==========================================================
# 2. LOAD DATASET
# ==========================================================
@st.cache_data
def load_data():
    return pd.read_csv("world_cup_score.csv")


try:
    df = load_data().copy()
except FileNotFoundError:
    st.error(
        "Dataset not found. Keep world_cup_score.csv "
        "in the same GitHub repository as this app file."
    )
    st.stop()

df.columns = df.columns.astype(str).str.strip()
df = df.dropna(how="all")

# ==========================================================
# 3. CHECK REQUIRED COLUMNS
# ==========================================================
required_columns = [
    "Year",
    "Match Number",
    "Winner",
    "Team 1",
    "Team 2",
    "Total Score for Team 1",
    "Total Score for Team 2"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "Required columns are missing: "
        + ", ".join(missing_columns)
    )
    st.write("Available columns:", df.columns.tolist())
    st.stop()

# ==========================================================
# 4. DATA CLEANING
# ==========================================================
for col in ["Winner", "Team 1", "Team 2"]:
    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

for col in [
    "Total Score for Team 1",
    "Total Score for Team 2"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["Year", "Match Number", "Team 1", "Team 2"]
)

# Assumption: Year + Match Number uniquely identifies a match.
matches = df.drop_duplicates(
    subset=["Year", "Match Number"],
    keep="first"
).copy()

matches["Year"] = matches["Year"].astype(int)

if matches.empty:
    st.error("No valid match records were found.")
    st.stop()

# ==========================================================
# 5. HELPER FUNCTIONS
# ==========================================================
def clean_text(value):
    """Normalize text for reliable comparisons."""
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def is_no_result(value):
    """Identify matches without a normal winning team."""
    return clean_text(value) in {
        "", "nan", "none", "no result", "no-result",
        "abandoned", "tied", "tie", "draw"
    }


def get_outcome(row):
    """Classify a match using its winner and participating teams."""
    winner = clean_text(row["Winner"])
    team1 = clean_text(row["Team 1"])
    team2 = clean_text(row["Team 2"])

    if is_no_result(winner):
        return "Other / No Result"

    if winner == team1 or winner == team2:
        return "Decided"

    return "Other / No Result"


def calculate_team_statistics(data, teams):
    """
    Calculate statistics for selected teams only.
    Win Percentage = Wins / Decided Matches * 100.
    """
    rows = []

    for team in teams:
        team_normalized = clean_text(team)

        team_matches = data[
            data["Team 1"].apply(clean_text).eq(team_normalized)
            | data["Team 2"].apply(clean_text).eq(team_normalized)
        ]

        appearances = len(team_matches)
        decided_matches = team_matches[
            team_matches["Outcome"] == "Decided"
        ]

        wins = sum(
            clean_text(winner) == team_normalized
            for winner in decided_matches["Winner"]
        )

        losses = max(len(decided_matches) - wins, 0)

        win_percentage = (
            wins / len(decided_matches) * 100
            if len(decided_matches) > 0
            else 0
        )

        rows.append({
            "Team": team,
            "Matches Played": appearances,
            "Decided Matches": len(decided_matches),
            "Wins": wins,
            "Losses": losses,
            "Win Percentage": round(win_percentage, 2)
        })

    return pd.DataFrame(
        rows,
        columns=[
            "Team", "Matches Played", "Decided Matches",
            "Wins", "Losses", "Win Percentage"
        ]
    )


def create_bar_chart(
    data,
    x_column,
    y_column,
    title,
    x_label,
    y_label,
    figsize=(11, 5),
    ylim=None
):
    """Create a consistent Matplotlib bar chart."""
    if data.empty:
        st.info("No data is available for this visualization.")
        return

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(data[x_column].astype(str), data[y_column])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    if ylim is not None:
        ax.set_ylim(ylim)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ==========================================================
# 6. SIDEBAR FILTERS
# ==========================================================
st.sidebar.title("🔎 Dashboard Controls")

all_teams = sorted(
    set(matches["Team 1"].dropna().astype(str))
    | set(matches["Team 2"].dropna().astype(str))
)
all_years = sorted(matches["Year"].unique().tolist())

selected_teams = st.sidebar.multiselect(
    "Select Team(s)",
    options=all_teams,
    default=all_teams,
    help=(
        "Select teams to analyse. Matches involving any selected "
        "team will be included; team-specific charts show selected teams."
    )
)

selected_years = st.sidebar.multiselect(
    "Select Year(s)",
    options=all_years,
    default=all_years,
    help="Select the World Cup years to analyse."
)

selected_outcome = st.sidebar.selectbox(
    "Select Match Outcome",
    ["All Outcomes", "Decided", "Other / No Result"]
)

visualization_options = [
    "Matches Played by Each Team",
    "Team-wise Win Percentage",
    "Wins by Team in a Specific Year",
    "Year-wise Match Outcomes",
    "Team-wise Average Runs per Match",
    "India's Win Percentage by Year",
    "Top 10 Teams by Average Runs",
    "Wins vs. Losses by Team",
    "Highest Team Scores",
    "Team Score Comparison",
    "Toss Winners vs. Match Winners",
    "Team Score Distribution - Histogram",
    "Team Score Distribution - Box Plot",
    "View Filtered Dataset"
]

selected_visualization = st.sidebar.selectbox(
    "Select Visualization",
    visualization_options
)

if st.sidebar.button("🔄 Reset Filters"):
    st.rerun()

# ==========================================================
# 7. APPLY FILTERS CONSISTENTLY
# ==========================================================
# Empty team/year selections mean "all".
effective_teams = selected_teams if selected_teams else all_teams
effective_years = selected_years if selected_years else all_years

# Include matches involving ANY selected team.
team_mask = (
    matches["Team 1"].isin(effective_teams)
    | matches["Team 2"].isin(effective_teams)
)
year_mask = matches["Year"].isin(effective_years)

filtered_df = matches[team_mask & year_mask].copy()
filtered_df["Outcome"] = filtered_df.apply(get_outcome, axis=1)

if selected_outcome != "All Outcomes":
    filtered_df = filtered_df[
        filtered_df["Outcome"] == selected_outcome
    ].copy()

if filtered_df.empty:
    st.warning(
        "No matches match your selected filters. "
        "Try selecting different teams, years, or outcomes."
    )
    st.info("Change the sidebar filters to display the dashboard again.")
    st.stop()

# ==========================================================
# 8. DASHBOARD OVERVIEW
# ==========================================================
st.header("📊 Dashboard Overview")
metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric("Matches", len(filtered_df))

with metric2:
    participating_teams = (
        set(filtered_df["Team 1"].dropna())
        | set(filtered_df["Team 2"].dropna())
    )
    st.metric("Teams", len(participating_teams))

with metric3:
    st.metric("Years", filtered_df["Year"].nunique())

with metric4:
    st.metric(
        "Decided Matches",
        int((filtered_df["Outcome"] == "Decided").sum())
    )

# Team-specific charts display selected teams only.
team_stats = calculate_team_statistics(filtered_df, effective_teams)

# ==========================================================
# 9. PREPARE SCORE DATA
# ==========================================================
score1 = "Total Score for Team 1"
score2 = "Total Score for Team 2"

score_data_all = pd.concat(
    [
        filtered_df[["Team 1", score1]].rename(
            columns={"Team 1": "Team", score1: "Runs"}
        ),
        filtered_df[["Team 2", score2]].rename(
            columns={"Team 2": "Team", score2: "Runs"}
        )
    ],
    ignore_index=True
)

score_data_all["Runs"] = pd.to_numeric(
    score_data_all["Runs"], errors="coerce"
)
score_data_all = score_data_all.dropna(subset=["Runs", "Team"])

# Team-specific score graphs include selected teams only.
score_data = score_data_all[
    score_data_all["Team"].isin(effective_teams)
].copy()

# ==========================================================
# 10. VISUALIZATION AREA
# ==========================================================
st.divider()
st.header("📈 " + selected_visualization)

# 1. MATCHES PLAYED BY EACH TEAM
if selected_visualization == "Matches Played by Each Team":
    chart_data = team_stats.sort_values(
        "Matches Played", ascending=False
    )
    create_bar_chart(
        chart_data, "Team", "Matches Played",
        "Matches Played by Each Selected Team",
        "Team", "Matches Played"
    )
    st.dataframe(chart_data, use_container_width=True, hide_index=True)

# 2. TEAM-WISE WIN PERCENTAGE
elif selected_visualization == "Team-wise Win Percentage":
    chart_data = team_stats.sort_values(
        "Win Percentage", ascending=False
    )
    create_bar_chart(
        chart_data, "Team", "Win Percentage",
        "Win Percentage by Selected Team",
        "Team", "Win Percentage (%)", ylim=(0, 100)
    )
    st.caption("Win Percentage = Wins / Decided Matches × 100.")
    st.dataframe(chart_data, use_container_width=True, hide_index=True)

# 3. WINS BY TEAM IN A SPECIFIC YEAR
elif selected_visualization == "Wins by Team in a Specific Year":
    chart_data = team_stats.sort_values("Wins", ascending=False)
    create_bar_chart(
        chart_data, "Team", "Wins",
        "Wins by Selected Team(s) in Selected Year(s)",
        "Team", "Wins"
    )
    st.dataframe(chart_data, use_container_width=True, hide_index=True)

# 4. YEAR-WISE MATCH OUTCOMES
elif selected_visualization == "Year-wise Match Outcomes":
    yearly = (
        filtered_df.groupby(["Year", "Outcome"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    st.bar_chart(yearly, use_container_width=True)
    st.dataframe(yearly, use_container_width=True)

# 5. TEAM-WISE AVERAGE RUNS PER MATCH
elif selected_visualization == "Team-wise Average Runs per Match":
    average_runs = (
        score_data.groupby("Team")["Runs"]
        .mean()
        .sort_values(ascending=False)
        .rename("Average Runs per Match")
        .reset_index()
    )
    if average_runs.empty:
        st.info("No valid score data is available.")
    else:
        st.bar_chart(
            average_runs.set_index("Team"),
            y="Average Runs per Match",
            use_container_width=True
        )
        st.dataframe(average_runs, use_container_width=True, hide_index=True)

# 6. INDIA'S WIN PERCENTAGE BY YEAR
elif selected_visualization == "India's Win Percentage by Year":
    india_aliases = {"india", "ind"}
    india_selected = any(
        clean_text(team) in india_aliases
        for team in effective_teams
    )

    if not india_selected:
        st.info(
            "India is not selected. Choose India in the team filter "
            "to view this visualization."
        )
    else:
        india_matches = filtered_df[
            filtered_df["Team 1"].apply(clean_text).isin(india_aliases)
            | filtered_df["Team 2"].apply(clean_text).isin(india_aliases)
        ].copy()

        if india_matches.empty:
            st.info("No India matches match the selected filters.")
        else:
            india_matches["India Won"] = (
                india_matches["Winner"].apply(clean_text).isin(india_aliases)
                & (india_matches["Outcome"] == "Decided")
            )
            india_matches["Decided"] = (
                india_matches["Outcome"] == "Decided"
            )

            india_yearly = (
                india_matches.groupby("Year")
                .agg(
                    Matches=("Winner", "size"),
                    Decided_Matches=("Decided", "sum"),
                    Wins=("India Won", "sum")
                )
                .sort_index()
            )

            india_yearly["Win Percentage"] = (
                india_yearly["Wins"]
                .div(
                    india_yearly["Decided_Matches"].replace(
                        0, float("nan")
                    )
                )
                .mul(100)
                .round(2)
            )

            st.line_chart(
                india_yearly[["Win Percentage"]],
                use_container_width=True
            )
            st.caption(
                "India's win percentage uses decided India matches "
                "as the denominator. Years with no decided matches "
                "have no win-percentage value."
            )
            st.dataframe(india_yearly, use_container_width=True)

# 7. TOP 10 TEAMS BY AVERAGE RUNS
elif selected_visualization == "Top 10 Teams by Average Runs":
    average_runs = (
        score_data.groupby("Team")["Runs"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .rename("Average Runs")
        .reset_index()
    )
    if average_runs.empty:
        st.info("No valid score data is available.")
    else:
        st.bar_chart(
            average_runs.set_index("Team"),
            y="Average Runs",
            use_container_width=True
        )
        st.dataframe(average_runs, use_container_width=True, hide_index=True)

# 8. WINS VS. LOSSES BY TEAM
elif selected_visualization == "Wins vs. Losses by Team":
    chart_data = team_stats.set_index("Team")[["Wins", "Losses"]]
    st.bar_chart(chart_data, use_container_width=True)
    st.dataframe(team_stats, use_container_width=True, hide_index=True)

# 9. HIGHEST TEAM SCORES
elif selected_visualization == "Highest Team Scores":
    top_scores = score_data.sort_values(
        "Runs", ascending=False
    ).head(10)
    create_bar_chart(
        top_scores, "Team", "Runs",
        "Top 10 Highest Scores by Selected Teams",
        "Team", "Runs"
    )
    st.dataframe(top_scores, use_container_width=True, hide_index=True)

# 10. TEAM SCORE COMPARISON
elif selected_visualization == "Team Score Comparison":
    comparison_data = filtered_df.dropna(subset=[score1, score2])

    if comparison_data.empty:
        st.info("No matches have valid scores for both teams.")
    else:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(
            comparison_data[score1],
            comparison_data[score2],
            alpha=0.7
        )
        ax.set_xlabel("Team 1 Total Score")
        ax.set_ylabel("Team 2 Total Score")
        ax.set_title("Team 1 vs. Team 2 Scores in Filtered Matches")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption(
            "Each point represents one filtered match. "
            "Both participating teams are included."
        )

# 11. TOSS WINNERS VS. MATCH WINNERS
elif selected_visualization == "Toss Winners vs. Match Winners":
    toss_candidates = [
        col for col in filtered_df.columns
        if "toss" in col.lower() and "winner" in col.lower()
    ]

    if not toss_candidates:
        st.info(
            "The dataset does not contain a recognized toss-winner column."
        )
    else:
        toss_col = toss_candidates[0]
        toss_data = filtered_df[
            filtered_df["Outcome"] == "Decided"
        ].dropna(subset=[toss_col, "Winner"]).copy()

        toss_data = toss_data[
            toss_data[toss_col].astype(str).str.strip().ne("")
        ]

        if toss_data.empty:
            st.info(
                "No decided matches with valid toss-winner data "
                "are available for the selected filters."
            )
        else:
            toss_data["Toss Winner Won Match"] = (
                toss_data[toss_col].apply(clean_text)
                == toss_data["Winner"].apply(clean_text)
            )
            toss_data["Result"] = toss_data[
                "Toss Winner Won Match"
            ].map({
                True: "Toss winner won match",
                False: "Toss winner lost match"
            })

            counts = (
                toss_data["Result"].value_counts()
                .reindex(
                    [
                        "Toss winner won match",
                        "Toss winner lost match"
                    ],
                    fill_value=0
                )
            )
            st.bar_chart(counts, horizontal=True, use_container_width=True)
            st.dataframe(
                counts.rename("Matches").rename_axis("Result").reset_index(),
                use_container_width=True,
                hide_index=True
            )

# 12. TEAM SCORE DISTRIBUTION - HISTOGRAM
elif selected_visualization == "Team Score Distribution - Histogram":
    if score_data.empty:
        st.info("No valid score values are available.")
    else:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.hist(score_data["Runs"], bins=15, edgecolor="black")
        ax.set_xlabel("Runs")
        ax.set_ylabel("Frequency")
        ax.set_title("Score Distribution for Selected Teams")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption(
            "Scores by selected teams in matches that satisfy "
            "the sidebar filters are included."
        )

# 13. TEAM SCORE DISTRIBUTION - BOX PLOT
elif selected_visualization == "Team Score Distribution - Box Plot":
    if score_data.empty:
        st.info("No valid score values are available.")
    else:
        box_data = []
        box_labels = []

        for team in effective_teams:
            team_scores = score_data.loc[
                score_data["Team"] == team, "Runs"
            ].dropna()

            if not team_scores.empty:
                box_data.append(team_scores.to_numpy())
                box_labels.append(team)

        if not box_data:
            st.info("No score values are available.")
        else:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.boxplot(box_data, labels=box_labels)
            ax.set_xlabel("Selected Team")
            ax.set_ylabel("Runs")
            ax.set_title("Score Distribution by Selected Team")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

# 14. VIEW FILTERED DATASET
elif selected_visualization == "View Filtered Dataset":
    st.write(
        "Matches shown below satisfy the selected team, year, "
        "and outcome filters."
    )
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Dataset",
        data=csv_data,
        file_name="filtered_world_cup_matches.csv",
        mime="text/csv"
    )

# ==========================================================
# 11. TEAM PERFORMANCE SUMMARY
# ==========================================================
st.divider()
st.header("🏆 Team Performance Summary")

summary = team_stats.sort_values(
    "Win Percentage", ascending=False
)
st.dataframe(summary, use_container_width=True, hide_index=True)

st.caption(
    "Statistics reflect the selected filters. Matches Played includes "
    "all appearances, while Win Percentage uses decided matches only."
)

# ==========================================================
# 12. FOOTER
# ==========================================================
st.divider()
st.caption(
    "Cricket World Cup Analysis | "
    "Python • Pandas • Matplotlib • Streamlit"
)
