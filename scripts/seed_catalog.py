"""Populate the academic catalog (programs and their subjects) in a development database.

The full laboratory seeder (`app/seed.py`) also creates terms, offerings, students,
enrollments and grades. This script adds only the catalog, and it writes through the
same service layer the API uses, so schema validation and the program reference check
still apply. Programs and subjects whose code already exists are skipped, which makes
repeat runs safe.

Every subject belongs to exactly one program because `courses.program_id` is required
by the schema; shared general-education subjects would need a schema change.

Usage from the project root:

    python scripts/seed_catalog.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app import models as m
from app import schemas as s
from app import services as service
from app.database import SessionLocal

PROGRAMS = [
    {'code': 'BSIT', 'name': 'Bachelor of Science in Information Technology', 'description': 'Software development, networking, database administration and IT support.'},
    {'code': 'BSCS', 'name': 'Bachelor of Science in Computer Science', 'description': 'Algorithms, systems software, artificial intelligence and computing theory.'},
    {'code': 'BSIS', 'name': 'Bachelor of Science in Information Systems', 'description': 'Business processes, enterprise systems and data-driven decision support.'},
]

SUBJECTS = [
    ('BSIT', 'IT101', 'Introduction to Information Technology', 3, 'Computing fundamentals, hardware, software and IT career paths.'),
    ('BSIT', 'IT102', 'Computer Programming 1', 3, 'Problem solving, algorithms and structured programming.'),
    ('BSIT', 'IT201', 'Computer Programming 2', 3, 'Object-oriented design, modules and reusable components.'),
    ('BSIT', 'IT202', 'Data Structures and Algorithms', 3, 'Lists, trees, graphs, searching, sorting and complexity.'),
    ('BSIT', 'IT203', 'Database Management Systems', 3, 'Relational modelling, SQL, normalization and transactions.'),
    ('BSIT', 'IT204', 'Networking 1', 3, 'Network models, addressing, routing and troubleshooting basics.'),
    ('BSIT', 'IT205', 'Web Systems and Technologies', 3, 'Client and server web development with REST services.'),
    ('BSIT', 'IT301', 'Systems Integration and Architecture', 3, 'Enterprise integration patterns and layered architectures.'),
    ('BSIT', 'IT302', 'Information Assurance and Security', 3, 'Threat models, access control and secure development practice.'),
    ('BSIT', 'IT303', 'Capstone Project 1', 3, 'Team proposal, requirements and prototype for the capstone.'),
    ('BSIT', 'IT304', 'IT Seminar', 1, 'Current industry practice and professional ethics discussions.'),
    ('BSCS', 'CS101', 'Introduction to Computer Science', 3, 'Computational thinking and the discipline of computing.'),
    ('BSCS', 'CS102', 'Discrete Structures', 3, 'Logic, sets, relations, graphs and proof techniques.'),
    ('BSCS', 'CS201', 'Data Structures and Algorithms', 3, 'Algorithm design, analysis and advanced data structures.'),
    ('BSCS', 'CS202', 'Object-Oriented Programming', 3, 'Abstraction, inheritance, polymorphism and design patterns.'),
    ('BSCS', 'CS203', 'Operating Systems', 3, 'Processes, memory, scheduling, file systems and concurrency.'),
    ('BSCS', 'CS204', 'Automata Theory and Formal Languages', 3, 'Finite automata, grammars and computability.'),
    ('BSCS', 'CS301', 'Software Engineering', 3, 'Requirements, design, testing and team development process.'),
    ('BSCS', 'CS302', 'Artificial Intelligence', 3, 'Search, knowledge representation and introductory learning.'),
    ('BSCS', 'CS303', 'Compiler Design', 3, 'Lexical analysis, parsing and code generation.'),
    ('BSCS', 'CS304', 'Research Methods in Computing', 2, 'Literature review, experiment design and technical writing.'),
    ('BSIS', 'IS101', 'Foundations of Information Systems', 3, 'Information systems in organizations and their value.'),
    ('BSIS', 'IS102', 'Business Process Management', 3, 'Modeling, measuring and improving organizational processes.'),
    ('BSIS', 'IS201', 'Systems Analysis and Design', 3, 'Requirements gathering, modeling and solution design.'),
    ('BSIS', 'IS202', 'Database Design for Information Systems', 3, 'Business data modelling, SQL and reporting structures.'),
    ('BSIS', 'IS203', 'Enterprise Systems', 3, 'ERP and CRM concepts, configuration and process fit.'),
    ('BSIS', 'IS301', 'Information Systems Project Management', 3, 'Scheduling, risk, stakeholder and delivery management.'),
    ('BSIS', 'IS302', 'Data Analytics for Business', 3, 'Descriptive and predictive analysis for decision support.'),
    ('BSIS', 'IS303', 'IT Service Management', 3, 'Service strategy, incident handling and continual improvement.'),
]


def existing_ids(db, model, column, codes):
    rows = db.scalars(select(model).where(getattr(model, column).in_(codes)))
    return {getattr(row, column): row.id for row in rows}


def main():
    with SessionLocal() as db:
        admin = db.scalar(select(m.User).where(m.User.role == 'ADMIN').order_by(m.User.id))
        if admin is None:
            raise SystemExit('No ADMIN account found. Create one before populating the catalog.')

        program_ids = existing_ids(db, m.Program, 'code', [program['code'] for program in PROGRAMS])
        skipped_programs = len(program_ids)
        for payload in PROGRAMS:
            if payload['code'] in program_ids:
                continue
            # The service layer performs the same validation the API route would.
            created = service.save(db, 'programs', s.ProgramCreate(**payload), admin)
            program_ids[payload['code']] = created['data']['id']

        course_ids = existing_ids(db, m.Course, 'course_code', [subject[1] for subject in SUBJECTS])
        skipped_subjects = len(course_ids)
        for program_code, course_code, title, units, description in SUBJECTS:
            if course_code in course_ids:
                continue
            created = service.save(db, 'courses', s.CourseCreate(program_id=program_ids[program_code], course_code=course_code, course_title=title, units=units, description=description), admin)
            course_ids[course_code] = created['data']['id']

        print(f'programs: created {len(program_ids) - skipped_programs}, skipped {skipped_programs}')
        print(f'subjects: created {len(course_ids) - skipped_subjects}, skipped {skipped_subjects}')
        for program in db.scalars(select(m.Program).order_by(m.Program.code)):
            total = db.scalar(select(func.count()).select_from(m.Course).where(m.Course.program_id == program.id))
            print(f'  {program.code}: {total} subject(s)')
        print('Accounts were not modified; no terms, offerings, students, enrollments or grades were created.')


if __name__ == '__main__':
    main()
