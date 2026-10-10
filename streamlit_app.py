"""
Cricket World Cup Analysis Dashboard
Keep this file and world_cup_score.csv in the same folder.
Run locally with: streamlit run streamlit_app.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Cricket World Cup Analysis",
    page_icon="🏏",
    layout="wide"
)

PROJECT_DIR = Path(__file__).parent
DATA_FILE = PROJECT_DIR / "world_cup_score.csv"

REQUIRED = [
    "Year", "Team 1", "Team 2", "Winner",
    "Total Score for Team 1", "Total Score for Team 2"
]

INDIA_NAMES = {"india", "ind", "indian cricket team"}
NO_RESULT_NAMES = {
    "", "nan", "none", "no result", "no-result", "abandoned",
    "tied", "tie", "nr", "n/r", "draw"
}


@st.cache_data
def load_data(path):
    data = pd.read_csv(path)
    data.columns = data.columns.astype(str).str.strip()

    missing = [column for column in REQUIRED if column not in data.columns]
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(missing))

    for column in ["Winner", "Team 1", "Team 2", "Match Detail"]:
        if column in data.columns:
            data[column] = data[column].astype("string").str.strip()

    # Prefer the most specific match identifiers available.
    keys = [column for column in ["Year", "Match Number", "Match Detail"]
            if column in data.columns]
    if not keys:
        raise ValueError(
            "Could not find match identifiers such as Year, Match Number, "
            "or Match Detail."
        )

    source_rows = len(data)
    matches = data.drop_duplicates(subset=keys, keep="first").copy()
    matches["Year"] = pd.to_numeric(matches["Year"], errors="coerce")

    for column in ["Total Score for Team 1", "Total Score for Team 2"]:
        matches[column] = pd.to_numeric(matches[column], errors="coerce")

    matches = matches.dropna(subset=["Year", "Team 1", "Team 2"]).copy()
    matches = matches[
        matches["Team 1"].astype(str).str.strip().ne("")
        & matches["Team 2"].astype(str).str.strip().ne("")
    ].copy()
    matches["Year"] = matches["Year"].astype(int)

    return matches, source_rows


def norm(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().lower().split())


def outcome_for_row(row):
    """Return the outcome from Team 1's perspective."""
    winner = norm(row["Winner"])
    team1 = norm(row["Team 1"])
    team2 = norm(row["Team 2"])

    if winner in NO_RESULT_NAMES:
        return "No result / tie"
    if winner == team1:
        return "Team 1 won"
    if winner == team2:
        return "Team 2 won"
    return "Other / unclear"


