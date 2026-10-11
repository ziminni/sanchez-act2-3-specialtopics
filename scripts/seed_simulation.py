"""Populate a teaching simulation: terms, offerings, enrollments and grades.

Run this after `scripts/seed_catalog.py` (programs and subjects) and
`scripts/seed_accounts.py` (accounts and linked students). It creates two academic
terms, offers catalog subjects in each term with the two instructors taking turns,
enrolls the five students in three or four subjects each, and encodes grades:

* first-term subjects are completed with midterm and final grades, so the computed GWA
  in `GET /students/{id}/academic-record` is meaningful;
* second-term subjects are in progress with a midterm grade only, so they are excluded
  from the GWA until a final grade exists;
* one second-term subject is dropped, which also leaves the average.

Dates, sections, schedules and rooms are plausible but entirely synthetic. Existing
terms, offerings, enrollments and grades are skipped, so repeat runs are safe.

Usage from the project root:

    python scripts/seed_simulation.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app import models as m
from app import schemas as s
from app import services as service
from app.config import settings
from app.database import SessionLocal

ACADEMIC_YEAR = '2026-2027'
TERMS = [
    ('FIRST', date(2026, 8, 3), date(2026, 12, 18)),
    ('SECOND', date(2027, 1, 11), date(2027, 5, 28)),
]

# semester, subject code, instructor, section, schedule, room, capacity
OFFERINGS = [
    ('FIRST', 'IT101', 'instructor@example.com', 'A', 'MWF 09:00-10:00', 'Room IT-201', 40),
    ('FIRST', 'IT102', 'instructor2@example.com', 'A', 'TTh 10:30-12:00', 'Room IT-202', 40),
    ('FIRST', 'IT203', 'instructor@example.com', 'A', 'MWF 13:00-14:00', 'Room IT-203', 40),
    ('FIRST', 'IT205', 'instructor2@example.com', 'A', 'Sat 08:00-11:00', 'Room IT-204', 35),
    ('FIRST', 'CS101', 'instructor@example.com', 'A', 'MWF 07:30-08:30', 'Room CS-101', 40),
    ('FIRST', 'CS202', 'instructor2@example.com', 'A', 'TTh 13:00-14:30', 'Room CS-102', 40),
    ('FIRST', 'IS101', 'instructor@example.com', 'A', 'MWF 10:30-11:30', 'Room IS-101', 40),
    ('FIRST', 'IS201', 'instructor2@example.com', 'A', 'TTh 08:00-09:30', 'Room IS-102', 40),
    ('SECOND', 'IT202', 'instructor@example.com', 'A', 'MWF 09:00-10:00', 'Room IT-201', 40),
    ('SECOND', 'CS301', 'instructor2@example.com', 'A', 'TTh 10:30-12:00', 'Room CS-101', 35),
    ('SECOND', 'CS203', 'instructor@example.com', 'A', 'MWF 07:30-08:30', 'Room CS-103', 40),
    ('SECOND', 'IS203', 'instructor@example.com', 'A', 'MWF 13:00-14:00', 'Room IS-101', 40),
    ('SECOND', 'IS302', 'instructor2@example.com', 'A', 'Sat 08:00-11:00', 'Room IS-102', 35),
]

# student email, subject code, semester, status, midterm grade, final grade
ENROLLMENTS = [
    ('student@example.com', 'IT101', 'FIRST', 'COMPLETED', 86, 88),
    ('student@example.com', 'IT102', 'FIRST', 'COMPLETED', 90, 92),
    ('student@example.com', 'IT203', 'FIRST', 'COMPLETED', 89, 90),
    ('student@example.com', 'IT202', 'SECOND', 'ENROLLED', 86, None),
    ('student2@example.com', 'IT101', 'FIRST', 'COMPLETED', 83, 85),
    ('student2@example.com', 'IT205', 'FIRST', 'COMPLETED', 77, 79),
    ('student2@example.com', 'IT202', 'SECOND', 'ENROLLED', 84, None),
    ('student3@example.com', 'CS101', 'FIRST', 'COMPLETED', 92, 94),
    ('student3@example.com', 'CS202', 'FIRST', 'COMPLETED', 90, 91),
    ('student3@example.com', 'CS301', 'SECOND', 'ENROLLED', 92, None),
    ('student4@example.com', 'IS101', 'FIRST', 'COMPLETED', 85, 87),
    ('student4@example.com', 'IS201', 'FIRST', 'COMPLETED', 88, 89),
    ('student4@example.com', 'IS203', 'SECOND', 'ENROLLED', 88, None),
    ('student4@example.com', 'IS302', 'SECOND', 'ENROLLED', 90, None),
    ('student5@example.com', 'CS101', 'FIRST', 'COMPLETED', 88, 90),
    ('student5@example.com', 'CS203', 'SECOND', 'DROPPED', None, None),
    ('student5@example.com', 'CS301', 'SECOND', 'ENROLLED', 89, None),
]


def seed_terms(db, registrar):
    created, skipped = 0, 0
    term_ids = {}
    for semester, start_date, end_date in TERMS:
        existing = db.scalar(select(m.AcademicTerm).where(
            m.AcademicTerm.academic_year == ACADEMIC_YEAR,
            m.AcademicTerm.semester == semester,
        ))
        if existing:
            term_ids[semester] = existing.id
            skipped += 1
        else:
            # The service layer enforces the consecutive-year and date-order rules.
            result = service.save(db, 'academic-terms', s.TermCreate(
                academic_year=ACADEMIC_YEAR, semester=semester,
                start_date=start_date, end_date=end_date,
            ), registrar)
            term_ids[semester] = result['data']['id']
            created += 1
    return term_ids, created, skipped


def seed_offerings(db, registrar, users, term_ids):
    created, skipped = 0, 0
    offerings = {}
    courses = {course.course_code: course for course in db.scalars(select(m.Course))}
    for semester, course_code, instructor_email, section, schedule, room, capacity in OFFERINGS:
        course = courses.get(course_code)
        if course is None:
            raise SystemExit(f'Subject {course_code} is missing; run scripts/seed_catalog.py first.')
        instructor = users.get(instructor_email)
        if instructor is None:
            raise SystemExit(f'Account {instructor_email} is missing; run scripts/seed_accounts.py first.')
        key = (course_code, semester)
        existing = db.scalar(select(m.CourseOffering).where(
            m.CourseOffering.course_id == course.id,
            m.CourseOffering.academic_term_id == term_ids[semester],
            m.CourseOffering.section == section,
        ))
        if existing:
            offerings[key] = existing.id
            skipped += 1
        else:
            result = service.save(db, 'course-offerings', s.OfferingCreate(
                course_id=course.id, academic_term_id=term_ids[semester],
                instructor_id=instructor.id, section=section, schedule=schedule,
                room=room, capacity=capacity,
            ), registrar)
            offerings[key] = result['data']['id']
            created += 1
    return offerings, created, skipped


def seed_enrollments(db, registrar, users, offerings, term_starts):
    created, skipped, graded = 0, 0, 0
    students = {student.user_id: student for student in db.scalars(select(m.Student))}
    for email, course_code, semester, status, midterm, final in ENROLLMENTS:
        user = users.get(email)
        student = students.get(user.id) if user else None
        if student is None:
            raise SystemExit(f'Student profile for {email} is missing; run scripts/seed_accounts.py first.')
        offering_id = offerings[(course_code, semester)]
        existing = db.scalar(select(m.Enrollment).where(
            m.Enrollment.student_id == student.id,
            m.Enrollment.course_offering_id == offering_id,
        ))
        if existing:
            enrollment_id = existing.id
            skipped += 1
        else:
            result = service.save(db, 'enrollments', s.EnrollmentCreate(
                student_id=student.id, course_offering_id=offering_id,
                enrollment_date=term_starts[semester], status=status,
            ), registrar)
            enrollment_id = result['data']['id']
            created += 1
        if midterm is None and final is None:
            continue
        if db.scalar(select(m.Grade.id).where(m.Grade.enrollment_id == enrollment_id)):
            continue
        # Grades are written by the offering's own instructor, never by the registrar.
        offering = db.get(m.CourseOffering, offering_id)
        instructor = db.get(m.User, offering.instructor_id)
        service.save(db, 'grades', s.GradeCreate(
            enrollment_id=enrollment_id, midterm_grade=midterm,
            final_grade=final, remarks='Recorded by the assigned instructor',
        ), instructor)
        graded += 1
    return created, skipped, graded


def main():
    if settings.app_env == 'production':
        raise SystemExit('Refusing to populate the simulation while APP_ENV=production.')
    with SessionLocal() as db:
        users = {user.email: user for user in db.scalars(select(m.User))}
        registrar = users.get('registrar@example.com')
        if registrar is None:
            raise SystemExit('No registrar account; run scripts/seed_accounts.py first.')
        term_starts = {semester: start for semester, start, _ in TERMS}
        term_ids, terms_created, terms_skipped = seed_terms(db, registrar)
        offerings, offerings_created, offerings_skipped = seed_offerings(db, registrar, users, term_ids)
        enrollments_created, enrollments_skipped, grades_created = seed_enrollments(db, registrar, users, offerings, term_starts)
        print(f'academic terms: created {terms_created}, skipped {terms_skipped}')
        print(f'offerings: created {offerings_created}, skipped {offerings_skipped}')
        print(f'enrollments: created {enrollments_created}, skipped {enrollments_skipped}; grades created {grades_created}')
        for semester, term_id in term_ids.items():
            count = db.scalar(select(func.count()).select_from(m.CourseOffering).where(m.CourseOffering.academic_term_id == term_id))
            print(f'  {ACADEMIC_YEAR} {semester}: {count} offering(s)')
        for user in sorted((account for account in users.values() if account.role == 'STUDENT'), key=lambda account: account.id):
            student = db.scalar(select(m.Student).where(m.Student.user_id == user.id))
            enrollments = db.scalar(select(func.count()).select_from(m.Enrollment).where(m.Enrollment.student_id == student.id)) if student else 0
            marks = db.scalar(select(func.count()).select_from(m.Grade).join(m.Enrollment, m.Grade.enrollment_id == m.Enrollment.id).where(m.Enrollment.student_id == student.id)) if student else 0
            print(f'  {user.name}: {enrollments} enrollment(s), {marks} graded')


if __name__ == '__main__':
    main()
