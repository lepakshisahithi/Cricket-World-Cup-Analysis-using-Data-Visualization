import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Cricket World Cup Analysis",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Cricket World Cup Analysis")
st.subheader("Interactive Data Visualization and Team Performance Dashboard")

st.write(
    "Explore team performance, match outcomes, win percentages, "
    "and scoring patterns across Cricket World Cup years."
)

# ==========================================
# LOAD DATASET
# ==========================================
@st.cache_data
def load_data():
    return pd.read_csv("world_cup_score.csv")


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Dataset not found. Keep world_cup_score.csv "
        "in the same GitHub repository as app.py."
    )
    st.stop()

df.columns = df.columns.astype(str).str.strip()
df = df.dropna(how="all")

# ==========================================
# CHECK REQUIRED COLUMNS
# ==========================================
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

# ==========================================
# DATA CLEANING
# ==========================================
for col in ["Winner", "Team 1", "Team 2"]:
    df[col] = df[col].astype("string").str.strip()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

for col in [
    "Total Score for Team 1",
    "Total Score for Team 2"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Year", "Match Number"])

# The CSV contains multiple rows per match.
# Keep one record for each year and match number.
matches = df.drop_duplicates(
    subset=["Year", "Match Number"],
    keep="first"
).copy()

matches["Year"] = matches["Year"].astype(int)

# Remove invalid team names
matches = matches.dropna(subset=["Team 1", "Team 2"])

if matches.empty:
    st.warning("No valid match records were found.")
    st.stop()

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def is_no_result(value):
    return clean_text(value) in {
        "", "nan", "none", "no result",
        "abandoned", "tied", "draw"
    }


def get_outcome(row):
    winner = clean_text(row["Winner"])

    if is_no_result(winner):
        return "Other / No Result"

    team1 = clean_text(row["Team 1"])
    team2 = clean_text(row["Team 2"])

    if winner == team1 or winner == team2:
        return "Decided"

    return "Other / No Result"


def calculate_team_statistics(data):
    """
    Count each team's appearances, wins, losses,
    and win percentage.
    """
    team_names = sorted(
        set(data["Team 1"].dropna().astype(str))
        | set(data["Team 2"].dropna().astype(str))
    )

    rows = []

    for team in team_names:
        team_matches = data[
            (data["Team 1"].astype(str) == team)
            | (data["Team 2"].astype(str) == team)
        ]

        appearances = len(team_matches)

        wins = sum(
            clean_text(winner) == clean_text(team)
            for winner in team_matches["Winner"]
        )

        decided_matches = sum(
            not is_no_result(winner)
            and clean_text(winner) in {
                clean_text(t1), clean_text(t2)
            }
            for winner, t1, t2 in zip(
                team_matches["Winner"],
                team_matches["Team 1"],
                team_matches["Team 2"]
            )
        )

        losses = max(decided_matches - wins, 0)

        win_percentage = (
            wins / appearances * 100
            if appearances else 0
        )

        rows.append({
            "Team": team,
            "Matches Played": appearances,
            "Wins": wins,
            "Losses": losses,
            "Win Percentage": round(win_percentage, 2)
        })

    return pd.DataFrame(rows)


# ==========================================
# SIDEBAR FILTERS
# ==========================================
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
    help="Choose the teams you want to analyse."
)

selected_years = st.sidebar.multiselect(
    "Select Year(s)",
    options=all_years,
    default=all_years,
    help="Choose the World Cup years."
)

outcome_options = [
    "All Outcomes",
    "Decided",
    "Other / No Result"
]

