import os

# Regression tests use a deliberate origin allowlist, independent of local .env.
os.environ["CORS_ORIGINS"] = '["http://127.0.0.1:5173"]'

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app import models as m
from app.security import password_hash

PASSWORD = 'Local-testing-password-123!'


@pytest.fixture(scope='session')
def hashed_password():
    return password_hash.hash(PASSWORD)


@pytest.fixture
def setup(hashed_password):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        users = [m.User(id=i, name=role, email=f'{name}@example.com', role=role, status='ACTIVE', password_hash=hashed_password) for i, name, role in [(1, 'admin', 'ADMIN'), (2, 'registrar', 'REGISTRAR'), (3, 'instructor', 'INSTRUCTOR'), (4, 'otherinstructor', 'INSTRUCTOR'), (5, 'student', 'STUDENT'), (6, 'otherstudent', 'STUDENT')]]
        db.add_all(users)
        db.add(m.Program(id=1, code='BSIT', name='Information Technology', status='ACTIVE'))
        db.flush()
        db.add(m.Course(id=1, program_id=1, course_code='IT101', course_title='Programming', units=3, status='ACTIVE'))
        db.add(m.AcademicTerm(id=1, academic_year='2026-2027', semester='FIRST', start_date=date(2026, 8, 1), end_date=date(2026, 12, 20), status='ACTIVE'))
        db.flush()
        db.add_all([m.Student(id=i, user_id=user_id, student_number=f'2026-0000{i}', first_name=first, last_name=last, program_id=1, year_level=i, status='ACTIVE') for i, user_id, first, last in [(1, 5, 'Ana', 'Dela Cruz'), (2, 6, 'Ben', 'Santos')]])
        db.add_all([m.CourseOffering(id=i, course_id=1, academic_term_id=1, instructor_id=instructor, section=f'A{i}', capacity=2, status='ACTIVE') for i, instructor in [(1, 3), (2, 4)]])
        db.flush()
        db.add_all([m.Enrollment(id=i, student_id=i, course_offering_id=i, enrollment_date=date(2026, 8, 1), status='ENROLLED') for i in [1, 2]])
        db.flush()
        db.add(m.Grade(id=1, enrollment_id=1, midterm_grade=80, final_grade=90))
        db.commit()
    def override_db():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(setup):
    return setup[0]


@pytest.fixture
def auth(client):
    cache = {}
    def headers(name='admin'):
        if name not in cache:
            response = client.post('/api/v1/auth/login', json={'email': f'{name}@example.com', 'password': PASSWORD})
            assert response.status_code == 200, response.text
            cache[name] = {'Authorization': 'Bearer ' + response.json()['data']['access_token']}
        return cache[name]
    return headers
