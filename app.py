
from plotly import data
import streamlit as st
import pandas as pd
import plotly.express as px

from database import (
    initialize_database,
    register_student,
    authenticate_student,
    get_student_records,
    add_student_record,
    get_student_history,
    update_student_record,
    delete_student_record,
    get_archived_student_records,
    restore_student_record,
    get_student_profile,
    update_student_profile
)
from src.analytics import generate_analytics
from src.recommendations import generate_recommendations
from src.intelligence import (
    generate_student_intelligence,
    get_intelligence_summary
)
from src.study_planner import (
    generate_study_plan,
    generate_weekly_timetable
)


st.set_page_config(
    page_title="Student Success AI",
    page_icon="🎓",
    layout="wide"
)

initialize_database()

# Session authentication state
if "student" not in st.session_state:
    st.session_state.student = None


def show_login():

    st.title("🎓 Student Success AI")
    st.subheader("Your Personal Academic Intelligence Platform")

    login_tab, register_tab = st.tabs(
        ["Login", "Create Student Account"]
    )

    with login_tab:

        st.subheader("Welcome Back")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", use_container_width=True):

            student = authenticate_student(username, password)

            if student:
                st.session_state.student = student
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with register_tab:

        st.subheader("Create Your Student Account")

        full_name = st.text_input("Full Name")
        new_username = st.text_input("Choose Username")
        new_password = st.text_input(
            "Create Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        st.caption("Academic details are optional and can be edited later.")
        institution = st.text_input("Institution / University")
        course_name = st.text_input("Course / Degree")
        department = st.text_input("Department")
        current_semester = st.text_input("Current Semester / Year")
        academic_year = st.text_input("Academic Year (e.g. 2026-27)")

        if st.button("Create Account", use_container_width=True):

            if new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                try:
                    student_id = register_student(
                        full_name,
                        new_username,
                        new_password,
                        institution,
                        course_name,
                        department,
                        current_semester,
                        academic_year
                    )

                    st.success(
                        f"Account created! Your Student ID is {student_id}"
                    )

                    st.info("Please log in using your username and password.")

                except ValueError as error:
                    st.error(str(error))


def show_dashboard(student):

    st.title("🎓 Student Success AI")

    st.write(f"Welcome, {student['full_name']}!")

    st.caption(f"Student ID: {student['student_id']}")

    if st.button("Logout"):
        st.session_state.student = None
        st.rerun()

    # Student profile: editable academic identity details.
    profile = get_student_profile(student["student_id"])

    st.divider()
    st.subheader("👤 Student Profile")

    with st.expander("View / Edit Student Profile", expanded=True):
        with st.form("student_profile_form"):
            profile_name = st.text_input(
                "Full Name", value=profile["full_name"]
            )
            profile_institution = st.text_input(
                "Institution / University", value=profile["institution"]
            )
            profile_course = st.text_input(
                "Course / Degree", value=profile["course_name"]
            )
            profile_department = st.text_input(
                "Department", value=profile["department"]
            )
            profile_semester = st.text_input(
                "Current Semester / Year", value=profile["current_semester"]
            )
            profile_academic_year = st.text_input(
                "Academic Year", value=profile["academic_year"]
            )

            profile_submitted = st.form_submit_button("Save Profile")

            if profile_submitted:
                try:
                    message = update_student_profile(
                        student["student_id"],
                        profile_name,
                        profile_institution,
                        profile_course,
                        profile_department,
                        profile_semester,
                        profile_academic_year
                    )
                    st.session_state.student = get_student_profile(
                        student["student_id"]
                    )
                    st.success(message)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    # Fetch only authenticated student's records
    records = get_student_records(student["student_id"])

    with st.expander("➕ Add Academic Record"):

        with st.form("academic_record_form"):

            subject = st.text_input("Subject Name")

            col1, col2 = st.columns(2)

            with col1:
                 classes_held = st.number_input("Classes Held", min_value=1, step=1)
                 assignments_total = st.number_input("Total Assignments", min_value=0, step=1)
                 quiz_average = st.number_input("Quiz Average (%)", min_value=0.0, max_value=100.0)

            with col2:
                 classes_attended = st.number_input("Classes Attended", min_value=0, step=1)
                 assignments_submitted = st.number_input("Assignments Submitted", min_value=0, step=1)
                 exam_score = st.number_input("Exam Score (%)", min_value=0.0, max_value=100.0)

            study_hours_weekly = st.number_input("Study Hours Per Week", min_value=0.0)                         
            submitted = st.form_submit_button("Save Academic Record")

            if submitted:

                if not subject.strip():
                    st.error("Please enter a subject name.")

                elif classes_attended > classes_held:
                    st.error("Classes attended cannot exceed classes held.")

                elif assignments_submitted > assignments_total:
                    st.error("Submitted assignments cannot exceed total assignments.")

                else:
                    add_student_record(
                    student["student_id"],
                    subject.strip(),
                    int(classes_held),
                    int(classes_attended),
                    int(assignments_total),
                    int(assignments_submitted),
                    quiz_average,
                    exam_score,
                    study_hours_weekly
                )

                    st.success("Academic record saved!")
                    st.rerun()
    if not records:
        st.info(
            "Your account is ready! Your academic records "
            "will appear here once they are added."
        )
        return

    columns = [
    "record_id",
    "student_id",
    "subject",
    "classes_held",
    "classes_attended",
    "assignments_total",
    "assignments_submitted",
    "quiz_average",
    "exam_score",
    "study_hours_weekly",
    "is_archived"
]

    data = pd.DataFrame(records, columns=columns)

    history = get_student_history(student["student_id"])

    data = generate_analytics(data, history=history)
    data = generate_student_intelligence(data)
    data = generate_recommendations(data)
    study_plan = generate_study_plan(data)
    weekly_timetable = generate_weekly_timetable(study_plan)


    st.divider()

    st.subheader("📈 Academic Progress History")

    if history:
        history_columns = [
            "subject",
            "classes_attended",
            "classes_held",
            "assignments_submitted",
            "assignments_total",
            "quiz_average",
            "exam_score",
            "study_hours_weekly",
            "recorded_at"
        ]

        history_data = pd.DataFrame(
            history,
            columns=history_columns
        )

        for subject in history_data["subject"].unique():

            subject_history = history_data[
                history_data["subject"] == subject
            ].copy()

            st.write(f"**{subject}**")

            fig = px.line(
                subject_history,
                x="recorded_at",
                y="exam_score",
                markers=True,
                title=f"{subject} - Exam Score Progress"
            )

            fig.update_yaxes(range=[0, 100])

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No academic history available yet.")

    st.subheader("Your Academic Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Average Attendance",
            f"{data['attendance_percentage'].mean():.1f}%"
        )

    with col2:
        st.metric(
            "Assignment Completion",
            f"{data['assignment_percentage'].mean():.1f}%"
        )

    with col3:
        st.metric(
            "Overall Performance",
            f"{data['overall_performance'].mean():.1f}%"
        )

    st.divider()

    st.subheader("📊 Subject Performance")

    fig = px.bar(
        data,
        x="subject",
        y="overall_performance",
        color="subject",
        range_y=[0, 100]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Attendance Analysis")

    attendance_fig = px.bar(
        data,
        x="subject",
        y="attendance_percentage",
        color="subject",
        range_y=[0, 100]
    )

    st.plotly_chart(attendance_fig, use_container_width=True)
    st.divider()

    st.subheader("🚦 Subject Risk Classification")

    for _, row in data.iterrows():
        with st.expander(
            f"{row['subject']} — {row['risk_level']} Risk"
        ):
            st.write(f"**Risk Level:** {row['risk_level']}")
            st.write(f"**Reason:** {row['risk_reasons']}")
            st.write(f"**Performance Trend:** {row['performance_trend']}")

            if pd.notna(row["performance_change"]):
                st.write(
                    f"**Performance Change:** "
                    f"{row['performance_change']:+.1f} percentage points"
                )

    st.divider()
    st.subheader("🧠 Student Performance Intelligence")

    intelligence_summary = get_intelligence_summary(data)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Strongest Subject",
            intelligence_summary["strongest_subject"] or "N/A"
        )

    with col2:
        st.metric(
            "Weakest Subject",
            intelligence_summary["weakest_subject"] or "N/A"
        )

    with col3:
        st.metric(
            "Needs Attention First",
            intelligence_summary["top_priority_subject"] or "N/A"
        )

    with col4:
        st.metric(
            "Subjects Needing Attention",
            intelligence_summary["subjects_needing_attention"]
        )

    st.divider()
    st.subheader("🎯 Subject Priority Ranking")

    priority_data = data.sort_values(
        "priority_rank",
        ascending=True
    )

    for _, row in priority_data.iterrows():

        with st.expander(
            f"#{row['priority_rank']} — {row['subject']} | "
            f"{row['priority_level']} Priority"
        ):
            st.metric(
    "Priority Score",
    (
        f"{row['priority_score']:.1f}/100"
        if pd.notna(row["priority_score"])
        else "N/A"
    )
)

            st.write(
                f"**Priority Level:** {row['priority_level']}"
            )

            st.write(
                f"**Why this subject needs attention:** "
                f"{row['priority_reasons']}"
            )
    st.divider()
    st.subheader("📚 Smart Weekly Study Planner")
    st.caption("Recommended study hours based on your subject priorities.")

    planner_display = study_plan[
        [
            "subject",
            "study_hours_weekly",
            "recommended_study_hours",
            "hours_change",
            "allocation_reason"
        ]
    ].rename(columns={
        "subject": "Subject",
        "study_hours_weekly": "Current Hours",
        "recommended_study_hours": "Recommended Hours",
        "hours_change": "Change",
        "allocation_reason": "Why This Allocation?"
    })

    st.dataframe(
        planner_display,
        hide_index=True,
        use_container_width=True
    )

    st.subheader("🗓️ Your Weekly Timetable")

    for day in [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]:
        day_plan = weekly_timetable[
            weekly_timetable["Day"] == day
        ]

        with st.expander(day):
            st.dataframe(
                day_plan[
                    ["Subject", "Activity", "Duration (hours)"]
                ],
                hide_index=True,
                use_container_width=True
            )
    st.dataframe(
        planner_display,
        hide_index=True,
        use_container_width=True
    )    
    st.subheader("💡 Your Personal Recommendations")

    for _, row in data.iterrows():

        with st.expander(row["subject"]):

            st.write(row["recommendations"])

    st.divider()

    st.subheader("📅 Weekly Academic Action Plan")
    st.caption("Your subject-wise targets for this week.")

    for _, row in data.iterrows():

        with st.expander(
            f"{row['subject']} — {row['priority_level']} Priority"
        ):
       
            st.metric(
    "Priority Score",
    (
        f"{row['priority_score']:.1f}/100"
        if pd.notna(row["priority_score"])
        else "N/A"
    )
)

            st.markdown("### 🎯 This Week's Tasks")

            for task in row["weekly_action_plan"]:
                st.markdown(f"- {task}")

            st.divider()

        st.subheader("Edit Academic Information")

        with st.form(key=f"edit_form_{row['record_id']}"):

            classes_held = st.number_input(
                "Classes Held",
                min_value=1,
                value=int(row["classes_held"])
            )

            classes_attended = st.number_input(
                "Classes Attended",
                min_value=0,
                value=int(row["classes_attended"])
            )

            assignments_total = st.number_input(
                "Total Assignments",
                min_value=1,
                value=int(row["assignments_total"])
            )

            assignments_submitted = st.number_input(
                "Assignments Submitted",
                min_value=0,
                value=int(row["assignments_submitted"])
            )

            quiz_average = st.number_input(
                "Quiz Average",
                min_value=0.0,
                max_value=100.0,
                value=float(row["quiz_average"])
            )

            exam_score = st.number_input(
                "Exam Score",
                min_value=0.0,
                max_value=100.0,
                value=float(row["exam_score"])
            )

            study_hours_weekly = st.number_input(
                "Weekly Study Hours",
                min_value=0.0,
                value=float(row["study_hours_weekly"])
            )

            submitted = st.form_submit_button("Update Record")

            if submitted:

                if classes_attended > classes_held:
                    st.error("Attendance cannot exceed classes held.")

                elif assignments_submitted > assignments_total:
                    st.error("Submitted assignments cannot exceed total assignments.")

                else:
                    result = update_student_record(
                        row["record_id"],
                        student["student_id"],
                        row["subject"],
                        int(classes_held),
                        int(classes_attended),
                        int(assignments_total),
                        int(assignments_submitted),
                        quiz_average,
                        exam_score,
                        study_hours_weekly
                    )

                    st.success(result)
                    st.rerun()
            st.divider()

        st.subheader("Delete Academic Record")

        confirm_delete = st.checkbox(
            f"I confirm deleting {row['subject']}",
            key=f"confirm_delete_{row['record_id']}"
        )

        if st.button(
            "Delete Subject",
            key=f"delete_{row['record_id']}"
        ):
            if confirm_delete:
                result = delete_student_record(
                    row["record_id"],
                    student["student_id"]
                )
                st.success(result)
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

    st.divider()
    st.subheader("📦 Archived Academic Records")

    archived_records = get_archived_student_records(
        student["student_id"]
    )

    if archived_records:
        for record in archived_records:

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{record[2]}**")

            with col2:
                if st.button(
                    "Restore",
                    key=f"restore_{record[0]}"
                ):
                    result = restore_student_record(
                        record[0],
                        student["student_id"]
                    )
                    st.success(result)
                    st.rerun()
    else:
        st.info("No archived records found.")        
    st.success("Your academic dashboard is ready!")


# Application entry point
if st.session_state.student is None:
    show_login()

else:
    show_dashboard(st.session_state.student)

