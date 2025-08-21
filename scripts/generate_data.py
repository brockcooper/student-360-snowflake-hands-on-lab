#!/usr/bin/env python3
import argparse
import csv
import os
import random
from datetime import datetime, timedelta


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def daterange(start_date: datetime, end_date: datetime, step_days: int = 1):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=step_days)


def choose_weighted(items_with_weights):
    items, weights = zip(*items_with_weights)
    return random.choices(items, weights=weights, k=1)[0]


def generate_terms():
    # Three terms spanning an academic year
    terms = [
        {
            "term_id": "2024FA",
            "term_name": "Fall 2024",
            "start_date": datetime(2024, 8, 26),
            "end_date": datetime(2024, 12, 13),
        },
        {
            "term_id": "2025SP",
            "term_name": "Spring 2025",
            "start_date": datetime(2025, 1, 13),
            "end_date": datetime(2025, 5, 2),
        },
        {
            "term_id": "2025FA",
            "term_name": "Fall 2025",
            "start_date": datetime(2025, 8, 25),
            "end_date": datetime(2025, 12, 12),
        },
    ]
    return terms


def generate_catalog(num_courses: int = 120):
    subjects = [
        "MATH",
        "ENG",
        "CS",
        "BIO",
        "CHEM",
        "HIST",
        "ECON",
        "PSYC",
        "PHYS",
        "ART",
        "STAT",
        "BUS",
        "SOC",
        "PHIL",
    ]
    titles = [
        "Introduction",
        "Foundations",
        "Principles",
        "Advanced Topics",
        "Methods",
        "Applications",
        "Data Analysis",
        "Algorithms",
        "Laboratory",
        "Seminar",
        "Design",
    ]

    courses = []
    course_idx = 1
    while len(courses) < num_courses:
        subj = random.choice(subjects)
        catalog_nbr = f"{random.randint(100, 499)}"
        title = f"{subj} {random.choice(titles)}"
        units = random.choice([3, 3, 3, 4])
        course_id = f"{subj}{catalog_nbr}"
        courses.append({
            "course_id": course_id,
            "subject": subj,
            "catalog_nbr": catalog_nbr,
            "title": title,
            "units": units,
        })
        course_idx += 1
    return courses


def generate_sections(courses, terms):
    sections = []
    for term in terms:
        for course in courses:
            num_sections = random.choice([1, 1, 1, 2, 3])
            for section_nbr in range(1, num_sections + 1):
                modality = random.choice(["INPERSON", "ONLINE", "HYBRID"])
                course_section_id = f"{course['course_id']}-{term['term_id']}-S{section_nbr:02d}"
                sections.append({
                    "course_section_id": course_section_id,
                    "course_id": course["course_id"],
                    "term_id": term["term_id"],
                    "section_nbr": section_nbr,
                    "modality": modality,
                })
    return sections


