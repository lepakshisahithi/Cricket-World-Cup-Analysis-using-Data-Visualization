"""
Cricket World Cup Analysis Dashboard with GLOBAL SIDEBAR FILTERS.

Keep this file and world_cup_score.csv in the same folder.
Streamlit Cloud main file: streamlit_app.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Cricket World Cup Analysis", page_icon="🏏", layout="wide")

PROJECT_DIR = Path(__file__).parent
DATA_FILE = PROJECT_DIR / "world_cup_score.csv"

REQUIRED = [
    "Year", "Team 1", "Team 2", "Winner",
    "Total Score for Team 1", "Total Score for Team 2",
]
INDIA_NAMES = {"india", "ind", "indian cricket team"}
NO_RESULT_NAMES = {
    "", "nan", "none", "no result", "no-result", "abandoned",
    "tied", "tie", "nr", "n/r", "draw",
}


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df.columns = df.columns.astype(str).str.strip()
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(missing))

    for c in ["Team 1", "Team 2", "Winner", "Match Detail"]:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()

    # Deduplicate only when an identifier is available.
    keys = [c for c in ["Year", "Match Number", "Match Detail"] if c in df.columns]
    if keys:
        df = df.drop_duplicates(subset=keys, keep="first").copy()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    for c in ["Total Score for Team 1", "Total Score for Team 2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Year", "Team 1", "Team 2"]).copy()
    df = df[
        df["Team 1"].astype(str).str.strip().ne("")
        & df["Team 2"].astype(str).str.strip().ne("")
    ].copy()
    df["Year"] = df["Year"].astype(int)
    return df


def norm(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().lower().split())


def is_no_result(value):
    return norm(value) in NO_RESULT_NAMES


def result_category(row):
    winner = norm(row["Winner"])
    t1 = norm(row["Team 1"])
    t2 = norm(row["Team 2"])
    if winner in NO_RESULT_NAMES:
        return "No Result / Tie"
    if winner == t1:
        return "Team 1 Win"
    if winner == t2:
        return "Team 2 Win"
    return "Other / Unclear"


def show_chart(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


st.title("🏏 Cricket World Cup Analysis")
st.write("Use the sidebar to filter the data. **Every graph and the table update together.**")

if not DATA_FILE.exists():
    st.error("Dataset not found. Put `world_cup_score.csv` beside `streamlit_app.py` in your GitHub repository.")
    st.stop()

try:
    matches = load_data(str(DATA_FILE))
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

if matches.empty:
    st.error("No valid match records were found in the dataset.")
    st.stop()

matches["Result Category"] = matches.apply(result_category, axis=1)

all_years = sorted(matches["Year"].unique().tolist())
all_teams = sorted(
    set(matches["Team 1"].dropna().astype(str))
    | set(matches["Team 2"].dropna().astype(str))
)

# ============================================================
# SIDEBAR: ONE SHARED FILTER SET FOR THE ENTIRE DASHBOARD
# ============================================================
st.sidebar.title("🎛️ Global Dashboard Filters")
st.sidebar.caption("These selections apply to ALL 9 graphs and the match table.")

year_choice = st.sidebar.selectbox(
    "📅 Years",
    ["All Years", "Select Year Range", "Select Specific Years"],
    key="global_year_mode",
)

if year_choice == "All Years":
    chosen_years = all_years
elif year_choice == "Select Year Range":
    if len(all_years) > 1:
        year_range = st.sidebar.slider(
            "Choose year range",
            min_value=int(min(all_years)),
            max_value=int(max(all_years)),
            value=(int(min(all_years)), int(max(all_years))),
            step=1,
            key="global_year_range",
        )
        chosen_years = [y for y in all_years if year_range[0] <= y <= year_range[1]]
    else:
        chosen_years = all_years
        st.sidebar.info("Only one year exists in the dataset.")
else:
    chosen_years = st.sidebar.multiselect(
        "Choose specific year(s)",
        options=all_years,
        default=all_years,
        key="global_years",
    )

team_choice = st.sidebar.selectbox(
    "🏏 Teams",
    ["All Teams", "Choose Teams", "One Team"],
    key="global_team_mode",
)
if team_choice == "All Teams":
    chosen_teams = all_teams
elif team_choice == "Choose Teams":
    chosen_teams = st.sidebar.multiselect(
        "Select team(s)",
        options=all_teams,
        default=all_teams,
        key="global_teams",
    )
else:
    one_team = st.sidebar.selectbox(
        "Select one team",
        options=all_teams,
        key="global_one_team",
    )
    chosen_teams = [one_team]

winner_choice = st.sidebar.selectbox(
    "🏆 Match Result / Winner",
    [
        "All Results",
        "Only Wins by Selected Team(s)",
        "Only Losses by Selected Team(s)",
        "Only No Result / Tie",
    ],
    key="global_winner_filter",
    help=(
        "Win/Loss uses the teams selected above. If multiple teams are selected, "
        "a match is included when one of those teams has the chosen outcome."
    ),
)

st.sidebar.divider()
if st.sidebar.button("🔄 Reset all filters", use_container_width=True):
    for key in [
        "global_year_mode", "global_year_range", "global_years",
        "global_team_mode", "global_teams", "global_one_team",
        "global_winner_filter",
    ]:
        st.session_state.pop(key, None)
    st.rerun()

# Apply year + team filters first.
filtered = matches[matches["Year"].isin(chosen_years)].copy()

if chosen_teams:
    filtered = filtered[
        filtered["Team 1"].isin(chosen_teams)
        | filtered["Team 2"].isin(chosen_teams)
    ].copy()
else:
    filtered = filtered.iloc[0:0].copy()

# Apply outcome filter based on the selected teams.
if winner_choice == "Only Wins by Selected Team(s)":
    if chosen_teams:
        filtered = filtered[
            filtered["Winner"].map(lambda x: norm(x) in {norm(t) for t in chosen_teams})
        ].copy()
    else:
        filtered = filtered.iloc[0:0].copy()
elif winner_choice == "Only Losses by Selected Team(s)":
    if chosen_teams:
        selected_norm = {norm(t) for t in chosen_teams}
        filtered = filtered[
            filtered.apply(
                lambda row: (
                    norm(row["Winner"]) not in NO_RESULT_NAMES
                    and norm(row["Winner"]) not in selected_norm
                    and (
                        norm(row["Team 1"]) in selected_norm
                        or norm(row["Team 2"]) in selected_norm
                    )
                ),
                axis=1,
            )
        ].copy()
    else:
        filtered = filtered.iloc[0:0].copy()
elif winner_choice == "Only No Result / Tie":
    filtered = filtered[
        filtered["Winner"].map(is_no_result)
    ].copy()

st.sidebar.markdown(f"**Matches after filters: {len(filtered):,}**")

if filtered.empty:
    st.warning(
        "No matches match your current filters. Try All Years, All Teams, "
        "and All Results, or broaden your selections."
    )
    st.stop()

# Everything below uses ONLY `filtered`, so all charts stay synchronized.
teams_in_view = sorted(
    set(filtered["Team 1"].astype(str)) | set(filtered["Team 2"].astype(str))
)
years_in_view = sorted(filtered["Year"].unique().tolist())
all_runs = pd.concat(
    [filtered["Total Score for Team 1"], filtered["Total Score for Team 2"]],
    ignore_index=True,
).dropna()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Filtered Matches", f"{len(filtered):,}")
m2.metric("Teams in View", f"{len(teams_in_view):,}")
m3.metric("Years in View", f"{len(years_in_view):,}")
m4.metric("Average Team Score", f"{all_runs.mean():.1f}" if not all_runs.empty else "N/A")

st.caption(
    f"Active filters — Years: {len(chosen_years)} | "
    f"Selected teams: {', '.join(chosen_teams) if chosen_teams else 'None'} | "
    f"Result: {winner_choice}"
)

# Graph 1
st.header("1. 📈 World Cup Match Trends by Year")
matches_per_year = filtered.groupby("Year").size().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(matches_per_year.index, matches_per_year.values, marker="o", linewidth=2)
ax.set(title="World Cup Match Trends by Year", xlabel="Year", ylabel="Number of Matches")
ax.grid(True, alpha=0.3)
show_chart(fig)

# Graph 2
st.header("2. 🌍 Team Participation in World Cups")
participation = []
for year, group in filtered.groupby("Year"):
    teamset = set(group["Team 1"].dropna().astype(str)) | set(group["Team 2"].dropna().astype(str))
    participation.append({"Year": year, "Teams": len(teamset)})
part = pd.DataFrame(participation).sort_values("Year")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(part["Year"], part["Teams"], marker="o", linewidth=2)
ax.set(title="Team Participation in World Cups", xlabel="Year", ylabel="Teams")
ax.grid(True, alpha=0.3)
show_chart(fig)

# Graph 3
st.header("3. 🏏 Most Frequently Participating Teams")
appearances = pd.concat([filtered["Team 1"], filtered["Team 2"]], ignore_index=True).value_counts()
appearances = appearances.sort_values().tail(15)
fig, ax = plt.subplots(figsize=(10, 7))
appearances.plot(kind="barh", ax=ax)
ax.set(title="Most Frequently Participating Teams", xlabel="Match Appearances", ylabel="Team")
show_chart(fig)

# Shared long-format score data
team_scores = pd.concat(
    [
        filtered[["Team 1", "Total Score for Team 1"]].rename(
            columns={"Team 1": "Team", "Total Score for Team 1": "Runs"}
        ),
        filtered[["Team 2", "Total Score for Team 2"]].rename(
            columns={"Team 2": "Team", "Total Score for Team 2": "Runs"}
        ),
    ],
    ignore_index=True,
)
team_scores["Runs"] = pd.to_numeric(team_scores["Runs"], errors="coerce")

# Graph 4
st.header("4. 🎯 Team-wise Average Runs Comparison")
avg_runs = team_scores.dropna(subset=["Team", "Runs"]).groupby("Team")["Runs"].mean().sort_values().tail(15)
fig, ax = plt.subplots(figsize=(10, 7))
avg_runs.plot(kind="barh", ax=ax)
ax.set(title="Team-wise Average Runs", xlabel="Average Runs", ylabel="Team")
show_chart(fig)

# Graph 5
st.header("5. 📊 Average Team Scores Across Years")
year_scores = pd.concat(
    [
        filtered[["Year", "Total Score for Team 1"]].rename(columns={"Total Score for Team 1": "Runs"}),
        filtered[["Year", "Total Score for Team 2"]].rename(columns={"Total Score for Team 2": "Runs"}),
    ],
    ignore_index=True,
)
year_scores["Runs"] = pd.to_numeric(year_scores["Runs"], errors="coerce")
avg_year = year_scores.dropna(subset=["Year", "Runs"]).groupby("Year")["Runs"].mean().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(avg_year.index, avg_year.values, marker="o", linewidth=2)
ax.set(title="Average Team Scores Across Years", xlabel="Year", ylabel="Average Runs")
ax.grid(True, alpha=0.3)
show_chart(fig)

# Graph 6
st.header("6. 🥧 Match Outcome Distribution for India")
india_mask = (
    filtered["Team 1"].map(lambda x: norm(x) in INDIA_NAMES)
    | filtered["Team 2"].map(lambda x: norm(x) in INDIA_NAMES)
)
india = filtered[india_mask].copy()
if not india.empty:
    india_outcomes = india.apply(result_category, axis=1).value_counts()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(india_outcomes.values, labels=india_outcomes.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("India Match Outcome Distribution (filtered matches)")
    show_chart(fig)
else:
    st.info("No India matches exist within the current global filters.")

# Graph 7
st.header("7. ⚡ Relationship Between Team 1 and Team 2 Scores")
score_pair = filtered[["Total Score for Team 1", "Total Score for Team 2"]].dropna()
if not score_pair.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(score_pair["Total Score for Team 1"], score_pair["Total Score for Team 2"], alpha=0.6)
    ax.set(title="Team 1 vs Team 2 Scores", xlabel="Team 1 Runs", ylabel="Team 2 Runs")
    ax.grid(True, alpha=0.3)
    show_chart(fig)
else:
    st.info("No complete score pairs available.")

# Graph 8
st.header("8. 📉 Distribution of World Cup Team Scores")
runs = pd.concat(
    [filtered["Total Score for Team 1"], filtered["Total Score for Team 2"]],
    ignore_index=True,
).dropna()
if not runs.empty:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(runs, bins=15, edgecolor="black")
    ax.set(title="Distribution of Team Scores", xlabel="Runs", ylabel="Frequency")
    show_chart(fig)
else:
    st.info("No scores available.")

# Graph 9
st.header("9. 🔥 Comparison of Team Score Distributions")
runs1 = filtered["Total Score for Team 1"].dropna()
runs2 = filtered["Total Score for Team 2"].dropna()
if not runs1.empty and not runs2.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.violinplot([runs1.values, runs2.values], showmeans=True, showmedians=True)
    ax.set_xticks([1, 2], ["Team 1", "Team 2"])
    ax.set(title="Team Score Distribution Comparison", xlabel="Team", ylabel="Runs")
    show_chart(fig)
else:
    st.info("Not enough score data for the violin plot.")

# Filtered table
st.divider()
st.header("📋 Filtered Match Dataset")
display_cols = [c for c in filtered.columns if c != "Result Category"]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
st.download_button(
    "⬇️ Download Filtered Dataset as CSV",
    data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
    file_name="filtered_world_cup_matches.csv",
    mime="text/csv",
)
st.caption("Cricket World Cup Analysis | Python • Pandas • Matplotlib • Streamlit")
