from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, connect_args={'check_same_thread': False, 'timeout': 30} if settings.database_url.startswith('sqlite') else {})
if engine.dialect.name == 'sqlite':
    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request):
    with SessionLocal() as db:
        # Serialize SQLite writes before reading capacity or permission state.
        if engine.dialect.name == 'sqlite' and request.method in {'POST', 'PATCH', 'PUT', 'DELETE'}:
            db.connection().exec_driver_sql('BEGIN IMMEDIATE')
        try:
            yield db
        finally:
            db.rollback()