def generate_advisors(num_advisors: int = 50):
    first_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Riley", "Morgan", "Jamie", "Avery", "Quinn", "Parker",
        "Reese", "Blake", "Drew", "Rowan", "Skyler", "Hayden", "Kendall", "Logan", "Emerson", "Finley",
    ]
    last_names = [
        "Smith", "Johnson", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
        "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    ]
    departments = ["Engineering", "Science", "Arts", "Business", "Social Sciences", "Education", "Health", "Undeclared"]
    advisors = []
    for i in range(1, num_advisors + 1):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        advisors.append({
            "advisor_id": f"ADV{i:03d}",
            "advisor_name": name,
            "department": random.choice(departments),
        })
    return advisors


def generate_students(num_students: int, terms, advisors):
    first_names = [
        "Olivia","Liam","Emma","Noah","Ava","Oliver","Sophia","Elijah","Isabella","Mateo",
        "Mia","Lucas","Amelia","Levi","Harper","Asher","Evelyn","James","Luna","Benjamin",
    ]
    last_names = [
        "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
        "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    ]
    genders = ["F", "M", "X"]
    residency_values = ["IN_STATE", "OUT_OF_STATE", "INTERNATIONAL"]
    majors = [
        "Computer Science","Mathematics","Biology","Chemistry","Economics","Psychology","History","Art",
        "Business Administration","Sociology","Statistics","Physics","Philosophy","Education","Nursing",
    ]

    term_ids = [t["term_id"] for t in terms]
    students = []
    base_sid = 10000000
    for i in range(num_students):
        sid = base_sid + i
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{sid % 1000}@example.edu"
        dob = datetime(1998, 1, 1) + timedelta(days=random.randint(0, 365 * 10))
        gender = random.choice(genders)
        residency = choose_weighted([(residency_values[0], 70), (residency_values[1], 25), (residency_values[2], 5)])
        program = "Undergraduate"
        major = random.choice(majors)
        admit_term_id = random.choice(term_ids[:-1])  # admit before current
        current_term_id = term_ids[-1]
        term_index = term_ids.index(current_term_id) - term_ids.index(admit_term_id)
        class_standing = ["Freshman", "Sophomore", "Junior", "Senior"][min(max(term_index, 0), 3)]
        advisor_id = random.choice(advisors)["advisor_id"]
        ethnicity = random.choice(["Not Disclosed","Hispanic or Latino","White","Black or African American","Asian","Multiracial"]) 

        students.append({
            "student_id": sid,
            "first_name": fn,
            "last_name": ln,
            "email": email,
            "dob": dob.strftime("%Y-%m-%d"),
            "gender": gender,
            "ethnicity": ethnicity,
            "residency": residency,
            "program": program,
            "major": major,
            "admit_term_id": admit_term_id,
            "current_term_id": current_term_id,
            "class_standing": class_standing,
            "advisor_id": advisor_id,
        })
    return students


def generate_enrollments(students, sections, terms):
    # Focus enrollments on current term; add a light sprinkle on prior term for realism
    term_map = {t["term_id"]: t for t in terms}
    current_term_id = terms[-1]["term_id"]
    prior_term_id = terms[-2]["term_id"]

    sections_by_term = {}
    for s in sections:
        sections_by_term.setdefault(s["term_id"], []).append(s)

    enrollments = []
    for student in students:
        # Current term: 4-5 sections per student
        current_sections = random.sample(sections_by_term[current_term_id], k=random.choice([4, 4, 5]))
        for sec in current_sections:
            enrollments.append({
                "student_id": student["student_id"],
                "course_section_id": sec["course_section_id"],
                "term_id": current_term_id,
                "enrollment_status": "ENROLLED",
                "grade_letter": "",
                "grade_points": "",
            })
        # Prior term: ~40% of students had enrollments (to support GPA/grades)
        if random.random() < 0.4:
            prior_sections = random.sample(sections_by_term[prior_term_id], k=random.choice([3, 4]))
            for sec in prior_sections:
                grade_letter = random.choice(["A","A-","B+","B","B-","C+","C","D","F"])
                grade_points = {
                    "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
                    "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0
                }[grade_letter]
                enrollments.append({
                    "student_id": student["student_id"],
                    "course_section_id": sec["course_section_id"],
                    "term_id": prior_term_id,
                    "enrollment_status": "COMPLETED",
                    "grade_letter": grade_letter,
                    "grade_points": grade_points,
                })
    return enrollments


def write_csv(path, rows, header):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_lms(enrollments, sections):
    # Crosswalk and LMS events derived only from enrollments
    xwalk = []
    lms_logins = []
    submissions = []

    lms_id_by_section = {}
    for sec in sections:
        lms_id_by_section[sec["course_section_id"]] = f"LMS-{abs(hash(sec['course_section_id'])) % 10_000_000:07d}"
        xwalk.append({
            "course_section_id": sec["course_section_id"],
            "lms_course_id": lms_id_by_section[sec["course_section_id"]],
        })

    # Group enrollments by (student, section) and by term boundaries
    # For performance, we create limited events per enrollment
    #  - 6 login events
    #  - 4 submissions
    term_dates = {
        "2024FA": (datetime(2024, 8, 26), datetime(2024, 12, 13)),
        "2025SP": (datetime(2025, 1, 13), datetime(2025, 5, 2)),
        "2025FA": (datetime(2025, 8, 25), datetime(2025, 12, 12)),
    }

    for enr in enrollments:
        csid = enr["course_section_id"]
        term_id = enr["term_id"]
        start_dt, end_dt = term_dates[term_id]
        lms_course_id = lms_id_by_section[csid]
        student_id = enr["student_id"]

        # Login/view events
        for _ in range(6):
            event_ts = start_dt + timedelta(days=random.randint(0, (end_dt - start_dt).days), hours=random.randint(8, 20), minutes=random.randint(0, 59))
            lms_logins.append({
                "student_id": student_id,
                "lms_course_id": lms_course_id,
                "event_ts": event_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": random.choice(["login","view","discussion_view","resource_click"]),
            })

        # Submissions
        for aidx in range(1, 5):
            submitted_ts = start_dt + timedelta(days=random.randint(7, (end_dt - start_dt).days))
            score = random.randint(60, 100)
            max_score = 100
            late_flag = random.choice(["0","0","0","1"])  # mostly on time
            submissions.append({
                "student_id": student_id,
                "lms_course_id": lms_course_id,
                "assignment_id": f"A{aidx:02d}",
                "submitted_ts": submitted_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "score": score,
                "max_score": max_score,
                "late_flag": late_flag,
            })

    return xwalk, lms_logins, submissions


def generate_admissions(students, terms):
    applications = []
    tests = []
    for s in students:
        app_term_id = s["admit_term_id"]
        app_complete_dt = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 200))
        decision = "Admit"
        decision_dt = app_complete_dt + timedelta(days=random.randint(5, 30))
        deposit_flag = random.choice(["1","1","1","0"])  # mostly deposited
        applications.append({
            "student_id": s["student_id"],
            "application_id": f"APP{s['student_id']}",
            "app_term_id": app_term_id,
            "app_complete_dt": app_complete_dt.strftime("%Y-%m-%d"),
            "decision": decision,
            "decision_dt": decision_dt.strftime("%Y-%m-%d"),
            "deposit_flag": deposit_flag,
        })
        if random.random() < 0.6:
            test_type = random.choice(["SAT","ACT"]) 
            test_date = app_complete_dt - timedelta(days=random.randint(30, 180))
            score = random.randint(18, 35) if test_type == "ACT" else random.randint(900, 1550)
            tests.append({
                "student_id": s["student_id"],
                "test_type": test_type,
                "test_date": test_date.strftime("%Y-%m-%d"),
                "score": score,
            })
    return applications, tests


