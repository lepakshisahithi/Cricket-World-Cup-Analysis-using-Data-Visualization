"""
Cricket World Cup Analysis Dashboard
Keep this file and world_cup_score.csv in the same folder.
Run locally with: streamlit run streamlit_app.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Cricket World Cup Analysis", page_icon="🏏", layout="wide")
st.title("🏏 Cricket World Cup Analysis")
st.subheader("Interactive World Cup Statistics Dashboard")

PROJECT_DIR = Path(__file__).parent
DATA_FILE = PROJECT_DIR / "world_cup_score.csv"

REQUIRED = [
    "Year", "Team 1", "Team 2", "Winner",
    "Total Score for Team 1", "Total Score for Team 2"
]

@st.cache_data
def load_data(path):
    data = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in data.columns]
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(missing))
    for c in ["Winner", "Team 1", "Team 2", "Match Detail"]:
        if c in data.columns:
            data[c] = data[c].astype("string").str.strip()
    keys = [c for c in ["Year", "Match Number", "Match Detail"] if c in data.columns]
    if not keys:
        raise ValueError("Could not find match identifiers (Year, Match Number, Match Detail).")
    matches = data.drop_duplicates(subset=keys, keep="first").copy()
    matches["Year"] = pd.to_numeric(matches["Year"], errors="coerce")
    for c in ["Total Score for Team 1", "Total Score for Team 2"]:
        matches[c] = pd.to_numeric(matches[c], errors="coerce")
    return matches, len(data)

if not DATA_FILE.exists():
    st.error("world_cup_score.csv was not found. Put it in the same folder as streamlit_app.py.")
    st.stop()
try:
    matches, source_rows = load_data(str(DATA_FILE))
except Exception as e:
    st.error(f"Could not load dataset: {e}")
    st.stop()
if matches.empty:
    st.error("The dataset has no match records.")
    st.stop()

def show_chart(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

def norm(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().lower().split())

INDIA_NAMES = {"india", "ind", "indian cricket team"}

# Overview
years = sorted(matches["Year"].dropna().unique().tolist())
teams = sorted(set(matches["Team 1"].dropna().astype(str)) |
               set(matches["Team 2"].dropna().astype(str)))
a, b, c, d = st.columns(4)
a.metric("Unique match records", f"{len(matches):,}")
b.metric("Teams", f"{len(teams):,}")
c.metric("Years", f"{len(years):,}")
d.metric("Source CSV rows", f"{source_rows:,}")
st.caption("The code keeps the first row for each available match identifier. Verify that this row contains final scores and the winner.")

# Filters
st.sidebar.header("Dashboard Filters")
selected_years = st.sidebar.multiselect("Select World Cup year(s)", years, default=years)
selected_teams = st.sidebar.multiselect("Select team(s)", teams, default=teams)
filtered = matches.copy()
if selected_years:
    filtered = filtered[filtered["Year"].isin(selected_years)]
if selected_teams:
    filtered = filtered[filtered["Team 1"].isin(selected_teams) |
                        filtered["Team 2"].isin(selected_teams)]
if filtered.empty:
    st.warning("No matches match these filters. Change or clear the filters.")
    st.stop()

# Graph 1
st.header("1. 📈 World Cup Match Trends by Year")
s = filtered.groupby("Year").size().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(s.index, s.values, marker="o", linewidth=2)
ax.set(title="World Cup Match Trends by Year", xlabel="World Cup Year", ylabel="Number of Matches")
ax.grid(True, alpha=.3)
show_chart(fig)

# Graph 2
st.header("2. 🌍 Team Participation in World Cups")
participation = []
for year, group in filtered.groupby("Year"):
    teamset = set(group["Team 1"].dropna().astype(str))
    teamset.update(group["Team 2"].dropna().astype(str))
    participation.append({"Year": year, "Teams": len(teamset)})
part = pd.DataFrame(participation).sort_values("Year")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(part["Year"], part["Teams"], marker="o", linewidth=2)
ax.set(title="Team Participation in World Cups", xlabel="World Cup Year", ylabel="Number of Participating Teams")
ax.grid(True, alpha=.3)
show_chart(fig)

# Graph 3
st.header("3. 🏏 Most Frequently Participating Teams")
appearances = pd.concat([filtered["Team 1"].dropna(), filtered["Team 2"].dropna()], ignore_index=True).value_counts()
appearances = appearances.sort_values().tail(15)
fig, ax = plt.subplots(figsize=(10, 7))
appearances.plot(kind="barh", ax=ax)
ax.set(title="Most Frequently Participating Teams", xlabel="Total Match Appearances", ylabel="Team")
show_chart(fig)

# Prepare team score table
t1 = filtered[["Team 1", "Total Score for Team 1"]].rename(columns={"Team 1":"Team", "Total Score for Team 1":"Runs"})
t2 = filtered[["Team 2", "Total Score for Team 2"]].rename(columns={"Team 2":"Team", "Total Score for Team 2":"Runs"})
team_scores = pd.concat([t1, t2], ignore_index=True)
team_scores["Runs"] = pd.to_numeric(team_scores["Runs"], errors="coerce")

# Graph 4
st.header("4. 🎯 Team-wise Average Runs Comparison")
avg = team_scores.dropna(subset=["Team", "Runs"]).groupby("Team")["Runs"].mean().sort_values().tail(15)
fig, ax = plt.subplots(figsize=(10, 7))
avg.plot(kind="barh", ax=ax)
ax.set(title="Team-wise Average Runs Comparison", xlabel="Average Runs per Match", ylabel="Team")
show_chart(fig)

# Graph 5
st.header("5. 📊 Average Team Scores Across Years")
yscores = pd.concat([
    filtered[["Year", "Total Score for Team 1"]].rename(columns={"Total Score for Team 1":"Runs"}),
    filtered[["Year", "Total Score for Team 2"]].rename(columns={"Total Score for Team 2":"Runs"})
], ignore_index=True)
yscores["Runs"] = pd.to_numeric(yscores["Runs"], errors="coerce")
avg_year = yscores.dropna(subset=["Year", "Runs"]).groupby("Year")["Runs"].mean().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
ax.fill_between(avg_year.index, avg_year.values, alpha=.4)
ax.plot(avg_year.index, avg_year.values, marker="o")
ax.set(title="Average Team Scores Across Years", xlabel="World Cup Year", ylabel="Average Team Runs")
ax.grid(True, alpha=.3)
show_chart(fig)

# Graph 6
st.header("6. 🥧 India's World Cup Match Outcome Distribution")
india_mask = filtered["Team 1"].map(lambda x: norm(x) in INDIA_NAMES) | filtered["Team 2"].map(lambda x: norm(x) in INDIA_NAMES)
india = filtered[india_mask].copy()
def india_result(row):
    winner = norm(row["Winner"])
    if winner in {"", "nan", "none", "no result", "no-result", "abandoned", "tied", "nr", "n/r"}:
        return "Other / No Result"
    if winner in INDIA_NAMES:
        return "Win"
    teams_in_match = {norm(row["Team 1"]), norm(row["Team 2"])}
    if winner in teams_in_match:
        return "Loss"
    return "Other / No Result"
if not india.empty:
    counts = india.apply(india_result, axis=1).value_counts().reindex(["Win", "Loss", "Other / No Result"], fill_value=0)
    counts = counts[counts > 0]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("India's World Cup Match Outcome Distribution")
    show_chart(fig)
else:
    st.info("India is not present in the selected matches. Change the team/year filters.")

# Graph 7
st.header("7. ⚡ Relationship Between Team 1 and Team 2 Scores")
score_pair = filtered[["Total Score for Team 1", "Total Score for Team 2"]].apply(pd.to_numeric, errors="coerce").dropna()
if not score_pair.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(score_pair["Total Score for Team 1"], score_pair["Total Score for Team 2"], alpha=.6)
    ax.set(title="Relationship Between Team 1 and Team 2 Scores", xlabel="Team 1 Runs", ylabel="Team 2 Runs")
    ax.grid(True, alpha=.3)
    show_chart(fig)
else:
    st.info("No complete score pairs are available.")

# Graph 8
st.header("8. 📉 Distribution of World Cup Team Scores")
runs = pd.concat([filtered["Total Score for Team 1"], filtered["Total Score for Team 2"]], ignore_index=True)
runs = pd.to_numeric(runs, errors="coerce").dropna()
if not runs.empty:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(runs, bins=15, edgecolor="black")
    ax.set(title="Distribution of World Cup Team Scores", xlabel="Total Runs", ylabel="Frequency")
    show_chart(fig)
else:
    st.info("No scores are available for the selected filters.")

# Graph 9
st.header("9. 🔥 Comparison of Team Score Distributions")
runs1 = pd.to_numeric(filtered["Total Score for Team 1"], errors="coerce").dropna()
runs2 = pd.to_numeric(filtered["Total Score for Team 2"], errors="coerce").dropna()
if not runs1.empty and not runs2.empty:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.violinplot([runs1.values, runs2.values], showmeans=True, showmedians=True)
    ax.set_xticks([1, 2], ["Team 1", "Team 2"])
    ax.set(title="Comparison of Team Score Distributions", xlabel="Team", ylabel="Total Runs")
    show_chart(fig)
else:
    st.info("Not enough score data for the violin plot.")

# Filtered table and download
st.divider()
st.header("📋 View Filtered Match Dataset")
st.dataframe(filtered, use_container_width=True, hide_index=True)
st.download_button(
    "⬇️ Download Filtered Dataset as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_world_cup_matches.csv",
    mime="text/csv"
)
st.caption("Cricket World Cup Analysis | Python • Pandas • Matplotlib • Streamlit")
