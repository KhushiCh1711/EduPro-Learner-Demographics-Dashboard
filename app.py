"""
EduPro Learner Demographics Dashboard
--------------------------------------
Analyzes the Users dataset (UserID, UserName, Age, Gender, Email) to answer:
  - What is the age distribution of learners on EduPro?
  - How is the platform split by gender?
  - How do age and gender intersect (age bands x gender)
  """

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="EduPro | Learner Demographics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "users.csv"

# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    bins = [0, 17, 25, 35, 45, 200]
    labels = ["<18", "18-25", "26-35", "36-45", "45+"]
    df["AgeGroup"] = pd.cut(df["Age"], bins=bins, labels=labels, right=True)

    return df


df = load_data(DATA_PATH)

# ----------------------------------------------------------------------------
# Sidebar - filters
# ----------------------------------------------------------------------------
st.sidebar.title("🎓 EduPro Analytics")
st.sidebar.caption("Learner Demographics Dashboard")
st.sidebar.markdown("---")

st.sidebar.subheader("Filters")

age_groups_available = [g for g in ["<18", "18-25", "26-35", "36-45", "45+"] if g in df["AgeGroup"].unique().tolist()]
selected_age_groups = st.sidebar.multiselect(
    "Age Group", options=age_groups_available, default=age_groups_available
)

genders_available = sorted(df["Gender"].dropna().unique().tolist())
selected_genders = st.sidebar.multiselect(
    "Gender", options=genders_available, default=genders_available
)

age_min, age_max = int(df["Age"].min()), int(df["Age"].max())
selected_age_range = st.sidebar.slider(
    "Exact Age Range", min_value=age_min, max_value=age_max, value=(age_min, age_max)
)

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About this dashboard", expanded=False):
    st.markdown(
        "This dashboard analyzes learner demographics on EduPro."
    )

# Apply filters
mask = (
    df["AgeGroup"].isin(selected_age_groups)
    & df["Gender"].isin(selected_genders)
    & df["Age"].between(selected_age_range[0], selected_age_range[1])
)
fdf = df[mask].copy()

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("🎓 EduPro Learner Demographics")
st.caption("Understanding who learns on EduPro — age, gender, and participation patterns")

if fdf.empty:
    st.warning("No users match the selected filters. Adjust filters in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)

total_users = len(fdf)
median_age = fdf["Age"].median()
female_pct = (fdf["Gender"].eq("Female").mean() * 100) if "Female" in fdf["Gender"].values else 0
male_pct = (fdf["Gender"].eq("Male").mean() * 100) if "Male" in fdf["Gender"].values else 0
top_age_group = fdf["AgeGroup"].value_counts().idxmax()

k1.metric("Total Learners", f"{total_users:,}")
k2.metric("Median Age", f"{median_age:.0f} yrs")
k3.metric("Female Share", f"{female_pct:.1f}%")
k4.metric("Male Share", f"{male_pct:.1f}%")
k5.metric("Largest Age Group", str(top_age_group))

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 1: Age distribution + Gender split
# ----------------------------------------------------------------------------
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Age Distribution")
    fig_age = px.histogram(
        fdf, x="Age", nbins=int(age_max - age_min + 1),
        color_discrete_sequence=["#6C5CE7"],
    )
    fig_age.update_layout(
        bargap=0.05, xaxis_title="Age", yaxis_title="Number of Learners",
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_age, use_container_width=True)

with c2:
    st.subheader("Gender Split")
    gender_counts = fdf["Gender"].value_counts().reset_index()
    gender_counts.columns = ["Gender", "Count"]
    fig_gender = px.pie(
        gender_counts, names="Gender", values="Count", hole=0.55,
        color="Gender",
        color_discrete_map={"Female": "#FD79A8", "Male": "#0984E3", "Other": "#00B894"},
    )
    fig_gender.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_gender, use_container_width=True)

# ----------------------------------------------------------------------------
# Row 2: Age group bar + Age group x Gender
# ----------------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Learners by Age Group")
    age_group_counts = (
        fdf["AgeGroup"].value_counts().reindex(age_groups_available).reset_index()
    )
    age_group_counts.columns = ["AgeGroup", "Count"]
    fig_ag = px.bar(
        age_group_counts, x="AgeGroup", y="Count", text="Count",
        color="AgeGroup", color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_ag.update_traces(textposition="outside")
    fig_ag.update_layout(showlegend=False, margin=dict(t=10, b=10), xaxis_title="Age Group", yaxis_title="Learners")
    st.plotly_chart(fig_ag, use_container_width=True)

with c4:
    st.subheader("Age Group × Gender")
    cross = pd.crosstab(fdf["AgeGroup"], fdf["Gender"]).reindex(age_groups_available)
    fig_cross = px.bar(
        cross, barmode="group",
        color_discrete_map={"Female": "#FD79A8", "Male": "#0984E3", "Other": "#00B894"},
    )
    fig_cross.update_layout(margin=dict(t=10, b=10), xaxis_title="Age Group", yaxis_title="Learners", legend_title="Gender")
    st.plotly_chart(fig_cross, use_container_width=True)

# ----------------------------------------------------------------------------
# Row 3: Heatmap-style table + raw data
# ----------------------------------------------------------------------------
st.subheader("Age Group × Gender — Density Heatmap")
heat = pd.crosstab(fdf["AgeGroup"], fdf["Gender"]).reindex(age_groups_available)
fig_heat = go.Figure(
    data=go.Heatmap(
        z=heat.values, x=heat.columns.tolist(), y=heat.index.astype(str).tolist(),
        colorscale="Purples", text=heat.values, texttemplate="%{text}",
    )
)
fig_heat.update_layout(margin=dict(t=10, b=10), xaxis_title="Gender", yaxis_title="Age Group")
st.plotly_chart(fig_heat, use_container_width=True)

with st.expander("📋 View filtered raw data"):
    st.dataframe(fdf[["UserID", "UserName", "Age", "AgeGroup", "Gender"]], use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="edupro_filtered_users.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(
    "EduPro Learner Demographics Dashboard · Built from Users data (3,000 records) · "
    "Enrollment & course-preference modules pending Courses/Transactions data."
)