def generate_financials(students, enrollments, courses_by_id):
    # Aggregate charges by enrolled units; payments and aid reduce balance
    # Focus on current term; generate smaller amounts for prior term
    # Build units per enrollment
    units_by_section = {}
    for enr in enrollments:
        course_id = enr["course_section_id"].split("-")[0]
        units_by_section[enr["course_section_id"]] = courses_by_id[course_id]["units"]

    current_term_id = max(set(e["term_id"] for e in enrollments))

    enrollments_by_student_term = {}
    for enr in enrollments:
        key = (enr["student_id"], enr["term_id"])
        enrollments_by_student_term.setdefault(key, []).append(enr)

    student_accounts = []
    transactions = []
    aid_awards = []

    trans_id = 1
    award_id = 1
    for (student_id, term_id), enr_list in enrollments_by_student_term.items():
        total_units = sum(units_by_section[e["course_section_id"]] for e in enr_list)
        tuition_rate = 350 if random.random() < 0.7 else 650  # in-state vs out-of-state
        charges = total_units * tuition_rate
        fees = random.randint(100, 400)
        total_charges = round(charges + fees, 2)

        # Aid for ~55% of students in a term
        aid = 0
        if random.random() < 0.55:
            aid = random.randint(500, 3500)
            aid_awards.append({
                "award_id": f"AWD{award_id:07d}",
                "student_id": student_id,
                "term_id": term_id,
                "aid_type": random.choice(["Grant","Scholarship","Loan"]),
                "amount": aid,
                "disbursed_dt": (datetime(2025, 1, 10) if term_id.endswith("SP") else datetime(2025, 8, 20)).strftime("%Y-%m-%d"),
            })
            award_id += 1

        # Payments: 1-3 payments per term
        payments = 0
        for _ in range(random.choice([1, 2, 3])):
            amt = random.randint(200, 2000)
            payments += amt
            transactions.append({
                "transaction_id": f"TX{trans_id:09d}",
                "student_id": student_id,
                "term_id": term_id,
                "trans_dt": (datetime(2025, 2, 1) if term_id.endswith("SP") else datetime(2025, 9, 1)).strftime("%Y-%m-%d"),
                "trans_type": "PAYMENT",
                "amount": amt,
                "method": random.choice(["CARD","ACH","CASH"]),
            })
            trans_id += 1

        # One tuition charge transaction for transparency
        transactions.append({
            "transaction_id": f"TX{trans_id:09d}",
            "student_id": student_id,
            "term_id": term_id,
            "trans_dt": (datetime(2025, 1, 20) if term_id.endswith("SP") else datetime(2025, 8, 28)).strftime("%Y-%m-%d"),
            "trans_type": "CHARGE",
            "amount": total_charges,
            "method": "BILLING",
        })
        trans_id += 1

        total_payments = payments + aid
        balance = round(total_charges - total_payments, 2)
        student_accounts.append({
            "student_id": student_id,
            "term_id": term_id,
            "total_charges": round(total_charges, 2),
            "total_payments": round(total_payments, 2),
            "balance": balance,
        })

    return student_accounts, transactions, aid_awards