def show_chart(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# -------------------- LOAD DATA --------------------
st.title("🏏 Cricket World Cup Analysis")
st.subheader("Interactive World Cup Statistics Dashboard")

if not DATA_FILE.exists():
    st.error(
        "`world_cup_score.csv` was not found. Put it in the same folder "
        "as `streamlit_app.py`."
    )
    st.stop()

try:
    matches, source_rows = load_data(str(DATA_FILE))
except Exception as exc:
    st.error(f"Could not load dataset: {exc}")
    st.stop()

if matches.empty:
    st.error("The dataset has no valid match records.")
    st.stop()

# Derive an outcome category once so the same filter is applied everywhere.
matches["Outcome"] = matches.apply(outcome_for_row, axis=1)

all_years = sorted(matches["Year"].dropna().unique().tolist())
all_teams = sorted(
    set(matches["Team 1"].dropna().astype(str))
    | set(matches["Team 2"].dropna().astype(str))
)
outcome_options = [
    "All outcomes",
    "Team 1 won",
    "Team 2 won",
    "No result / tie",
    "Other / unclear",
]

# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.title("🎛️ Dashboard Filters")
st.sidebar.caption(
    "Choose filters here. All 9 graphs, the KPI cards, and the match table "
    "will update together."
)

year_mode = st.sidebar.radio(
    "World Cup year",
    ["All years", "Choose year range", "Choose individual years"],
    index=0
)

if year_mode == "Choose year range":
    if len(all_years) > 1:
        year_range = st.sidebar.slider(
            "Select year range",
            min_value=int(min(all_years)),
            max_value=int(max(all_years)),
            value=(int(min(all_years)), int(max(all_years))),
            step=1
        )
        selected_years = [
            year for year in all_years
            if year_range[0] <= year <= year_range[1]
        ]
    else:
        selected_years = all_years
        st.sidebar.info(f"Only one year is available: {all_years[0]}")
elif year_mode == "Choose individual years":
    selected_years = st.sidebar.multiselect(
        "Select year(s)",
        options=all_years,
        default=all_years
    )
else:
    selected_years = all_years

selected_teams = st.sidebar.multiselect(
    "Select team(s)",
    options=all_teams,
    default=all_teams,
    help="Keep all teams selected for the full dataset. Remove teams to narrow the analysis."
)

selected_outcome = st.sidebar.selectbox(
    "Match outcome",
    options=outcome_options,
    index=0
)

# -------------------- APPLY ALL FILTERS ONCE --------------------
filtered = matches[matches["Year"].isin(selected_years)].copy()

# A match remains if at least one selected team took part.
if selected_teams:
    filtered = filtered[
        filtered["Team 1"].isin(selected_teams)
        | filtered["Team 2"].isin(selected_teams)
    ].copy()
else:
    filtered = filtered.iloc[0:0].copy()

if selected_outcome != "All outcomes":
    filtered = filtered[filtered["Outcome"] == selected_outcome].copy()

st.sidebar.divider()
st.sidebar.write(f"**Matches after filters:** {len(filtered):,}")
if st.sidebar.button("Reset filters"):
    st.rerun()

if filtered.empty:
    st.warning(
        "No matches match these filters. Select more teams, change the year "
        "selection, or choose 'All outcomes'."
    )
    st.stop()

# -------------------- FILTERED KPI CARDS --------------------
teams_in_filtered = sorted(
    set(filtered["Team 1"].dropna().astype(str))
    | set(filtered["Team 2"].dropna().astype(str))
)
years_in_filtered = sorted(filtered["Year"].dropna().unique().tolist())
score_values = pd.concat(
    [
        filtered["Total Score for Team 1"],
        filtered["Total Score for Team 2"]
    ],
    ignore_index=True
).dropna()
average_score = score_values.mean() if not score_values.empty else float("nan")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Matches in view", f"{len(filtered):,}")
k2.metric("Teams in view", f"{len(teams_in_filtered):,}")
k3.metric("Years in view", f"{len(years_in_filtered):,}")
k4.metric(
    "Average team score",
    f"{average_score:.1f}" if pd.notna(average_score) else "N/A"
)
st.caption(
    f"Showing {len(filtered):,} match records from {len(matches):,} "
    f"deduplicated records ({source_rows:,} source CSV rows)."
)

# -------------------- GRAPH 1 --------------------
st.header("1. 📈 World Cup Match Trends by Year")
matches_per_year = filtered.groupby("Year").size().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(matches_per_year.index, matches_per_year.values, marker="o", linewidth=2)
ax.set(
    title="World Cup Match Trends by Year",
    xlabel="World Cup Year",
    ylabel="Number of Matches"
)
ax.grid(True, alpha=0.3)
show_chart(fig)

# -------------------- GRAPH 2 --------------------
st.header("2. 🌍 Team Participation in World Cups")
participation = []
for year, group in filtered.groupby("Year"):
    participating_teams = (
        set(group["Team 1"].dropna().astype(str))
        | set(group["Team 2"].dropna().astype(str))
    )
    participation.append({"Year": year, "Teams": len(participating_teams)})

part = pd.DataFrame(participation).sort_values("Year")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(part["Year"], part["Teams"], marker="o", linewidth=2)
ax.set(
    title="Team Participation in World Cups",
    xlabel="World Cup Year",
    ylabel="Number of Participating Teams"
)
ax.grid(True, alpha=0.3)
show_chart(fig)

# -------------------- GRAPH 3 --------------------
st.header("3. 🏏 Most Frequently Participating Teams")
appearances = pd.concat(
    [filtered["Team 1"], filtered["Team 2"]],
    ignore_index=True
).dropna().value_counts()
appearances = appearances.sort_values().tail(15)

if not appearances.empty:
    fig, ax = plt.subplots(figsize=(10, 7))
    appearances.plot(kind="barh", ax=ax)
    ax.set(
        title="Most Frequently Participating Teams",
        xlabel="Total Match Appearances",
        ylabel="Team"
    )
    show_chart(fig)
else:
    st.info("No team appearance data is available for these filters.")

# Build a common long-format score table from the filtered matches.
t1 = filtered[["Team 1", "Total Score for Team 1"]].rename(
    columns={"Team 1": "Team", "Total Score for Team 1": "Runs"}
)
t2 = filtered[["Team 2", "Total Score for Team 2"]].rename(
    columns={"Team 2": "Team", "Total Score for Team 2": "Runs"}
)
team_scores = pd.concat([t1, t2], ignore_index=True)
team_scores["Runs"] = pd.to_numeric(team_scores["Runs"], errors="coerce")

# -------------------- GRAPH 4 --------------------
st.header("4. 🎯 Team-wise Average Runs Comparison")
avg = (
    team_scores.dropna(subset=["Team", "Runs"])
    .groupby("Team")["Runs"].mean()
    .sort_values()
    .tail(15)
)
if not avg.empty:
    fig, ax = plt.subplots(figsize=(10, 7))
    avg.plot(kind="barh", ax=ax)
    ax.set(
        title="Team-wise Average Runs Comparison",
        xlabel="Average Runs per Match",
        ylabel="Team"
    )
    show_chart(fig)
else:
    st.info("No score data is available for these filters.")

# -------------------- GRAPH 5 --------------------
st.header("5. 📊 Average Team Scores Across Years")
year_scores = pd.concat(
    [
        filtered[["Year", "Total Score for Team 1"]].rename(
            columns={"Total Score for Team 1": "Runs"}
        ),
        filtered[["Year", "Total Score for Team 2"]].rename(
            columns={"Total Score for Team 2": "Runs"}
        ),
    ],
    ignore_index=True
)
year_scores["Runs"] = pd.to_numeric(year_scores["Runs"], errors="coerce")
avg_year = (
    year_scores.dropna(subset=["Year", "Runs"])
    .groupby("Year")["Runs"].mean()
    .sort_index()
)
if not avg_year.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(avg_year.index, avg_year.values, alpha=0.4)
    ax.plot(avg_year.index, avg_year.values, marker="o")
    ax.set(
        title="Average Team Scores Across Years",
        xlabel="World Cup Year",
        ylabel="Average Team Runs"
    )
    ax.grid(True, alpha=0.3)
    show_chart(fig)
else:
    st.info("No score data is available for these filters.")

# -------------------- GRAPH 6 --------------------
st.header("6. 🥧 India's World Cup Match Outcome Distribution")
india_mask = (
    filtered["Team 1"].map(lambda value: norm(value) in INDIA_NAMES)
    | filtered["Team 2"].map(lambda value: norm(value) in INDIA_NAMES)
)
india = filtered[india_mask].copy()

if not india.empty:
    india_counts = (
        india.apply(outcome_for_row, axis=1)
        .value_counts()
        .reindex(outcome_options[1:], fill_value=0)
    )
    india_counts = india_counts[india_counts > 0]
    if not india_counts.empty:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            india_counts.values,
            labels=india_counts.index,
            autopct="%1.1f%%",
            startangle=90
        )
        ax.set_title("India's World Cup Match Outcome Distribution")
        show_chart(fig)
    else:
        st.info("No India match outcomes are available for these filters.")
