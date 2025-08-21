## Student 360 Hands‑On Lab (Snowflake)

Welcome to the Student 360 hands‑on lab. You will build a simple, realistic Student 360 analytics flow in Snowflake using dynamic tables and a one‑page Streamlit‑in‑Snowflake app.

### What you’ll do (high level)
- Stand up a curated “student data lake” from a public S3 bucket (already prepared).
- Transform raw data into a minimal dimensional model with dynamic tables (no SCDs): STAGE → DIM/FACT.
- Build reporting dynamic tables for cohort summaries, courses, financials, advising, and “at‑risk” flags.
- Explore with quick SQL, then view everything in a Streamlit‑in‑Snowflake dashboard.

### Focus of this lab
- Keep ingestion simple (scripted) so we can focus on:
  - Dynamic tables for incremental, dependency‑aware transformations
  - Simple dimensional modeling for a Student 360
  - Lineage from sources → stage → dim/fact → reports
  - A small Streamlit app for exploration and storytelling

### Estimated time
60–90 minutes end‑to‑end (most time on dynamic tables, lineage, and the app).

---

## Prerequisites
- Snowflake account with role `SYSADMIN` (or equivalent privileges)
- A running warehouse named `COMPUTE_WH` (or update the scripts to your warehouse name)
- Internet access to the public S3 bucket (no credentials required)

Optional (for maintainers): AWS CLI installed if you want to regenerate/upload sample data.

---

## Quick start
1) In the Snowflake UI, open a new SQL worksheet and run:
   - `hands_on_lab/0_setup.sql` (creates databases, schemas, stage, tables, and loads data)
   - `hands_on_lab/2_data_modeling.sql` (dynamic tables for STAGE, DIM, FACT)
   - `hands_on_lab/3_reporting.sql` (reporting dynamic tables)

2) In the Snowflake Streamlit UI, create an app using `hands_on_lab/4_streamlit.py` and run it.

3) Optionally run `hands_on_lab/1_data_exploration.sql` to browse the data by SQL.

---

## What’s happening under the hood (technical details)

### Data lake – sources and loading
- Database: `STUDENT_DATA_LAKE`
- Schemas: `SIS`, `LMS`, `ADMISSIONS`, `FINANCIALS`, `STUDENT_ADVISING`, and `ADMIN` (shared utilities)
- Stage: `ADMIN.STUDENT_DATA_STAGE` → `s3://snowflake-student-360-hol-975500823464` (public‑read)
- File format: `ADMIN.CSV_STANDARD` with `PARSE_HEADER = TRUE` and quoting compatible with standard CSVs
- Loads: `COPY INTO ... MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE` for all base tables

The sample dataset contains 12,548 students across multiple terms with realistic enrollments, LMS events, financials, and advising activity.

### Transformations – dynamic tables
- Database: `STUDENT_DATA_WAREHOUSE`
- Schemas: `STAGE`, `DIM`, `FACT`, `REPORTS`
- All core tables in `STAGE`, `DIM`, and `FACT` use `TARGET_LAG = '30 days'` for low‑maintenance refresh.
- Reporting tables in `REPORTS` use `TARGET_LAG = 'DOWNSTREAM'` to follow upstream dependencies.

Minimal dimensional model (no SCDs; natural keys):
- DIM.STUDENT: student profile columns (program, major, residency, advisor)
- DIM.TERM: academic terms
- DIM.SECTION: course offerings (joins to course attributes)
- DIM.ADVISOR: advisor directory
- FACT.ENROLLMENT: one row per student‑section‑term with attempted units and grades
- FACT.ENGAGEMENT_DAILY: student × section × day event counts (derived from LMS logins)
- FACT.FINANCIAL_TRANSACTION: charges/payments with signed amounts and simple flags
- FACT.ADVISING: advising appointments per student/advisor/date

STAGE tables (silver layer):
- STAGE.ENGAGEMENT_DAILY: aggregates LMS events per student/section/day

