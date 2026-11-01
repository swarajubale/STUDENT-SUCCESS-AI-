import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import load_student_data
from src.analytics import generate_analytics
from src.recommendations import generate_recommendations


# Page configuration
st.set_page_config(
    page_title="Student Success AI",
    page_icon="🎓",
    layout="wide"
)

# Load and process data
data = load_student_data()
data = generate_analytics(data)
data = generate_recommendations(data)

# Dashboard heading
st.title("🎓 Student Success AI")
st.subheader("Your Personal Academic Progress Dashboard")

# Student selection
students = sorted(data["student_id"].unique())

selected_student = st.selectbox(
    "Select Student",
    students
)

student_data = data[data["student_id"] == selected_student]

# Key metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Average Attendance",
        f"{student_data['attendance_percentage'].mean():.1f}%"
    )

with col2:
    st.metric(
        "Assignment Completion",
        f"{student_data['assignment_percentage'].mean():.1f}%"
    )

with col3:
    st.metric(
        "Overall Performance",
        f"{student_data['overall_performance'].mean():.1f}%"
    )

st.divider()

# Subject performance chart
st.subheader("📊 Subject-wise Academic Performance")

fig = px.bar(
    student_data,
    x="subject",
    y="overall_performance",
    color="subject",
    title="Performance by Subject",
    range_y=[0, 100]
)

st.plotly_chart(fig, use_container_width=True)

# Attendance chart
st.subheader("📅 Attendance Analysis")

attendance_fig = px.bar(
    student_data,
    x="subject",
    y="attendance_percentage",
    color="subject",
    range_y=[0, 100]
)

st.plotly_chart(attendance_fig, use_container_width=True)

# Recommendations
st.subheader("💡 Your Personal Recommendations")

for _, row in student_data.iterrows():
    with st.expander(f"{row['subject']}"):
        st.write(row["recommendations"])

st.success("Your academic dashboard is ready!")