selected_outcome = st.sidebar.selectbox(
    "Select Match Outcome",
    outcome_options
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

# ==========================================
# APPLY FILTERS
# ==========================================
filtered_df = matches.copy()

if selected_teams:
    filtered_df = filtered_df[
        filtered_df["Team 1"].isin(selected_teams)
        | filtered_df["Team 2"].isin(selected_teams)
    ]
else:
    st.warning("Please select at least one team.")
    st.stop()

if selected_years:
    filtered_df = filtered_df[
        filtered_df["Year"].isin(selected_years)
    ]
else:
    st.warning("Please select at least one year.")
    st.stop()

filtered_df = filtered_df.copy()

filtered_df["Outcome"] = filtered_df.apply(
    get_outcome,
    axis=1
)

if selected_outcome != "All Outcomes":
    filtered_df = filtered_df[
        filtered_df["Outcome"] == selected_outcome
    ]

if filtered_df.empty:
    st.warning(
        "No matches match your selected filters. "
        "Try selecting different teams, years, or outcomes."
    )
    st.stop()

# ==========================================
# DASHBOARD OVERVIEW
# ==========================================
st.header("📊 Dashboard Overview")

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric("Matches", len(filtered_df))

with metric2:
    st.metric(
        "Teams",
        len(
            set(filtered_df["Team 1"])
            | set(filtered_df["Team 2"])
        )
    )

with metric3:
    st.metric(
        "Years",
        filtered_df["Year"].nunique()
    )

with metric4:
    st.metric(
        "Decided Matches",
        (filtered_df["Outcome"] == "Decided").sum()
    )

# ==========================================
# TEAM STATISTICS
# ==========================================
team_stats = calculate_team_statistics(filtered_df)

# ==========================================
# PREPARE TEAM SCORE DATA
# ==========================================
score1 = "Total Score for Team 1"
score2 = "Total Score for Team 2"

score_data = pd.concat([
    filtered_df[["Team 1", score1]].rename(
        columns={"Team 1": "Team", score1: "Runs"}
    ),
    filtered_df[["Team 2", score2]].rename(
        columns={"Team 2": "Team", score2: "Runs"}
    )
], ignore_index=True)

score_data["Runs"] = pd.to_numeric(
    score_data["Runs"],
    errors="coerce"
)

score_data = score_data.dropna(subset=["Runs"])

# ==========================================
# VISUALIZATION AREA
# ==========================================
st.divider()

st.header("📈 " + selected_visualization)

# ------------------------------------------
# 1. MATCHES PLAYED BY EACH TEAM
# ------------------------------------------
if selected_visualization == "Matches Played by Each Team":

    chart_data = team_stats.sort_values(
        "Matches Played",
        ascending=False
    )

    if not chart_data.empty:
        fig, ax = plt.subplots(figsize=(11, 5))

        ax.bar(
            chart_data["Team"],
            chart_data["Matches Played"]
        )

        ax.set_xlabel("Team")
        ax.set_ylabel("Matches Played")
        ax.set_title("Matches Played by Each Team")
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        st.dataframe(chart_data, use_container_width=True)

# ------------------------------------------
# 2. TEAM-WISE WIN PERCENTAGE
# ------------------------------------------
elif selected_visualization == "Team-wise Win Percentage":

    chart_data = team_stats.sort_values(
        "Win Percentage",
        ascending=False
    )

    fig, ax = plt.subplots(figsize=(11, 5))

    ax.bar(
        chart_data["Team"],
        chart_data["Win Percentage"]
    )

    ax.set_xlabel("Team")
    ax.set_ylabel("Win Percentage (%)")
    ax.set_title("Team-wise Win Percentage")
    ax.set_ylim(0, 100)

    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(chart_data, use_container_width=True)

# ------------------------------------------
# 3. WINS BY TEAM IN A SPECIFIC YEAR
# ------------------------------------------
elif selected_visualization == "Wins by Team in a Specific Year":

    chart_data = calculate_team_statistics(filtered_df)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        chart_data["Team"],
        chart_data["Wins"]
    )

    ax.set_xlabel("Team")
    ax.set_ylabel("Wins")
    ax.set_title("Team Wins in Selected Year(s)")

    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

# ------------------------------------------
# 4. YEAR-WISE MATCH OUTCOMES
# ------------------------------------------
elif selected_visualization == "Year-wise Match Outcomes":

    yearly = (
        filtered_df.groupby(["Year", "Outcome"])
        .size()
        .unstack(fill_value=0)
    )

    st.bar_chart(yearly)

# ------------------------------------------
# 5. TEAM-WISE AVERAGE RUNS PER MATCH
# ------------------------------------------
elif selected_visualization == "Team-wise Average Runs per Match":

    average_runs = (
        score_data.groupby("Team")["Runs"]
        .mean()
        .sort_values(ascending=False)
    )

    st.bar_chart(average_runs)

    st.dataframe(
        average_runs.rename(
            "Average Runs per Match"
        ).reset_index(),
        use_container_width=True
    )

