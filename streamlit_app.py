import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------
st.set_page_config(
    page_title="Cricket World Cup Analysis",
    page_icon="🏏",
    layout="wide"
)

# ---------------------------------
# TITLE
# ---------------------------------
st.title("🏏 Cricket World Cup Analysis")
st.subheader("Data Visualization and Team Performance Dashboard")

st.write(
    "Explore Cricket World Cup data using one team filter. "
    "All statistics, tables, and graphs update together."
)

# ---------------------------------
# LOAD DATASET
# ---------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("world_cup_score.csv")

try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Dataset not found! Keep world_cup_score.csv "
        "in the same folder as app.py."
    )
    st.stop()

# ---------------------------------
# DATA CLEANING
# ---------------------------------
df.columns = df.columns.astype(str).str.strip()
df = df.dropna(how="all")

if df.empty:
    st.warning("The dataset contains no records.")
    st.stop()

# ---------------------------------
# FIND TEAM COLUMN
# ---------------------------------
team_candidates = [
    "team", "country", "winner", "batting_team",
    "Team", "Country", "Winner", "Batting Team",
    "Team Name", "team_name"
]

team_column = next(
    (
        col for col in team_candidates
        if col in df.columns
    ),
    None
)

# ---------------------------------
# SINGLE GLOBAL TEAM FILTER
# ---------------------------------
st.sidebar.header("🔎 Dashboard Filter")

filtered_df = df.copy()

if team_column:
    teams = sorted(
        df[team_column].dropna().astype(str).unique().tolist()
    )

    selected_teams = st.sidebar.multiselect(
        "Select Team(s)",
        teams,
        default=teams,
        help="This filter updates all dashboard sections."
    )

    filtered_df = df[
        df[team_column].astype(str).isin(selected_teams)
    ].copy()

    if not selected_teams:
        st.warning("Select at least one team to view the dashboard.")
        st.stop()
else:
    st.sidebar.info(
        "No recognized team column was found. "
        "Showing all records."
    )

# ---------------------------------
# DATASET OVERVIEW
# ---------------------------------
st.header("📊 Dataset Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Filtered Records", len(filtered_df))

with col2:
    st.metric("Total Columns", len(filtered_df.columns))

with col3:
    st.metric(
        "Teams Selected",
        filtered_df[team_column].nunique()
        if team_column else 0
    )

with st.expander("View Filtered Dataset"):
    st.dataframe(filtered_df, use_container_width=True)

with st.expander("View Column Information"):
    column_info = pd.DataFrame({
        "Column Name": filtered_df.columns,
        "Data Type": filtered_df.dtypes.astype(str).values,
        "Missing Values": filtered_df.isna().sum().values
    })

    st.dataframe(column_info, use_container_width=True)

# ---------------------------------
# NUMERIC COLUMNS
# ---------------------------------
numeric_columns = filtered_df.select_dtypes(
    include="number"
).columns.tolist()

if numeric_columns and not filtered_df.empty:

    # ---------------------------------
    # STATISTICAL SUMMARY
    # ---------------------------------
    st.header("📈 Statistical Summary")

    st.dataframe(
        filtered_df[numeric_columns].describe().round(2),
        use_container_width=True
    )

    # ---------------------------------
    # GRAPHS DISPLAYED TOGETHER
    # ---------------------------------
    st.header("📊 Interactive Data Visualizations")

    selected_column = numeric_columns[0]

    if len(numeric_columns) > 1:
        selected_column = st.selectbox(
            "Choose a numerical column for the graphs",
            numeric_columns
        )

    chart_data = filtered_df[selected_column].dropna()

    if not chart_data.empty:

        col1, col2 = st.columns(2)

        # HISTOGRAM
        with col1:
            st.subheader("📉 Distribution")

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.hist(
                chart_data,
                bins=15,
                edgecolor="black"
            )
            ax.set_title(f"Distribution of {selected_column}")
            ax.set_xlabel(selected_column)
            ax.set_ylabel("Frequency")
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

        # BAR CHART
        with col2:
            st.subheader("📊 Record-wise Comparison")

            bar_data = chart_data.head(30)

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(
                range(len(bar_data)),
                bar_data.values
            )
            ax.set_title(f"{selected_column} by Record")
            ax.set_xlabel("Record Index")
            ax.set_ylabel(selected_column)
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

        # BOX PLOT
        st.subheader("📦 Spread and Outliers")

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.boxplot(chart_data)
        ax.set_title(f"Box Plot of {selected_column}")
        ax.set_ylabel(selected_column)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("No numerical values are available for these selections.")

else:
    st.warning(
        "No numerical columns or records are available "
        "for the current selection."
    )

# ---------------------------------
# TEAM PERFORMANCE ANALYSIS
# ---------------------------------
if team_column and numeric_columns and not filtered_df.empty:

    st.header("🏆 Team Performance Analysis")

    # Calculate the mean of each numerical metric per team
    team_summary = (
        filtered_df.groupby(team_column)[numeric_columns]
        .mean()
        .round(2)
    )

    # Show all numerical metrics together
    st.subheader("Average Statistics by Team")
    st.dataframe(team_summary, use_container_width=True)

    # Plot the first available numeric metric
    metric = numeric_columns[0]

    plot_data = team_summary[metric].dropna().sort_values(
        ascending=False
    )

    if not plot_data.empty:
        st.subheader(f"Team Comparison: Average {metric}")
        st.bar_chart(plot_data)

# ---------------------------------
# FOOTER
# ---------------------------------
st.divider()

st.caption(
    "Cricket World Cup Analysis | "
    "Developed using Python, Pandas, Matplotlib, and Streamlit"
)

st.success("Dashboard loaded successfully!")