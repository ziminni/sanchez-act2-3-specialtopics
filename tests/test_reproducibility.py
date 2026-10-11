import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_migrations_seeding_and_recreation(tmp_path):
    database = tmp_path / 'recreated.db'
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{database}', 'SEED_PASSWORD': 'Synthetic-integration-password'}
    def run(*args, expected=0):
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode == expected, result.stdout + result.stderr
        return result
    run('-m', 'alembic', 'upgrade', 'head')
    run('-m', 'app.seed')
    with sqlite3.connect(database) as db:
        for table, count in {'users': 5, 'programs': 3, 'students': 100, 'courses': 20, 'academic_terms': 2, 'course_offerings': 20, 'enrollments': 200, 'grades': 100}.items():
            assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == count
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute('SELECT user_id FROM students WHERE id=1').fetchone()[0] == 5
    assert 'existing data was left unchanged' in run('-m', 'app.seed', expected=1).stderr
    run('-m', 'alembic', 'check')
    run('-m', 'alembic', 'downgrade', 'base')
    run('-m', 'alembic', 'upgrade', 'head')
    run('-m', 'app.seed')


def test_concurrent_last_seat_is_not_overbooked(tmp_path):
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{tmp_path / "capacity.db"}', 'SEED_PASSWORD': 'Synthetic-capacity-password'}
    for args in [('-m', 'alembic', 'upgrade', 'head'), ('-m', 'app.seed')]:
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    script = '''
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.main import app
from app.database import SessionLocal
from app.models import CourseOffering, Enrollment
from app.config import settings
with SessionLocal() as db:
    offering = CourseOffering(course_id=1, academic_term_id=1, instructor_id=3, section='LAST-SEAT', capacity=1, status='ACTIVE')
    db.add(offering)
    db.commit()
    offering_id = offering.id
with TestClient(app) as client:
    login = client.post('/api/v1/auth/login', json={'email':'admin@example.com','password':settings.seed_password})
    headers = {'Authorization':'Bearer ' + login.json()['data']['access_token']}
    def enroll(student_id):
        return client.post('/api/v1/enrollments', headers=headers, json={'student_id':student_id,'course_offering_id':offering_id}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(enroll, [1,2]))
    assert statuses == [201,409], statuses
with SessionLocal() as db:
    assert db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.course_offering_id == offering_id)) == 1
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
