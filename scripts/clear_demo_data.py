"""Remove demonstration records from a development database, keeping the login accounts.

`app/seed.py` fills an empty migrated database with synthetic students, subjects,
terms, offerings, enrollments and grades. This maintenance script does the reverse
for a development database: it deletes those academic rows plus stored session
tokens, but leaves the five accounts you sign in with so the application can hold
real records entered by hand.

Usage from the project root:

    python scripts/clear_demo_data.py --yes

A timestamped copy of the SQLite file is written before anything is deleted. The
seeder refuses to run afterwards because accounts already exist, so the cleared
database cannot be silently re-filled with demonstration data.
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select

from app import models as m
from app.config import settings
from app.database import SessionLocal

# Children before parents: foreign keys restrict deleting a referenced record.
ACADEMIC_MODELS = [m.Grade, m.Enrollment, m.CourseOffering, m.Course, m.AcademicTerm, m.Student, m.Program]
REPORTED_MODELS = [*ACADEMIC_MODELS, m.Token]


def sqlite_backup():
    if not settings.database_url.startswith('sqlite'):
        return None
    path = Path(settings.database_url.split('///')[-1])
    if not path.exists():
        return None
    target = path.with_name(f'{path.name}-before-clear-{datetime.now():%Y%m%d%H%M%S}')
    shutil.copy2(path, target)
    return target


def counts(db, models):
    return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) for model in models}


def main():
    if '--yes' not in sys.argv:
        raise SystemExit('This deletes demonstration academic records. Re-run with --yes to confirm.')
    if settings.app_env == 'production':
        raise SystemExit('Refusing to clear records while APP_ENV=production.')
    backup = sqlite_backup()
    if backup:
        print(f'Backup written to {backup.name}')
    with SessionLocal() as db:
        before = counts(db, REPORTED_MODELS)
        for model in ACADEMIC_MODELS:
            db.execute(delete(model))
        # Demonstration sessions are revoked as well; accounts themselves are kept.
        db.execute(delete(m.Token))
        db.commit()
        after = counts(db, REPORTED_MODELS)
        users = db.scalar(select(func.count()).select_from(m.User))
    for table, removed in before.items():
        print(f'{table}: removed {removed}, remaining {after[table]}')
    print(f'users: kept {users} login account(s)')
    print('Next: sign in with an existing account and create real records. app.seed now refuses to run here (accounts exist).')


if __name__ == '__main__':
    main()