def generate_advising(students, advisors):
    appointments = []
    notes = []
    appt_id = 1
    note_id = 1
    for s in students:
        # 0–3 appointments
        k = random.choice([0, 0, 1, 1, 2, 3])
        for _ in range(k):
            advisor = random.choice(advisors)
            dt = datetime(2025, random.choice([2, 3, 9, 10]), random.randint(1, 28))
            appointments.append({
                "appointment_id": f"APT{appt_id:07d}",
                "student_id": s["student_id"],
                "advisor_id": advisor["advisor_id"],
                "appointment_dt": dt.strftime("%Y-%m-%d"),
                "outcome": random.choice(["Completed","No Show","Rescheduled","Action Plan"]),
            })
            appt_id += 1
            if random.random() < 0.5:
                notes.append({
                    "note_id": f"NOTE{note_id:07d}",
                    "student_id": s["student_id"],
                    "advisor_id": advisor["advisor_id"],
                    "note_dt": dt.strftime("%Y-%m-%d"),
                    "category": random.choice(["Academic","Financial","Wellness","Career"]),
                    "risk_flag": random.choice(["0","0","1"]),
                })
                note_id += 1
    return appointments, notes


def main():
    parser = argparse.ArgumentParser(description="Generate Student 360 synthetic CSV data")
    parser.add_argument("--num-students", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=360)
    parser.add_argument("--out-dir", type=str, default="data")
    args = parser.parse_args()

    random.seed(args.seed)

    # Prepare directories
    base_dir = os.path.abspath(args.out_dir)
    sis_dir = os.path.join(base_dir, "sis")
    lms_dir = os.path.join(base_dir, "lms")
    adm_dir = os.path.join(base_dir, "admissions")
    fin_dir = os.path.join(base_dir, "financials")
    adv_dir = os.path.join(base_dir, "student_advising")
    for d in [sis_dir, lms_dir, adm_dir, fin_dir, adv_dir]:
        ensure_dir(d)

    # Generate reference data
    terms = generate_terms()
    courses = generate_catalog()
    sections = generate_sections(courses, terms)
    advisors = generate_advisors()
    students = generate_students(args.num_students, terms, advisors)
    enrollments = generate_enrollments(students, sections, terms)

    # Mapping helpers
    courses_by_id = {c["course_id"]: c for c in courses}

    # Write SIS CSVs
    write_csv(
        os.path.join(sis_dir, "students.csv"),
        students,
        [
            "student_id","first_name","last_name","email","dob","gender","ethnicity","residency","program","major",
            "admit_term_id","current_term_id","class_standing","advisor_id",
        ],
    )
    write_csv(
        os.path.join(sis_dir, "terms.csv"),
        (
            {
                "term_id": t["term_id"],
                "term_name": t["term_name"],
                "start_date": t["start_date"].strftime("%Y-%m-%d"),
                "end_date": t["end_date"].strftime("%Y-%m-%d"),
            }
            for t in terms
        ),
        ["term_id","term_name","start_date","end_date"],
    )
    write_csv(
        os.path.join(sis_dir, "courses.csv"),
        courses,
        ["course_id","subject","catalog_nbr","title","units"],
    )
    write_csv(
        os.path.join(sis_dir, "sections.csv"),
        sections,
        ["course_section_id","course_id","term_id","section_nbr","modality"],
    )
    write_csv(
        os.path.join(sis_dir, "enrollments.csv"),
        enrollments,
        ["student_id","course_section_id","term_id","enrollment_status","grade_letter","grade_points"],
    )

    # LMS
    xwalk, lms_logins, submissions = generate_lms(enrollments, sections)
    write_csv(os.path.join(lms_dir, "course_xwalk.csv"), xwalk, ["course_section_id","lms_course_id"])
    write_csv(os.path.join(lms_dir, "lms_logins.csv"), lms_logins, ["student_id","lms_course_id","event_ts","event_type"])
    write_csv(os.path.join(lms_dir, "submissions.csv"), submissions, ["student_id","lms_course_id","assignment_id","submitted_ts","score","max_score","late_flag"])

    # Admissions
    applications, tests = generate_admissions(students, terms)
    write_csv(os.path.join(adm_dir, "applications.csv"), applications, ["student_id","application_id","app_term_id","app_complete_dt","decision","decision_dt","deposit_flag"])
    write_csv(os.path.join(adm_dir, "tests.csv"), tests, ["student_id","test_type","test_date","score"])

    # Financials
    student_accounts, transactions, aid_awards = generate_financials(students, enrollments, courses_by_id)
    write_csv(os.path.join(fin_dir, "student_accounts.csv"), student_accounts, ["student_id","term_id","total_charges","total_payments","balance"])
    write_csv(os.path.join(fin_dir, "transactions.csv"), transactions, ["transaction_id","student_id","term_id","trans_dt","trans_type","amount","method"])
    write_csv(os.path.join(fin_dir, "aid_awards.csv"), aid_awards, ["award_id","student_id","term_id","aid_type","amount","disbursed_dt"])

    # Advising
    appointments, notes = generate_advising(students, advisors)
    write_csv(os.path.join(adv_dir, "advisors.csv"), advisors, ["advisor_id","advisor_name","department"])
    write_csv(os.path.join(adv_dir, "appointments.csv"), appointments, ["appointment_id","student_id","advisor_id","appointment_dt","outcome"])
    write_csv(os.path.join(adv_dir, "notes.csv"), notes, ["note_id","student_id","advisor_id","note_dt","category","risk_flag"])

    print("Data generation complete.")


if __name__ == "__main__":
    main()


