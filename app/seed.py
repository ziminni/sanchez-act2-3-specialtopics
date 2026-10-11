"""Generate deterministic synthetic laboratory data into an empty migrated DB."""
from datetime import date
from sqlalchemy import func, select
from .config import settings
from .database import SessionLocal
from . import models as m
from .security import password_hash


def seed():
    if len(settings.seed_password) < 12:
        raise SystemExit('Set SEED_PASSWORD to at least 12 characters in your local .env.')
    with SessionLocal() as db:
        models = [m.User, m.Program, m.Student, m.Course, m.AcademicTerm, m.CourseOffering, m.Enrollment, m.Grade]
        if any(db.scalar(select(func.count()).select_from(model)) for model in models):
            raise SystemExit('Seeder requires an empty database; existing data was left unchanged.')
        users = []
        for name, email, role in [('Admin User', 'admin@example.com', 'ADMIN'), ('Registrar User', 'registrar@example.com', 'REGISTRAR'), ('Instructor One', 'instructor@example.com', 'INSTRUCTOR'), ('Instructor Two', 'instructor2@example.com', 'INSTRUCTOR'), ('Student One', 'student@example.com', 'STUDENT')]:
            users.append(m.User(name=name, email=email, role=role, status='ACTIVE', password_hash=password_hash.hash(settings.seed_password)))
        db.add_all(users)
        programs = [m.Program(code=code, name=name, status='ACTIVE') for code, name in [('BSIT', 'Bachelor of Science in Information Technology'), ('BSCS', 'Bachelor of Science in Computer Science'), ('BSIS', 'Bachelor of Science in Information Systems')]]
        db.add_all(programs)
        db.flush()
        courses = [m.Course(program_id=programs[(i - 1) % 3].id, course_code=f'IT{i:03}', course_title=f'Computing Subject {i}', units=3, description='Synthetic demonstration subject', status='ACTIVE') for i in range(1, 21)]
        db.add_all(courses)
        terms = [m.AcademicTerm(academic_year='2026-2027', semester='FIRST', start_date=date(2026, 8, 1), end_date=date(2026, 12, 20), status='ACTIVE'), m.AcademicTerm(academic_year='2026-2027', semester='SECOND', start_date=date(2027, 1, 5), end_date=date(2027, 5, 30), status='ACTIVE')]
        db.add_all(terms)
        db.flush()
        students = [m.Student(student_number=f'2026-{i:05}', first_name=f'Student{i:03}', last_name=f'Family{i:03}', email=f'student{i}@example.com', program_id=programs[(i - 1) % 3].id, year_level=(i - 1) % 4 + 1, user_id=users[4].id if i == 1 else None, status='ACTIVE') for i in range(1, 101)]
        offerings = [m.CourseOffering(course_id=course.id, academic_term_id=terms[i // 10].id, instructor_id=users[2 + i % 2].id, section='A', schedule='Monday 09:00-10:30', room=f'R{i + 1}', capacity=40, status='ACTIVE') for i, course in enumerate(courses)]
        db.add_all(students + offerings)
        db.flush()
        enrollments = []
        for i, student in enumerate(students):
            for offset in [0, 10]:
                enrollments.append(m.Enrollment(student_id=student.id, course_offering_id=offerings[i % 10 + offset].id, enrollment_date=terms[offset // 10].start_date, status='ENROLLED'))
        db.add_all(enrollments)
        db.flush()
        db.add_all([m.Grade(enrollment_id=enrollment.id, midterm_grade=75 + i % 26, final_grade=75 + i % 26, remarks='Synthetic demonstration grade') for i, enrollment in enumerate(enrollments[:100])])
        db.commit()
        print('Seeded 5 users, 3 programs, 100 students, 20 courses, 2 terms, 20 offerings, 200 enrollments, 100 grades.')
        print('Demo login: admin@example.com (password from your local SEED_PASSWORD).')


if __name__ == '__main__':
    seed()
