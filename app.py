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
    "This dashboard analyzes Cricket World Cup data "
    "using Python, Pandas, Matplotlib, and Streamlit."
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
df.columns = df.columns.str.strip()

# Remove completely empty rows
df = df.dropna(how="all")

# ---------------------------------
# DATASET INFORMATION
# ---------------------------------
st.header("📊 Dataset Overview")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Records", len(df))

with col2:
    st.metric("Total Columns", len(df.columns))

with st.expander("View Dataset"):
    st.dataframe(df, use_container_width=True)

with st.expander("View Column Information"):
    column_info = pd.DataFrame({
        "Column Name": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing Values": df.isna().sum().values
    })
    st.dataframe(column_info, use_container_width=True)

# ---------------------------------
# SIDEBAR FILTERS
# ---------------------------------
st.sidebar.header("🔎 Dashboard Filters")

filtered_df = df.copy()

# Allow filtering by a team or country column
team_candidates = [
    "team", "country", "winner", "batting_team",
    "Team", "Country", "Winner"
]

team_column = next(
    (col for col in team_candidates if col in df.columns),
    None
)

if team_column:
    teams = sorted(
        df[team_column].dropna().astype(str).unique().tolist()
    )

    selected_teams = st.sidebar.multiselect(
        "Select Team(s)",
        teams,
        default=teams
    )

    filtered_df = filtered_df[
        filtered_df[team_column].astype(str).isin(selected_teams)
    ]

# ---------------------------------
# AUTOMATIC NUMERIC COLUMN DETECTION
# ---------------------------------
numeric_columns = filtered_df.select_dtypes(
    include="number"
).columns.tolist()

if numeric_columns:
    st.header("📈 Statistical Summary")

    st.dataframe(
        filtered_df[numeric_columns].describe().round(2),
        use_container_width=True
    )

    # ---------------------------------
    # SELECT COLUMN FOR VISUALIZATION
    # ---------------------------------
    st.header("📊 Interactive Data Visualization")

    selected_column = st.selectbox(
        "Choose a numerical column to visualize",
        numeric_columns
    )

    chart_type = st.radio(
        "Select Chart Type",
        ["Histogram", "Bar Chart", "Box Plot"],
        horizontal=True
    )

    if chart_type == "Histogram":
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.hist(
            filtered_df[selected_column].dropna(),
            bins=15,
            edgecolor="black"
        )

        ax.set_title(f"Distribution of {selected_column}")
        ax.set_xlabel(selected_column)
        ax.set_ylabel("Frequency")

        st.pyplot(fig)
        plt.close(fig)

    elif chart_type == "Bar Chart":
        chart_data = filtered_df[selected_column].dropna()

        if len(chart_data) > 30:
            chart_data = chart_data.head(30)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.bar(
            range(len(chart_data)),
            chart_data.values
        )

        ax.set_title(f"{selected_column} by Record")
        ax.set_xlabel("Record Index")
        ax.set_ylabel(selected_column)

        st.pyplot(fig)
        plt.close(fig)

    elif chart_type == "Box Plot":
        fig, ax = plt.subplots(figsize=(8, 4))

        ax.boxplot(
            filtered_df[selected_column].dropna()
        )

        ax.set_title(f"Box Plot of {selected_column}")
        ax.set_ylabel(selected_column)

        st.pyplot(fig)
        plt.close(fig)

else:
    st.warning(
        "No numerical columns were detected. "
        "Check the dataset format and column data types."
    )

# ---------------------------------
# TEAM-WISE ANALYSIS
# ---------------------------------
if team_column and numeric_columns:
    st.header("🏆 Team Performance Analysis")

    selected_metric = st.selectbox(
        "Select a metric for team comparison",
        numeric_columns,
        key="team_metric"
    )

    team_summary = (
        filtered_df.groupby(team_column)[selected_metric]
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    if not team_summary.empty:
        st.bar_chart(team_summary)

        st.write("### Team Statistics")
        st.dataframe(
            team_summary.rename(
                "Average " + selected_metric
            ).reset_index(),
            use_container_width=True
        )
    else:
        st.info("No team statistics are available for this selection.")

# ---------------------------------
# FOOTER
# ---------------------------------
st.divider()

st.caption(
    "Cricket World Cup Analysis | "
    "Developed using Python, Pandas, Matplotlib, and Streamlit"
)

st.success("Dashboard loaded successfully!")