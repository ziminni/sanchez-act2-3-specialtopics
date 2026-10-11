"""Create or refresh the laboratory accounts and their linked student profiles.

This re-initializes the sign-in set on a development database: every account gets a
real display name, an ACTIVE status and the password from the local `SEED_PASSWORD`
setting, and the update revokes any stored session token for that account. Five
STUDENT accounts are linked to five student profiles, so the student portal, grades
and GWA views can be demonstrated without inventing records by hand.

Existing emails and student numbers are updated in place, which makes repeat runs safe.
No terms, offerings, enrollments or grades are created.

Usage from the project root:

    python scripts/seed_accounts.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app import models as m
from app import schemas as s
from app import services as service
from app.config import settings
from app.database import SessionLocal

ACCOUNTS = [
    ('admin@example.com', 'Rafael Antonio Mercado', 'ADMIN'),
    ('registrar@example.com', 'Lucia Maribel Fernandez', 'REGISTRAR'),
    ('instructor@example.com', 'Miguel Angelo Villanueva', 'INSTRUCTOR'),
    ('instructor2@example.com', 'Teresa Corazon Bautista', 'INSTRUCTOR'),
    ('student@example.com', 'Ana Lourdes Dela Cruz', 'STUDENT'),
    ('student2@example.com', 'Juan Carlo Santos', 'STUDENT'),
    ('student3@example.com', 'Maria Sofia Reyes', 'STUDENT'),
    ('student4@example.com', 'Paolo Miguel Garcia', 'STUDENT'),
    ('student5@example.com', 'Beatrice Anne Lim', 'STUDENT'),
]

STUDENT_PROFILES = [
    {'email': 'student@example.com', 'student_number': '2026-00101', 'first_name': 'Ana', 'middle_name': 'Lourdes', 'last_name': 'Dela Cruz', 'program': 'BSIT', 'year_level': 3, 'birth_date': date(2004, 5, 12), 'contact_number': '0917-201-0145', 'address': '12 Mabini Street, Quezon City'},
    {'email': 'student2@example.com', 'student_number': '2026-00102', 'first_name': 'Juan', 'middle_name': 'Carlo', 'last_name': 'Santos', 'program': 'BSIT', 'year_level': 2, 'birth_date': date(2005, 2, 8), 'contact_number': '0918-442-7788', 'address': '45 Rizal Avenue, Pasig City'},
    {'email': 'student3@example.com', 'student_number': '2026-00103', 'first_name': 'Maria', 'middle_name': 'Sofia', 'last_name': 'Reyes', 'program': 'BSCS', 'year_level': 1, 'birth_date': date(2006, 9, 21), 'contact_number': '0920-335-9012', 'address': '8 Katipunan Street, Marikina City'},
    {'email': 'student4@example.com', 'student_number': '2026-00104', 'first_name': 'Paolo', 'middle_name': 'Miguel', 'last_name': 'Garcia', 'program': 'BSIS', 'year_level': 4, 'birth_date': date(2003, 11, 3), 'contact_number': '0917-889-3321', 'address': '77 Del Pilar Street, Makati City'},
    {'email': 'student5@example.com', 'student_number': '2026-00105', 'first_name': 'Beatrice', 'middle_name': 'Anne', 'last_name': 'Lim', 'program': 'BSCS', 'year_level': 2, 'birth_date': date(2005, 6, 30), 'contact_number': '0919-774-2256', 'address': '231 Bonifacio Street, Taguig City'},
]


def reset_accounts(db, admin):
    created, updated = 0, 0
    for email, name, role in ACCOUNTS:
        payload = s.UserCreate(name=name, email=email, password=settings.seed_password, role=role, status='ACTIVE')
        existing = db.scalar(select(m.User).where(m.User.email == email))
        if existing is None:
            service.save(db, 'users', payload, admin)
            created += 1
        else:
            # Re-submitting the password re-hashes it and revokes that account's tokens.
            service.save(db, 'users', payload, admin, existing.id)
            updated += 1
    return created, updated


def reset_students(db, admin):
    account_ids = {user.email: user.id for user in db.scalars(select(m.User))}
    program_ids = {program.code: program.id for program in db.scalars(select(m.Program))}
    created, updated = 0, 0
    for profile in STUDENT_PROFILES:
        if profile['program'] not in program_ids:
            raise SystemExit(f"Program {profile['program']} is missing; run scripts/seed_catalog.py first.")
        payload = s.StudentCreate(
            user_id=account_ids[profile['email']],
            student_number=profile['student_number'],
            first_name=profile['first_name'],
            middle_name=profile['middle_name'],
            last_name=profile['last_name'],
            birth_date=profile['birth_date'],
            email=profile['email'],
            contact_number=profile['contact_number'],
            address=profile['address'],
            program_id=program_ids[profile['program']],
            year_level=profile['year_level'],
            status='ACTIVE',
        )
        existing = db.scalar(select(m.Student).where(m.Student.student_number == profile['student_number']))
        if existing is None:
            service.save(db, 'students', payload, admin)
            created += 1
        else:
            service.save(db, 'students', payload, admin, existing.id)
            updated += 1
    return created, updated


def main():
    if len(settings.seed_password) < 12:
        raise SystemExit('Set SEED_PASSWORD to at least 12 characters in your local .env.')
    if settings.app_env == 'production':
        raise SystemExit('Refusing to re-initialize accounts while APP_ENV=production.')
    with SessionLocal() as db:
        admin = db.scalar(select(m.User).where(m.User.role == 'ADMIN').order_by(m.User.id))
        if admin is None:
            raise SystemExit('No ADMIN account exists yet; create the first administrator before running this script.')
        accounts_created, accounts_updated = reset_accounts(db, admin)
        students_created, students_updated = reset_students(db, admin)
        print(f'accounts: created {accounts_created}, reset {accounts_updated} (password = local SEED_PASSWORD, tokens revoked)')
        print(f'student profiles: created {students_created}, updated {students_updated}')
        for user in db.scalars(select(m.User).order_by(m.User.role, m.User.id)):
            student = db.scalar(select(m.Student).where(m.Student.user_id == user.id))
            link = f'student {student.student_number}' if student else 'no student profile'
            print(f'  {user.role:<10} {user.email:<24} {user.name} ({link})')
        print('No terms, offerings, enrollments or grades were created.')


if __name__ == '__main__':
    main()
