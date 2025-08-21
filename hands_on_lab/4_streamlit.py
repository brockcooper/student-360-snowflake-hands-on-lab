import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Optional

# In Snowflake-hosted Streamlit, use the active Snowpark session
from snowflake.snowpark.context import get_active_session


session = get_active_session()

DB = "STUDENT_DATA_WAREHOUSE"


@st.cache_data(ttl=300)
def run_df(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


def sql_literal(value: str) -> str:
    """Safely wrap a Python string as a single-quoted SQL literal."""
    return "'" + value.replace("'", "''") + "'"


@st.cache_data(ttl=300)
def get_terms() -> pd.DataFrame:
    return run_df(
        f"""
        SELECT TERM_ID, TERM_NAME, START_DATE
        FROM {DB}.DIM.TERM
        ORDER BY START_DATE DESC
        """
    )


@st.cache_data(ttl=300)
def get_programs_for_term(term_id: str) -> pd.DataFrame:
    return run_df(
        f"""
        SELECT DISTINCT PROGRAM, MAJOR
        FROM {DB}.REPORTS.STUDENT_TERM_SUMMARY
        WHERE TERM_ID = '{term_id}'
        ORDER BY PROGRAM, MAJOR
        """
    )


def build_filter_clause(
    term_id: str,
    programs: List[str],
    majors: List[str],
    student_search: Optional[str],
) -> str:
    clauses = [f"TERM_ID = '{term_id}'"]
    if programs:
        prog_list = ",".join(sql_literal(p) for p in programs)
        clauses.append(f"PROGRAM IN ({prog_list})")
    if majors:
        maj_list = ",".join(sql_literal(m) for m in majors)
        clauses.append(f"MAJOR IN ({maj_list})")
    if student_search:
        s = student_search.strip()
        if s.isdigit():
            clauses.append(f"STUDENT_ID = {int(s)}")
        else:
            like = s.replace("'", "''")
            clauses.append(f"(UPPER(FIRST_NAME) LIKE UPPER('%{like}%') OR UPPER(LAST_NAME) LIKE UPPER('%{like}%'))")
    return " AND ".join(clauses)


st.set_page_config(page_title="Student 360", layout="wide")
st.title("Student 360 Dashboard")

# Sidebar filters
terms_df = get_terms()
if terms_df.empty:
    st.warning("No terms found. Run setup scripts first.")
    st.stop()

default_term = terms_df.iloc[0]
term_label = st.sidebar.selectbox(
    "Term",
    options=terms_df["TERM_ID"].tolist(),
    format_func=lambda tid: f"{tid} – " + terms_df.set_index("TERM_ID").loc[tid, "TERM_NAME"],
    index=0,
)

programs_df = get_programs_for_term(term_label)
programs = sorted([p for p in programs_df["PROGRAM"].dropna().unique().tolist() if p])
majors = sorted([m for m in programs_df["MAJOR"].dropna().unique().tolist() if m])

sel_programs = st.sidebar.multiselect("Program", options=programs, default=[])
sel_majors = st.sidebar.multiselect("Major", options=majors, default=[])
student_search = st.sidebar.text_input("Search student (ID or name)")

st.sidebar.markdown("---")
st.sidebar.subheader("Risk filters")
flt_low_eng = st.sidebar.checkbox("Low engagement")
flt_high_bal = st.sidebar.checkbox("High balance")
flt_low_gpa = st.sidebar.checkbox("Low prior GPA")
flt_no_adv = st.sidebar.checkbox("No advising")

where_sts = build_filter_clause(term_label, sel_programs, sel_majors, student_search)

# KPI row from StudentTermSummary
kpi_sql = f"""
SELECT
  COUNT(DISTINCT STUDENT_ID) AS HEADCOUNT,
  AVG(TOTAL_UNITS) AS AVG_UNITS,
  AVG(NUM_COURSES) AS AVG_COURSES,
  AVG(ENGAGEMENT_EVENTS_TTD) AS AVG_EVENTS,
  AVG(IFF(BALANCE > 0, 1, 0)) AS BALANCE_RATE,
  AVG(IFF(NVL(ADVISING_APPOINTMENTS_COUNT,0) > 0, 1, 0)) AS ADVISING_RATE
FROM {DB}.REPORTS.STUDENT_TERM_SUMMARY
WHERE {where_sts}
"""

kpi = run_df(kpi_sql).iloc[0]

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Headcount", f"{int(kpi.HEADCOUNT):,}")
col2.metric("Avg Units", f"{kpi.AVG_UNITS:.1f}")
col3.metric("Avg Courses", f"{kpi.AVG_COURSES:.1f}")
col4.metric("Avg Engagement", f"{kpi.AVG_EVENTS:.0f}")
col5.metric("Balance Rate", f"{kpi.BALANCE_RATE*100:.0f}%")
col6.metric("Advising Rate", f"{kpi.ADVISING_RATE*100:.0f}%")

st.markdown("---")

# Tabs for overview, courses, risk
tab_overview, tab_courses, tab_risk = st.tabs(["Overview", "Courses", "Risk"])

with tab_overview:
    # Cohort summary table
    sts_sql = f"""
    SELECT
      STUDENT_ID, FIRST_NAME, LAST_NAME, PROGRAM, MAJOR,
      NUM_COURSES, TOTAL_UNITS, PRIOR_TERM_GPA, ENGAGEMENT_EVENTS_TTD,
      TOTAL_CHARGES, TOTAL_PAYMENTS, BALANCE, ADVISING_APPOINTMENTS_COUNT, LAST_ADVISING_DT
    FROM {DB}.REPORTS.STUDENT_TERM_SUMMARY
    WHERE {where_sts}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY STUDENT_ID ORDER BY TERM_ID DESC) = 1
    LIMIT 1000
    """
    sts_df = run_df(sts_sql)
    st.subheader("Cohort summary")
    st.dataframe(sts_df, use_container_width=True, hide_index=True)

    # Visual: Headcount by major (full width)
    st.caption("Headcount by major")
    prog_sql = f"""
    SELECT MAJOR, SUM(HEADCOUNT) AS HEADCOUNT
    FROM {DB}.REPORTS.PROGRAM_COHORT_OVERVIEW
    WHERE TERM_ID = '{term_label}' AND MAJOR IS NOT NULL
    GROUP BY MAJOR
    ORDER BY HEADCOUNT DESC
    LIMIT 20
    """
    prog_df = run_df(prog_sql)
    if not prog_df.empty:
        chart = (
            alt.Chart(prog_df)
            .mark_bar()
            .encode(
                x=alt.X("HEADCOUNT:Q", title="Headcount"),
                y=alt.Y("MAJOR:N", sort='-x', title="Major"),
                tooltip=["MAJOR", "HEADCOUNT"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No major data.")

    # Quick cohort metrics row
    if not sts_df.empty:
        med_gpa = float(sts_df["PRIOR_TERM_GPA"].median(skipna=True)) if "PRIOR_TERM_GPA" in sts_df else float("nan")
        med_bal = float(sts_df["BALANCE"].median(skipna=True)) if "BALANCE" in sts_df else float("nan")
        advising_rate = (sts_df["ADVISING_APPOINTMENTS_COUNT"].fillna(0) > 0).mean() if "ADVISING_APPOINTMENTS_COUNT" in sts_df else float("nan")
        m1, m2, m3 = st.columns(3)
        m1.metric("Median prior GPA", f"{med_gpa:.2f}" if med_gpa==med_gpa else "-")
        m2.metric("Median balance", f"${med_bal:,.0f}" if med_bal==med_bal else "-")
        m3.metric("Advising rate", f"{advising_rate*100:.0f}%" if advising_rate==advising_rate else "-")
    # GPA by major (average prior GPA)
    maj_sql = f"""
    SELECT MAJOR, AVG(PRIOR_TERM_GPA) AS AVG_PRIOR_GPA
    FROM {DB}.REPORTS.STUDENT_TERM_SUMMARY
    WHERE {where_sts} AND MAJOR IS NOT NULL AND PRIOR_TERM_GPA IS NOT NULL
    GROUP BY MAJOR
    ORDER BY AVG_PRIOR_GPA DESC
    LIMIT 20
    """
    maj_df = run_df(maj_sql)
    if not maj_df.empty:
        chart_major = (
            alt.Chart(maj_df)
            .mark_bar()
            .encode(
                x=alt.X("AVG_PRIOR_GPA:Q", title="Average prior GPA"),
                y=alt.Y("MAJOR:N", sort='-x', title="Major"),
                tooltip=["MAJOR", alt.Tooltip("AVG_PRIOR_GPA:Q", format=".2f", title="Avg prior GPA")],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_major, use_container_width=True)
    
    # Balance distribution to bottom
    st.caption("Balance distribution (filtered cohort)")
    if not sts_df.empty and "BALANCE" in sts_df.columns:
        chart_bal = (
            alt.Chart(sts_df)
            .mark_bar()
            .encode(
                x=alt.X("BALANCE:Q", bin=alt.Bin(maxbins=30), title="Balance ($)"),
                y=alt.Y("count()", title="Students"),
            )
            .properties(height=280)
        )
        st.altair_chart(chart_bal, use_container_width=True)

with tab_courses:
    # Course section summary for the term
    sec_sql = f"""
    SELECT *
    FROM {DB}.REPORTS.COURSE_SECTION_SUMMARY
    WHERE TERM_ID = '{term_label}'
    ORDER BY EVENTS_PER_STUDENT DESC NULLS LAST
    LIMIT 500
    """
    sec_df = run_df(sec_sql)
    st.subheader("Course sections (by engagement)")
    st.dataframe(sec_df, use_container_width=True, hide_index=True)

    # Visual 1: Students by subject and modality (grouped bar)
    st.caption("Students by subject and modality")
    enroll_by_subject_sql = f"""
    WITH sub AS (
      SELECT s.SUBJECT, s.MODALITY, COUNT(DISTINCT e.STUDENT_ID) AS STUDENTS
      FROM {DB}.FACT.ENROLLMENT e
      JOIN {DB}.DIM.SECTION s ON s.COURSE_SECTION_ID = e.COURSE_SECTION_ID
      WHERE s.TERM_ID = '{term_label}'
      GROUP BY s.SUBJECT, s.MODALITY
    )
    SELECT SUBJECT, MODALITY, STUDENTS
    FROM sub
    """
    enroll_by_subject_df = run_df(enroll_by_subject_sql)
    if not enroll_by_subject_df.empty:
        # keep top 15 subjects by total students
        totals = enroll_by_subject_df.groupby("SUBJECT")["STUDENTS"].sum().sort_values(ascending=False)
        top_subjects = totals.head(15).index.tolist()
        df_plot = enroll_by_subject_df[enroll_by_subject_df["SUBJECT"].isin(top_subjects)]
        chart_mod_units = (
            alt.Chart(df_plot)
            .mark_bar()
            .encode(
                x=alt.X("STUDENTS:Q", title="Students"),
                y=alt.Y("SUBJECT:N", sort='-x', title="Subject"),
                color=alt.Color("MODALITY:N", title="Modality"),
                tooltip=["SUBJECT", "MODALITY", "STUDENTS"],
            )
            .properties(height=400)
        )
        st.altair_chart(chart_mod_units, use_container_width=True)
    else:
        st.info("No enrollment data available for subject/modality chart.")

    # Additional course metrics
    if not sec_df.empty:
        tsec = int(sec_df.shape[0])
        avg_ev = float(sec_df["EVENTS_PER_STUDENT"].mean(skipna=True)) if "EVENTS_PER_STUDENT" in sec_df else float("nan")
        avg_comp = float(sec_df["COMPLETION_RATE"].mean(skipna=True)) if "COMPLETION_RATE" in sec_df else float("nan")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total sections", f"{tsec:,}")
        k2.metric("Avg engagement events total per student", f"{avg_ev:.1f}" if avg_ev==avg_ev else "-")
        k3.metric("Avg completion rate", f"{avg_comp*100:.0f}%" if avg_comp==avg_comp else "-")

        # Modality distribution
        st.caption("Modality distribution")
        mod_df = sec_df.groupby("MODALITY").size().reset_index(name="COUNT")
        chart_mod = (
            alt.Chart(mod_df)
            .mark_bar()
            .encode(
                x=alt.X("COUNT:Q", title="Sections"),
                y=alt.Y("MODALITY:N", sort='-x', title="Modality"),
                tooltip=["MODALITY", "COUNT"],
            )
            .properties(height=280)
        )
        st.altair_chart(chart_mod, use_container_width=True)
    else:
        st.info("No course section data.")

with tab_risk:
    risk_where = [f"TERM_ID = '{term_label}'"]
    if flt_low_eng:
        risk_where.append("LOW_ENGAGEMENT = 1")
    if flt_high_bal:
        risk_where.append("HIGH_BALANCE = 1")
    if flt_low_gpa:
        risk_where.append("LOW_PRIOR_GPA = 1")
    if flt_no_adv:
        risk_where.append("NO_ADVISING = 1")
    risk_clause = " AND ".join(risk_where)

    risk_sql = f"""
    SELECT *
    FROM {DB}.REPORTS.AT_RISK_STUDENTS
    WHERE {risk_clause}
    ORDER BY STUDENT_ID
    LIMIT 1000
    """
    risk_df = run_df(risk_sql)
    st.subheader("At-risk students")
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

    if not risk_df.empty:
        # Risk KPIs
        at_risk_count = int(risk_df.shape[0])
        cohort_sql = f"SELECT COUNT(DISTINCT STUDENT_ID) AS HEADCOUNT FROM {DB}.REPORTS.STUDENT_TERM_SUMMARY WHERE TERM_ID = '{term_label}'"
        cohort = int(run_df(cohort_sql).iloc[0].HEADCOUNT)
        med_bal_sql = f"SELECT MEDIAN(BALANCE) AS MEDIAN_BALANCE FROM {DB}.REPORTS.AT_RISK_STUDENTS WHERE TERM_ID = '{term_label}'"
        med_bal = float(run_df(med_bal_sql).iloc[0].MEDIAN_BALANCE)
        rk1, rk2, rk3 = st.columns(3)
        rk1.metric("At-risk count", f"{at_risk_count:,}")
        pct = (at_risk_count / cohort) if cohort else 0.0
        rk2.metric("% of cohort", f"{pct*100:.1f}%")
        rk3.metric("Median balance", f"${med_bal:,.0f}")

        # Risk reasons counts
        sums_sql = f"""
        SELECT SUM(LOW_ENGAGEMENT) AS LOW_ENG, SUM(HIGH_BALANCE) AS HIGH_BAL, SUM(LOW_PRIOR_GPA) AS LOW_GPA, SUM(NO_ADVISING) AS NO_ADV
        FROM {DB}.REPORTS.AT_RISK_STUDENTS
        WHERE TERM_ID = '{term_label}'
        """
        sums = run_df(sums_sql).iloc[0]
        reasons_df = pd.DataFrame({
            "REASON": ["Low engagement", "High balance", "Low prior GPA", "No advising"],
            "COUNT": [int(sums.LOW_ENG or 0), int(sums.HIGH_BAL or 0), int(sums.LOW_GPA or 0), int(sums.NO_ADV or 0)],
        })
        st.caption("Risk reasons count")
        chart_reasons = (
            alt.Chart(reasons_df)
            .mark_bar()
            .encode(x=alt.X("COUNT:Q", title="Students"), y=alt.Y("REASON:N", sort='-x', title="Reason"), tooltip=["REASON", "COUNT"])
            .properties(height=280)
        )
        st.altair_chart(chart_reasons, use_container_width=True)

        # At-risk by major
        major_risk_sql = f"""
        SELECT MAJOR, COUNT(*) AS AT_RISK
        FROM {DB}.REPORTS.AT_RISK_STUDENTS
        WHERE TERM_ID = '{term_label}' AND MAJOR IS NOT NULL
        GROUP BY MAJOR
        ORDER BY AT_RISK DESC
        LIMIT 15
        """
        major_risk_df = run_df(major_risk_sql)
        st.caption("At-risk by major")
        if not major_risk_df.empty:
            chart_major_risk = (
                alt.Chart(major_risk_df)
                .mark_bar()
                .encode(x=alt.X("AT_RISK:Q", title="Students"), y=alt.Y("MAJOR:N", sort='-x', title="Major"), tooltip=["MAJOR", "AT_RISK"])
                .properties(height=320)
            )
            st.altair_chart(chart_major_risk, use_container_width=True)

        st.download_button(
            "Download CSV",
            data=risk_df.to_csv(index=False).encode("utf-8"),
            file_name=f"at_risk_students_{term_label}.csv",
            mime="text/csv",
        )


