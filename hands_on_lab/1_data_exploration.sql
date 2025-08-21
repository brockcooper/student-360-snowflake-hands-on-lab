-- Student 360 – Data Exploration
-- Safe, quick queries to explore loaded data

-- Session context
USE ROLE SYSADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE STUDENT_DATA_LAKE;

-- =============================================================
-- Peek at some students
-- =============================================================
SELECT *
FROM SIS.STUDENTS
ORDER BY STUDENT_ID
LIMIT 20;

-- Term catalog snapshot
SELECT *
FROM SIS.TERMS
ORDER BY START_DATE
LIMIT 10;

-- =============================================================
-- Enrollment distribution by term and modality
-- =============================================================
SELECT e.TERM_ID,
       s.MODALITY,
       COUNT(*) AS enrollments
FROM SIS.ENROLLMENTS e
JOIN SIS.SECTIONS s
  ON s.COURSE_SECTION_ID = e.COURSE_SECTION_ID
GROUP BY 1,2
ORDER BY 1,2;

-- =============================================================
-- LMS engagement: events per student (sample of 20)
-- =============================================================
WITH enrollment_courses AS (
  SELECT DISTINCT e.STUDENT_ID,
                  e.COURSE_SECTION_ID,
                  x.LMS_COURSE_ID
  FROM SIS.ENROLLMENTS e
  JOIN LMS.COURSE_XWALK x
    ON x.COURSE_SECTION_ID = e.COURSE_SECTION_ID
)
SELECT ec.STUDENT_ID,
       COUNT(l.EVENT_TS) AS lms_event_count
FROM enrollment_courses ec
LEFT JOIN LMS.LMS_LOGINS l
  ON l.STUDENT_ID = ec.STUDENT_ID
 AND l.LMS_COURSE_ID = ec.LMS_COURSE_ID
GROUP BY ec.STUDENT_ID
ORDER BY lms_event_count DESC
LIMIT 20;

-- =============================================================
-- Financials: top outstanding balances (sample of 20)
-- =============================================================
SELECT sa.STUDENT_ID,
       sa.TERM_ID,
       sa.BALANCE
FROM FINANCIALS.STUDENT_ACCOUNTS sa
WHERE sa.BALANCE > 0
ORDER BY sa.BALANCE DESC
LIMIT 20;

-- =============================================================
-- Advising activity: appointments per student (sample of 20)
-- =============================================================
SELECT a.STUDENT_ID,
       COUNT(*) AS appointments
FROM STUDENT_ADVISING.APPOINTMENTS a
GROUP BY a.STUDENT_ID
ORDER BY appointments DESC
LIMIT 20;

-- =============================================================
-- Admissions funnel snapshot
-- =============================================================
SELECT DECISION,
       COUNT(*) AS applications
FROM ADMISSIONS.APPLICATIONS
GROUP BY DECISION
ORDER BY applications DESC;


