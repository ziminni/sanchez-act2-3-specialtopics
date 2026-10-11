from datetime import date, datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def now():
    # SQLite stores UTC timestamps without a timezone offset.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class User(TimestampMixin, Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('ADMIN','REGISTRAR','INSTRUCTOR','STUDENT')"), CheckConstraint("status IN ('ACTIVE','INACTIVE')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class Token(Base):
    __tablename__ = 'tokens'
    id: Mapped[int] = mapped_column(primary_key=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Program(TimestampMixin, Base):
    __tablename__ = 'programs'
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','INACTIVE')"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class Student(TimestampMixin, Base):
    __tablename__ = 'students'
    __table_args__ = (CheckConstraint('year_level BETWEEN 1 AND 6'), CheckConstraint("status IN ('ACTIVE','INACTIVE')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), unique=True)
    student_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    suffix: Mapped[str | None] = mapped_column(String(20))
    birth_date: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(254))
    contact_number: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[int] = mapped_column(ForeignKey('programs.id', ondelete='RESTRICT'), index=True)
    year_level: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class Course(TimestampMixin, Base):
    __tablename__ = 'courses'
    __table_args__ = (CheckConstraint('units > 0 AND units <= 12'), CheckConstraint("status IN ('ACTIVE','INACTIVE')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey('programs.id', ondelete='RESTRICT'), index=True)
    course_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    course_title: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    units: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class AcademicTerm(TimestampMixin, Base):
    __tablename__ = 'academic_terms'
    __table_args__ = (UniqueConstraint('academic_year', 'semester'), CheckConstraint('end_date >= start_date'), CheckConstraint("status IN ('ACTIVE','INACTIVE')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year: Mapped[str] = mapped_column(String(20))
    semester: Mapped[str] = mapped_column(String(30))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class CourseOffering(TimestampMixin, Base):
    __tablename__ = 'course_offerings'
    __table_args__ = (UniqueConstraint('course_id', 'academic_term_id', 'section'), CheckConstraint('capacity > 0'), CheckConstraint("status IN ('ACTIVE','INACTIVE')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id', ondelete='RESTRICT'), index=True)
    academic_term_id: Mapped[int] = mapped_column(ForeignKey('academic_terms.id', ondelete='RESTRICT'), index=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    section: Mapped[str] = mapped_column(String(30))
    schedule: Mapped[str | None] = mapped_column(String(200))
    room: Mapped[str | None] = mapped_column(String(50))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE')


class Enrollment(TimestampMixin, Base):
    __tablename__ = 'enrollments'
    __table_args__ = (UniqueConstraint('student_id', 'course_offering_id'), CheckConstraint("status IN ('ENROLLED','DROPPED','COMPLETED')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id', ondelete='RESTRICT'), index=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey('course_offerings.id', ondelete='RESTRICT'), index=True)
    enrollment_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default='ENROLLED')


class Grade(TimestampMixin, Base):
    __tablename__ = 'grades'
    __table_args__ = (CheckConstraint('midterm_grade IS NULL OR midterm_grade BETWEEN 0 AND 100'), CheckConstraint('final_grade IS NULL OR final_grade BETWEEN 0 AND 100'))
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey('enrollments.id', ondelete='RESTRICT'), unique=True)
    midterm_grade: Mapped[float | None] = mapped_column(Float)
    final_grade: Mapped[float | None] = mapped_column(Float)
    remarks: Mapped[str | None] = mapped_column(String(250))


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    # The account may be deleted later; actor keeps a readable snapshot.
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    actor: Mapped[str] = mapped_column(String(300))
    action: Mapped[str] = mapped_column(String(30), index=True)
    resource: Mapped[str | None] = mapped_column(String(40))
    record_id: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(64))


class SystemSetting(Base):
    __tablename__ = 'system_settings'
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    # JSON-encoded value; defaults live in app/system.py.
    value: Mapped[str] = mapped_column(Text)


class RolePermission(Base):
    """An administrator's override of one built-in role permission."""
    __tablename__ = 'role_permissions'
    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    module: Mapped[str] = mapped_column(String(40), primary_key=True)
    action: Mapped[str] = mapped_column(String(10), primary_key=True)
    allowed: Mapped[bool] = mapped_column(Boolean)
