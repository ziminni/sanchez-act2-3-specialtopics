import logging
import secrets
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from . import models as m, schemas as s, services as service
from .config import settings
from .database import get_db
from .security import DUMMY_HASH, bearer, current_user, digest_token, password_hash

ERRORS = {code: {'model': s.ErrorResponse, 'description': description, 'content': {'application/json': {'example': {'success': False, 'message': description, 'errors': {}}}}} for code, description in {400: 'Malformed request.', 401: 'Authentication required or invalid.', 403: 'Access forbidden.', 404: 'Resource not found.', 409: 'Duplicate record or conflicting state.', 422: 'Validation failed.', 500: 'Internal server error.'}.items()}
app = FastAPI(title='Student Information Management API', version='1.0.0', docs_url='/api/docs', redoc_url='/api/redoc', responses=ERRORS, description='Laboratory REST API. Login with JSON at /api/v1/auth/login, then paste access_token into Authorize. ADMIN and REGISTRAR manage academics; INSTRUCTOR reads assigned offerings and edits their grades; STUDENT reads only their own records. Grades use a 0–100 scale. All lists are paginated.')
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    detail = exc.detail if isinstance(exc.detail, dict) else {'message': str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={'success': False, 'message': detail.get('message', 'Request failed.'), 'errors': detail.get('errors', {})}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    errors = {}
    for error in exc.errors():
        field = '.'.join(str(part) for part in error['loc'] if part != 'body') or 'body'
        errors.setdefault(field, []).append(error['msg'])
    return JSONResponse(status_code=422, content={'success': False, 'message': 'Validation failed.', 'errors': errors})


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={'success': False, 'message': 'Duplicate record or record referenced by other data.', 'errors': {}})


@app.exception_handler(Exception)
async def server_error(request, exc):
    # Do not log exception text: database errors may include private parameters.
    logging.getLogger('student_api').error('Unhandled %s on %s %s', type(exc).__name__, request.method, request.url.path)
    return JSONResponse(status_code=500, content={'success': False, 'message': 'Internal server error.', 'errors': {}})


class Pagination(BaseModel):
    model_config = ConfigDict(extra='forbid')
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class CollectionParams(Pagination):
    search: str | None = Field(default=None, max_length=100)
    sort: str = Field(default='id', description='Column name; prefix with - for descending. Supported: id, timestamps, searchable columns, and resource filter columns.')
    status: str | None = None
    role: s.Role | None = None
    program_id: int | None = Field(default=None, gt=0)
    year_level: int | None = Field(default=None, ge=1, le=6)
    course_id: int | None = Field(default=None, gt=0)
    academic_term_id: int | None = Field(default=None, gt=0)
    instructor_id: int | None = Field(default=None, gt=0)
    student_id: int | None = Field(default=None, gt=0)
    course_offering_id: int | None = Field(default=None, gt=0)
    enrollment_id: int | None = Field(default=None, gt=0)


@app.get('/api/v1/health', tags=['Health'])
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return service.success({'status': 'ok'})