### Reporting – dynamic tables (semantic layer)
The `REPORTS` schema materializes common analytic views:
- REPORTS.STUDENT_TERM_SUMMARY: per student × term metrics (courses, units, engagement, financials, advising, prior‑term GPA)
- REPORTS.COURSE_SECTION_SUMMARY: per section metrics (enrollment, engagement per student, completion rate)
- REPORTS.ENGAGEMENT_WEEKLY_TREND: weekly engagement per student × section
- REPORTS.FINANCIAL_TERM_SUMMARY: student × term financial roll‑ups (charges, payments, balance)
- REPORTS.ADVISING_SUMMARY: student × term advising roll‑ups (counts, last appointment)
- REPORTS.PROGRAM_COHORT_OVERVIEW: cohort metrics by program/major × term
- REPORTS.AT_RISK_STUDENTS: simple rule‑based flags (low engagement, high balance, low prior GPA, no advising)

### Streamlit‑in‑Snowflake app
File: `hands_on_lab/4_streamlit.py`
- Uses `snowflake.snowpark.context.get_active_session()` to query `STUDENT_DATA_WAREHOUSE.REPORTS.*`
- Sidebar filters: term, program/major, search, risk toggles
- Overview tab: KPIs, headcount by major, GPA by major, balance distribution
- Courses tab: students by subject and modality, section metrics and distributions
- Risk tab: at‑risk KPIs, reason counts, at‑risk by major, CSV export

---

## Running the lab step‑by‑step
1) Set context in a worksheet:
   - Role: `SYSADMIN`
   - Warehouse: `COMPUTE_WH`

2) Run `hands_on_lab/0_setup.sql`
   - Creates `STUDENT_DATA_LAKE` and schemas
   - Creates `ADMIN.CSV_STANDARD` and stage to the public S3 bucket
   - Creates base tables and runs `COPY INTO` to load them
   - Creates `STUDENT_DATA_WAREHOUSE` with `STAGE`, `DIM`, `FACT`, `REPORTS`

3) Run `hands_on_lab/2_data_modeling.sql`
   - Builds the dynamic tables for STAGE, DIM, and FACT

4) Run `hands_on_lab/3_reporting.sql`
   - Builds the reporting dynamic tables with `TARGET_LAG = 'DOWNSTREAM'`

5) Launch the Streamlit app
   - In Snowflake, create an app and point the script to `hands_on_lab/4_streamlit.py`
   - Select a term and explore filters/visuals

6) (Optional) Explore with SQL via `hands_on_lab/1_data_exploration.sql`

---

## Troubleshooting
- Stage creation 403 Access Denied:
  - Bucket is public; ensure the stage uses `URL = 's3://snowflake-student-360-hol-975500823464'` and omit `DIRECTORY = (ENABLE=TRUE)`.
- COPY with column matching error:
  - The file format sets `PARSE_HEADER = TRUE`. Keep `MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE` in `COPY`.
- Warehouse errors:
  - If `COMPUTE_WH` doesn’t exist, change the scripts to your warehouse name.

---

## Repository layout
- `hands_on_lab/0_setup.sql` – databases, schemas, stage, file format, base tables, loads
- `hands_on_lab/1_data_exploration.sql` – simple sanity/preview queries
- `hands_on_lab/2_data_modeling.sql` – dynamic tables for STAGE, DIM, FACT
- `hands_on_lab/3_reporting.sql` – reporting dynamic tables
- `hands_on_lab/4_streamlit.py` – Streamlit‑in‑Snowflake app
- `data/` – generated sample CSVs (mirrored to public S3)
- `scripts/` – optional utilities (data generation and S3 upload)

---

## Clean up (optional)
You can drop the lab databases when done:
```
DROP DATABASE IF EXISTS STUDENT_DATA_WAREHOUSE;
DROP DATABASE IF EXISTS STUDENT_DATA_LAKE;
```