else:
    st.info(
        "India is not present in the filtered matches. Change the team, "
        "year, or outcome filters to include India's matches."
    )

# -------------------- GRAPH 7 --------------------
st.header("7. ⚡ Relationship Between Team 1 and Team 2 Scores")
score_pair = filtered[
    ["Total Score for Team 1", "Total Score for Team 2"]
].dropna()
if not score_pair.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        score_pair["Total Score for Team 1"],
        score_pair["Total Score for Team 2"],
        alpha=0.6
    )
    ax.set(
        title="Relationship Between Team 1 and Team 2 Scores",
        xlabel="Team 1 Runs",
        ylabel="Team 2 Runs"
    )
    ax.grid(True, alpha=0.3)
    show_chart(fig)
else:
    st.info("No complete score pairs are available for these filters.")

# -------------------- GRAPH 8 --------------------
st.header("8. 📉 Distribution of World Cup Team Scores")
runs = pd.concat(
    [filtered["Total Score for Team 1"], filtered["Total Score for Team 2"]],
    ignore_index=True
).dropna()
if not runs.empty:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(runs, bins=15, edgecolor="black")
    ax.set(
        title="Distribution of World Cup Team Scores",
        xlabel="Total Runs",
        ylabel="Frequency"
    )
    show_chart(fig)
else:
    st.info("No scores are available for these filters.")

# -------------------- GRAPH 9 --------------------
st.header("9. 🔥 Comparison of Team Score Distributions")
runs1 = filtered["Total Score for Team 1"].dropna()
runs2 = filtered["Total Score for Team 2"].dropna()
if not runs1.empty and not runs2.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.violinplot(
        [runs1.values, runs2.values],
        showmeans=True,
        showmedians=True
    )
    ax.set_xticks([1, 2], ["Team 1", "Team 2"])
    ax.set(
        title="Comparison of Team Score Distributions",
        xlabel="Team",
        ylabel="Total Runs"
    )
    show_chart(fig)
else:
    st.info("Not enough score data for the violin plot.")

# -------------------- FILTERED TABLE --------------------
st.divider()
st.header("📋 View Filtered Match Dataset")
table_columns = [column for column in filtered.columns if column != "Outcome"]
st.dataframe(
    filtered[table_columns],
    use_container_width=True,
    hide_index=True
)
st.download_button(
    "⬇️ Download Filtered Dataset as CSV",
    data=filtered[table_columns].to_csv(index=False).encode("utf-8"),
    file_name="filtered_world_cup_matches.csv",
    mime="text/csv"
)

st.caption("Cricket World Cup Analysis | Python • Pandas • Matplotlib • Streamlit")