@app.post('/api/v1/auth/login', tags=['Authentication'], response_model=s.LoginResponse)
def login(payload: s.Login, db: Session = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == str(payload.email).lower()))
    valid = password_hash.verify(payload.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or user.status != 'ACTIVE':
        raise HTTPException(401, 'Invalid email or password.', headers={'WWW-Authenticate': 'Bearer'})
    raw = secrets.token_urlsafe(32)
    db.execute(delete(m.Token).where(m.Token.expires_at <= m.now()))
    db.add(m.Token(digest=digest_token(raw), user_id=user.id, expires_at=m.now() + timedelta(minutes=settings.token_ttl_minutes)))
    db.commit()
    return service.success({'access_token': raw, 'token_type': 'bearer', 'expires_in': settings.token_ttl_minutes * 60}, 'Login successful.')


@app.get('/api/v1/auth/me', tags=['Authentication'], response_model=s.response_schema('CurrentUserResponse', s.read_schema(s.UserCreate)))
def me(user: m.User = Depends(current_user)):
    return service.success(service.public(user))


@app.post('/api/v1/auth/logout', tags=['Authentication'], status_code=204)
def logout(user: m.User = Depends(current_user), credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    db.execute(delete(m.Token).where(m.Token.digest == digest_token(credentials.credentials)))
    db.commit()
    return Response(status_code=204)


# The factory shares HTTP plumbing; domain rules remain explicit in services.py.
def register_resource(resource, model, schema, search_fields, filters):
    path = f'/api/v1/{resource}'
    read = s.read_schema(schema)
    single = s.response_schema(f'{model.__name__}Response', read)
    multiple = s.response_schema(f'{model.__name__}ListResponse', list[read], collection=True)
    update = s.update_schema(schema)

    def list_items(params: Annotated[CollectionParams, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        return service.collection(db, resource, user, params)

    def get_item(ident: int, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        return service.success(service.present(db, [service.get_authorized(db, model, ident, user)])[0])

    def create_item(payload, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        return service.save(db, resource, payload, user)

    def update_item(ident: int, payload, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        return service.save(db, resource, payload, user, ident)

    def delete_item(ident: int, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        service.remove(db, resource, ident, user)
        return Response(status_code=204)

    create_item.__annotations__['payload'] = schema
    update_item.__annotations__['payload'] = update
    for endpoint in [list_items, get_item, create_item, update_item, delete_item]:
        endpoint.__name__ = f'{endpoint.__name__}_{resource.replace("-", "_")}'
    app.add_api_route(path, list_items, methods=['GET'], tags=[resource], response_model=multiple, summary=f'List {resource}', description=f'Paginated, role-scoped list. Search columns: {", ".join(search_fields) or "none"}. Supported filters: {", ".join(filters)}. Other filters are rejected.')
    app.add_api_route(path, create_item, methods=['POST'], tags=[resource], response_model=single, status_code=201, summary=f'Create {resource}')
    app.add_api_route(path + '/{ident}', get_item, methods=['GET'], tags=[resource], response_model=single, summary=f'Retrieve {resource}')
    app.add_api_route(path + '/{ident}', update_item, methods=['PATCH'], tags=[resource], response_model=single, summary=f'Partially update {resource}', description='Omit fields to preserve them. Null is accepted only for nullable fields. Enrollment student/offering and grade enrollment references are immutable.')
    if model is not m.Grade:
        app.add_api_route(path + '/{ident}', delete_item, methods=['DELETE'], tags=[resource], status_code=204, summary=f'Delete {resource}', description='Hard delete. Returns 409 if other academic records reference this record. Consider setting status instead.')


for resource, config in service.RESOURCES.items():
    register_resource(resource, *config)


@app.get('/api/v1/students/{ident}/enrollments', tags=['Academic Records'], response_model=s.response_schema('StudentEnrollmentsResponse', list[s.read_schema(s.EnrollmentCreate)], True))
def student_enrollments(ident: int, params: Annotated[Pagination, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    service.get_authorized(db, m.Student, ident, user)
    return service.collection(db, 'enrollments', user, CollectionParams(**params.model_dump(), student_id=ident))


@app.get('/api/v1/students/{ident}/grades', tags=['Academic Records'], response_model=s.response_schema('StudentGradesResponse', list[s.read_schema(s.GradeCreate)], True))
def student_grades(ident: int, params: Annotated[Pagination, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    service.get_authorized(db, m.Student, ident, user)
    query = service.scoped(db, m.Grade, user).where(m.Grade.enrollment_id.in_(select(m.Enrollment.id).where(m.Enrollment.student_id == ident))).order_by(m.Grade.id)
    rows, meta = service.paginated(db, query, params)
    return service.success(service.present(db, rows), meta=meta)


class RosterStudent(BaseModel):
    id: int
    student_number: str
    first_name: str
    last_name: str
    enrollment_id: int
    enrollment_status: str


@app.get('/api/v1/course-offerings/{ident}/students', tags=['course-offerings'], response_model=s.response_schema('OfferingRosterResponse', list[RosterStudent], True))
def offering_students(ident: int, params: Annotated[Pagination, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    service.get_authorized(db, m.CourseOffering, ident, user)
    query = select(m.Enrollment).where(m.Enrollment.course_offering_id == ident).order_by(m.Enrollment.id)
    enrollments, meta = service.paginated(db, query, params)
    students = {student.id: student for student in db.scalars(select(m.Student).where(m.Student.id.in_([row.student_id for row in enrollments])))}
    return service.success([{'id': row.student_id, 'student_number': students[row.student_id].student_number, 'first_name': students[row.student_id].first_name, 'last_name': students[row.student_id].last_name, 'enrollment_id': row.id, 'enrollment_status': row.status} for row in enrollments], meta=meta)


class RecordCourse(BaseModel):
    enrollment_id: int
    status: str
    course_code: str
    course_title: str
    units: float
    section: str
    midterm_grade: float | None
    final_grade: float | None
    remarks: str | None


class RecordTerm(BaseModel):
    academic_term_id: int
    academic_year: str
    semester: str
    # Computed from this term's final grades, weighted by subject units.
    gwa: float | None
    units: float
    courses: list[RecordCourse]


class RecordData(BaseModel):
    student_id: int
    student_name: str
    student_number: str
    # Computed across the whole record; clients never submit a GWA.
    gwa: float | None
    units: float
    terms: list[RecordTerm]


def record_rows(db, ident, enrollment_ids=None):
    query = select(m.Enrollment, m.CourseOffering, m.Course, m.AcademicTerm, m.Grade).join(m.CourseOffering, m.CourseOffering.id == m.Enrollment.course_offering_id).join(m.Course, m.Course.id == m.CourseOffering.course_id).join(m.AcademicTerm, m.AcademicTerm.id == m.CourseOffering.academic_term_id).outerjoin(m.Grade, m.Grade.enrollment_id == m.Enrollment.id).where(m.Enrollment.student_id == ident)
    if enrollment_ids is not None:
        query = query.where(m.Enrollment.id.in_(enrollment_ids))
    return db.execute(query.order_by(m.AcademicTerm.id, m.Enrollment.id)).all()


def accumulate_grades(rows, totals):
    # Dropped and ungraded subjects never contribute to the weighted average.
    for enrollment, _, course, _, grade in rows:
        if enrollment.status == 'DROPPED' or grade is None or grade.final_grade is None:
            continue
        totals[0] += grade.final_grade * course.units
        totals[1] += course.units


def gwa_of(totals):
    weighted, units = totals
    return (round(weighted / units, 2) if units else None), round(units, 2)


@app.get('/api/v1/students/{ident}/academic-record', tags=['Academic Records'], response_model=s.response_schema('AcademicRecordResponse', RecordData, True), description='Paginate enrollments first, then group the page by academic term. A term may span pages; follow meta to retrieve the entire record. Instructors and administrators encode each subject grade; the response adds `gwa`, computed automatically from final grades weighted by units across the whole record (dropped and ungraded subjects are excluded). A GWA is never accepted as input. Instructors may read the records of students enrolled in their classes.')
def academic_record(ident: int, params: Annotated[Pagination, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    student = service.record_student(db, ident, user)
    query = select(m.Enrollment).join(m.CourseOffering, m.CourseOffering.id == m.Enrollment.course_offering_id).where(m.Enrollment.student_id == ident).order_by(m.CourseOffering.academic_term_id, m.Enrollment.id)
    enrollments, meta = service.paginated(db, query, params)
    rows = record_rows(db, ident, [row.id for row in enrollments])
    complete = record_rows(db, ident)
    overall = [0.0, 0.0]
    per_term = {}
    for row in complete:
        accumulate_grades([row], per_term.setdefault(row[3].id, [0.0, 0.0]))
    accumulate_grades(complete, overall)
    term_scores = {term_id: gwa_of(totals) for term_id, totals in per_term.items()}
    terms = {}
    for enrollment, offering, course, term, grade in rows:
        if term.id not in terms:
            term_gwa, term_units = term_scores.get(term.id, (None, 0.0))
            terms[term.id] = {'academic_term_id': term.id, 'academic_year': term.academic_year, 'semester': term.semester, 'gwa': term_gwa, 'units': term_units, 'courses': []}
        terms[term.id]['courses'].append({'enrollment_id': enrollment.id, 'status': enrollment.status, 'course_code': course.course_code, 'course_title': course.course_title, 'units': course.units, 'section': offering.section, 'midterm_grade': grade.midterm_grade if grade else None, 'final_grade': grade.final_grade if grade else None, 'remarks': grade.remarks if grade else None})
    gwa, units = gwa_of(overall)
    return service.success({'student_id': ident, 'student_name': f'{student.first_name} {student.last_name}', 'student_number': student.student_number, 'gwa': gwa, 'units': units, 'terms': list(terms.values())}, meta=meta)


# Keep Swagger's examples and the exported specification identical.
_original_openapi = app.openapi


def documented_openapi():
    from .export_docs import enrich_openapi
    if app.openapi_schema is None:
        app.openapi_schema = enrich_openapi(_original_openapi())
    return app.openapi_schema


app.openapi = documented_openapi


class InstructorSummary(BaseModel):
    id: int
    name: str
    status: str


@app.get('/api/v1/instructors', tags=['course-offerings'], response_model=s.response_schema('InstructorDirectoryResponse', list[InstructorSummary], True), description='Minimal instructor directory for administrators and registrars to assign course offerings. Does not expose account credentials or grant user-management access.')
def instructor_directory(params: Annotated[Pagination, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    from .security import require_staff
    require_staff(user)
    query = select(m.User).where(m.User.role == 'INSTRUCTOR', m.User.status == 'ACTIVE').order_by(m.User.name, m.User.id)
    rows, meta = service.paginated(db, query, params)
    return service.success([{'id': row.id, 'name': row.name, 'status': row.status} for row in rows], meta=meta)


class TaughtSubject(BaseModel):
    course_code: str
    course_title: str
    term_name: str
    section: str
    status: str


class TaughtStudent(BaseModel):
    id: int
    student_number: str
    first_name: str
    last_name: str
    program_name: str
    year_level: int
    subjects: list[TaughtSubject]


class StudentSearch(Pagination):
    search: str | None = Field(default=None, max_length=100)


@app.get('/api/v1/my-students', tags=['Academic Records'], response_model=s.response_schema('InstructorStudentsResponse', list[TaughtStudent], True), description='Students enrolled in the signed-in instructor\'s offerings, with the subjects they take from that instructor. Contact details are not included.')
def my_students(params: Annotated[StudentSearch, Query()], db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    if user.role != 'INSTRUCTOR':
        raise HTTPException(403, 'Only instructors have a class list of their own students.')
    query = select(m.Student).where(m.Student.id.in_(service.taught_student_ids(user)))
    if params.search:
        query = query.where(or_(*(column.icontains(params.search, autoescape=True) for column in [m.Student.student_number, m.Student.first_name, m.Student.last_name])))
    students, meta = service.paginated(db, query.order_by(m.Student.last_name, m.Student.first_name, m.Student.id), params)
    programs = service.by_id(db, m.Program, [student.program_id for student in students])
    offerings = list(db.scalars(select(m.CourseOffering).where(m.CourseOffering.instructor_id == user.id)))
    names = service.offering_names(db, offerings)
    enrollments = db.scalars(select(m.Enrollment).where(m.Enrollment.student_id.in_([student.id for student in students]), m.Enrollment.course_offering_id.in_([offering.id for offering in offerings])).order_by(m.Enrollment.id)).all()
    subjects = {}
    for row in enrollments:
        offering = names[row.course_offering_id]
        subjects.setdefault(row.student_id, []).append({**{key: offering[key] for key in ['course_code', 'course_title', 'term_name', 'section']}, 'status': row.status})
    return service.success([{'id': student.id, 'student_number': student.student_number, 'first_name': student.first_name, 'last_name': student.last_name, 'program_name': programs[student.program_id].name, 'year_level': student.year_level, 'subjects': subjects.get(student.id, [])} for student in students], meta=meta)