# ------------------------------------------
# 6. INDIA'S WIN PERCENTAGE BY YEAR
# ------------------------------------------
elif selected_visualization == "India's Win Percentage by Year":

    india_aliases = {
        "india", "ind"
    }

    india_matches = filtered_df[
        filtered_df["Team 1"].apply(
            lambda x: clean_text(x) in india_aliases
        )
        | filtered_df["Team 2"].apply(
            lambda x: clean_text(x) in india_aliases
        )
    ].copy()

    if india_matches.empty:
        st.info(
            "India is not included in the current filtered matches. "
            "Select India in the team filter to view this chart."
        )
    else:
        india_matches["India Won"] = (
            india_matches["Winner"].apply(clean_text).isin(
                india_aliases
            )
        )

        india_yearly = india_matches.groupby("Year").agg(
            Matches=("Winner", "size"),
            Wins=("India Won", "sum")
        )

        india_yearly["Win Percentage"] = (
            india_yearly["Wins"]
            / india_yearly["Matches"]
            * 100
        ).round(2)

        st.line_chart(
            india_yearly["Win Percentage"]
        )

        st.dataframe(
            india_yearly,
            use_container_width=True
        )

# ------------------------------------------
# 7. TOP 10 TEAMS BY AVERAGE RUNS
# ------------------------------------------
elif selected_visualization == "Top 10 Teams by Average Runs":

    average_runs = (
        score_data.groupby("Team")["Runs"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    st.bar_chart(average_runs)

    st.dataframe(
        average_runs.rename(
            "Average Runs"
        ).reset_index(),
        use_container_width=True
    )

# ------------------------------------------
# 8. WINS VS. LOSSES BY TEAM
# ------------------------------------------
elif selected_visualization == "Wins vs. Losses by Team":

    chart_data = team_stats.set_index("Team")[
        ["Wins", "Losses"]
    ]

    st.bar_chart(chart_data)

    st.dataframe(
        team_stats,
        use_container_width=True
    )

# ------------------------------------------
# 9. HIGHEST TEAM SCORES
# ------------------------------------------
elif selected_visualization == "Highest Team Scores":

    top_scores = score_data.sort_values(
        "Runs",
        ascending=False
    ).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        top_scores["Team"],
        top_scores["Runs"]
    )

    ax.set_xlabel("Team")
    ax.set_ylabel("Runs")
    ax.set_title("Top 10 Highest Team Scores")

    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(top_scores, use_container_width=True)

# ------------------------------------------
# 10. TEAM SCORE COMPARISON
# ------------------------------------------
elif selected_visualization == "Team Score Comparison":

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        filtered_df[score1],
        filtered_df[score2],
        alpha=0.7
    )

    ax.set_xlabel("Team 1 Total Score")
    ax.set_ylabel("Team 2 Total Score")
    ax.set_title("Team 1 vs. Team 2 Scores")

    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

# ------------------------------------------
# 11. TOSS WINNERS VS. MATCH WINNERS
# ------------------------------------------
elif selected_visualization == "Toss Winners vs. Match Winners":

    toss_candidates = [
        col for col in filtered_df.columns
        if "toss" in col.lower()
        and "winner" in col.lower()
    ]

    if toss_candidates:
        toss_col = toss_candidates[0]

        toss_data = filtered_df.dropna(
            subset=[toss_col, "Winner"]
        ).copy()

        toss_data["Toss Winner Won Match"] = (
            toss_data[toss_col].apply(clean_text)
            == toss_data["Winner"].apply(clean_text)
        )

        counts = toss_data[
            "Toss Winner Won Match"
        ].value_counts()

        counts.index = [
            "Toss winner won match" if value
            else "Toss winner lost match"
            for value in counts.index
        ]

        st.bar_chart(counts)
    else:
        st.info(
            "The dataset does not contain a recognized toss-winner column."
        )

# ------------------------------------------
# 12. HISTOGRAM
# ------------------------------------------
elif selected_visualization == "Team Score Distribution - Histogram":

    if not score_data.empty:
        fig, ax = plt.subplots(figsize=(9, 5))

        ax.hist(
            score_data["Runs"],
            bins=15,
            edgecolor="black"
        )

        ax.set_xlabel("Runs")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Team Scores")

        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No score values are available.")

# ------------------------------------------
# 13. BOX PLOT
# ------------------------------------------
elif selected_visualization == "Team Score Distribution - Box Plot":

    team1_scores = filtered_df[score1].dropna()
    team2_scores = filtered_df[score2].dropna()

    if not team1_scores.empty or not team2_scores.empty:
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.boxplot(
            [team1_scores, team2_scores],
            tick_labels=["Team 1", "Team 2"]
        )

        ax.set_ylabel("Runs")
        ax.set_title("Team Score Distribution")

        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No score values are available.")

# ------------------------------------------
# 14.