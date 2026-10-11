"""Shared resource operations and explicit academic/authorization rules."""
from math import ceil
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, func, or_, select
from . import models as m, schemas as s
from .security import password_hash, require_staff

RESOURCES = {
    'users': (m.User, s.UserCreate, ['name', 'email'], ['role', 'status']),
    'programs': (m.Program, s.ProgramCreate, ['code', 'name'], ['status']),
    'students': (m.Student, s.StudentCreate, ['student_number', 'first_name', 'last_name'], ['program_id', 'year_level', 'status']),
    'courses': (m.Course, s.CourseCreate, ['course_code', 'course_title'], ['program_id', 'status']),
    'academic-terms': (m.AcademicTerm, s.TermCreate, ['academic_year', 'semester'], ['status']),
    'course-offerings': (m.CourseOffering, s.OfferingCreate, ['section', 'schedule', 'room'], ['course_id', 'academic_term_id', 'instructor_id', 'status']),
    'enrollments': (m.Enrollment, s.EnrollmentCreate, [], ['student_id', 'course_offering_id', 'status']),
    'grades': (m.Grade, s.GradeCreate, ['remarks'], ['enrollment_id']),
}


def public(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns if column.name not in {'password_hash', 'digest'}}


def by_id(db, model, ids):
    ids = {ident for ident in ids if ident is not None}
    return {obj.id: obj for obj in db.scalars(select(model).where(model.id.in_(ids)))} if ids else {}


def term_name(term):
    return f'{term.academic_year} {term.semester.title()} semester'


def offering_names(db, offerings):
    courses = by_id(db, m.Course, [offering.course_id for offering in offerings])
    terms = by_id(db, m.AcademicTerm, [offering.academic_term_id for offering in offerings])
    instructors = by_id(db, m.User, [offering.instructor_id for offering in offerings])
    return {offering.id: {
        'course_code': courses[offering.course_id].course_code,
        'course_title': courses[offering.course_id].course_title,
        'term_name': term_name(terms[offering.academic_term_id]),
        'section': offering.section,
        'instructor_name': instructors[offering.instructor_id].name,
    } for offering in offerings}


def enrollment_names(db, enrollments):
    students = by_id(db, m.Student, [row.student_id for row in enrollments])
    offerings = offering_names(db, by_id(db, m.CourseOffering, [row.course_offering_id for row in enrollments]).values())
    names = {}
    for row in enrollments:
        student = students[row.student_id]
        offering = offerings[row.course_offering_id]
        names[row.id] = {
            'student_name': f'{student.first_name} {student.last_name}',
            'student_number': student.student_number,
            **{key: offering[key] for key in ['course_code', 'course_title', 'term_name', 'section']},
        }
    return names


def present(db, rows):
    """Public fields plus the readable names of each referenced record."""
    data = [public(row) for row in rows]
    if not rows:
        return data
    model = type(rows[0])
    if model in {m.Student, m.Course}:
        programs = by_id(db, m.Program, [row.program_id for row in rows])
        for item in data:
            item['program_name'] = programs[item['program_id']].name
    if model is m.Student:
        accounts = by_id(db, m.User, [row.user_id for row in rows])
        for item in data:
            item['account_email'] = accounts[item['user_id']].email if item['user_id'] in accounts else None
    if model is m.CourseOffering:
        names = offering_names(db, rows)
        for item in data:
            item.update({key: value for key, value in names[item['id']].items() if key != 'section'})
    if model is m.Enrollment:
        names = enrollment_names(db, rows)
        for item in data:
            item.update(names[item['id']])
    if model is m.Grade:
        names = enrollment_names(db, list(by_id(db, m.Enrollment, [row.enrollment_id for row in rows]).values()))
        for item in data:
            item.update(names[item['enrollment_id']])
    return data


def success(data, message='Request successful.', **extra):
    return {'success': True, 'message': message, 'data': data, **extra}


def lookup(db, model, ident):
    obj = db.get(model, ident)
    if obj is None:
        raise HTTPException(404, 'Resource not found.')
    return obj


def own_student_id(db, user):
    return db.scalar(select(m.Student.id).where(m.Student.user_id == user.id))


def scoped(db, model, user):
    query = select(model)
    if model is m.User:
        if user.role != 'ADMIN':
            raise HTTPException(403, 'Only administrators may manage users.')
        return query
    if user.role == 'REGISTRAR' and model is m.Grade:
        # Grading is the assigned instructor's task; administrators keep oversight.
        # Registrars still read academic records, which expose grades and the computed GWA.
        raise HTTPException(403, 'Only instructors and administrators may access grade records.')
    if user.role in {'ADMIN', 'REGISTRAR'}:
        return query
    if user.role == 'STUDENT':
        student_id = own_student_id(db, user)
        if model is m.Student:
            return query.where(m.Student.id == student_id)
        if model is m.Enrollment:
            return query.where(m.Enrollment.student_id == student_id)
        if model is m.Grade:
            return query.where(m.Grade.enrollment_id.in_(select(m.Enrollment.id).where(m.Enrollment.student_id == student_id)))
    if user.role == 'INSTRUCTOR':
        offering_ids = select(m.CourseOffering.id).where(m.CourseOffering.instructor_id == user.id)
        if model is m.CourseOffering:
            return query.where(m.CourseOffering.instructor_id == user.id)
        if model is m.Enrollment:
            return query.where(m.Enrollment.course_offering_id.in_(offering_ids))
        if model is m.Grade:
            return query.where(m.Grade.enrollment_id.in_(select(m.Enrollment.id).where(m.Enrollment.course_offering_id.in_(offering_ids))))
        if model in {m.Course, m.AcademicTerm}:
            foreign = m.CourseOffering.course_id if model is m.Course else m.CourseOffering.academic_term_id
            return query.where(model.id.in_(select(foreign).where(m.CourseOffering.instructor_id == user.id)))
    raise HTTPException(403, 'Your role cannot access this resource.')


def taught_student_ids(user):
    # Students enrolled in at least one of the instructor's offerings.
    offering_ids = select(m.CourseOffering.id).where(m.CourseOffering.instructor_id == user.id)
    return select(m.Enrollment.student_id).where(m.Enrollment.course_offering_id.in_(offering_ids))


def record_student(db, ident, user):
    """The student whose academic record this user may read."""
    if user.role != 'INSTRUCTOR':
        return get_authorized(db, m.Student, ident, user)
    student = lookup(db, m.Student, ident)
    if db.scalar(select(func.count()).select_from(taught_student_ids(user).where(m.Enrollment.student_id == ident).subquery())) == 0:
        raise HTTPException(403, 'You can only view academic records of students in your classes.')
    return student


def get_authorized(db, model, ident, user):
    query = scoped(db, model, user)
    obj = db.scalar(query.where(model.id == ident))
    if obj is None:
        lookup(db, model, ident)
        raise HTTPException(403, 'You do not have access to this record.')
    return obj


def paginated(db, query, params):
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = db.scalars(query.offset((params.page - 1) * params.per_page).limit(params.per_page)).all()
    return rows, {'page': params.page, 'per_page': params.per_page, 'total': total, 'last_page': max(1, ceil(total / params.per_page))}


def collection(db, resource, user, params):
    model, _, search_fields, filters = RESOURCES[resource]
    query = scoped(db, model, user)
    if params.search:
        if not search_fields:
            raise HTTPException(422, 'Search is not supported for this resource.')
        query = query.where(or_(*(getattr(model, name).icontains(params.search, autoescape=True) for name in search_fields)))
    for field, value in params.model_dump(exclude={'page', 'per_page', 'sort', 'search'}).items():
        if value is not None:
            if field not in filters:
                raise HTTPException(422, f'Filter {field} is not supported for this resource.')
            query = query.where(getattr(model, field) == value)
    sort_field = params.sort.lstrip('-')
    allowed = {'id', 'created_at', 'updated_at', *search_fields, *filters}
    if sort_field not in allowed:
        raise HTTPException(422, f'Invalid sort field. Allowed: {", ".join(sorted(allowed))}.')
    col = getattr(model, sort_field)
    query = query.order_by(col.desc() if params.sort.startswith('-') else col.asc(), model.id.asc())
    rows, meta = paginated(db, query, params)
    return success(present(db, rows), meta=meta)


def reference(db, model, ident, field):
    obj = db.get(model, ident)
    if obj is None:
        raise HTTPException(422, {'message': 'Validation failed.', 'errors': {field: ['Referenced record does not exist.']}})
    return obj


def grade_permission(db, enrollment_id, user):
    enrollment = reference(db, m.Enrollment, enrollment_id, 'enrollment_id')
    offering = lookup(db, m.CourseOffering, enrollment.course_offering_id)
    if user.role == 'INSTRUCTOR' and offering.instructor_id == user.id:
        return enrollment
    if user.role != 'ADMIN':
        raise HTTPException(403, 'Only the assigned instructor or an administrator may record grades.')
    return enrollment


def validate_business(db, model, data, user, existing=None):
    if model is m.User:
        if user.role != 'ADMIN':
            raise HTTPException(403, 'Only administrators may manage users.')
        if existing:
            if existing.id == user.id and (data['role'] != 'ADMIN' or data['status'] != 'ACTIVE'):
                raise HTTPException(409, 'An administrator cannot disable or demote their own account.')
            if data['role'] != existing.role:
                linked = db.scalar(select(m.Student.id).where(m.Student.user_id == existing.id))
                assigned = db.scalar(select(m.CourseOffering.id).where(m.CourseOffering.instructor_id == existing.id))
                if linked or assigned:
                    raise HTTPException(409, 'Remove student or instructor assignments before changing the role.')
        data['email'] = str(data['email']).lower()
    elif model is m.Grade:
        if user.role not in {'ADMIN', 'INSTRUCTOR'}:
            raise HTTPException(403, 'Only instructors and administrators may submit grades.')
        if existing and data['enrollment_id'] != existing.enrollment_id:
            raise HTTPException(409, 'A grade cannot be transferred to another enrollment.')
        enrollment = grade_permission(db, data['enrollment_id'], user)
        if enrollment.status == 'DROPPED':
            raise HTTPException(409, 'Grades cannot be edited for a dropped enrollment.')
    else:
        require_staff(user)
    if model is m.Student:
        reference(db, m.Program, data['program_id'], 'program_id')
        if data.get('user_id'):
            linked = reference(db, m.User, data['user_id'], 'user_id')
            if linked.role != 'STUDENT':
                raise HTTPException(422, 'The linked user must have the STUDENT role.')
        if data.get('birth_date'):
            from datetime import date
            if data['birth_date'] > date.today():
                raise HTTPException(422, 'Birth date cannot be in the future.')
    if model is m.Course:
        reference(db, m.Program, data['program_id'], 'program_id')
    if model is m.CourseOffering:
        reference(db, m.Course, data['course_id'], 'course_id')
        reference(db, m.AcademicTerm, data['academic_term_id'], 'academic_term_id')
        instructor = reference(db, m.User, data['instructor_id'], 'instructor_id')
        if instructor.role != 'INSTRUCTOR' or instructor.status != 'ACTIVE':
            raise HTTPException(422, 'Instructor must be an active INSTRUCTOR account.')
        if existing:
            count = db.scalar(select(func.count()).select_from(m.Enrollment).where(m.Enrollment.course_offering_id == existing.id, m.Enrollment.status == 'ENROLLED'))
            if data['capacity'] < count:
                raise HTTPException(409, 'Capacity cannot be lower than current enrollment.')
            has_enrollments = db.scalar(select(m.Enrollment.id).where(m.Enrollment.course_offering_id == existing.id).limit(1))
            if has_enrollments and any(data[field] != getattr(existing, field) for field in ['course_id', 'academic_term_id']):
                raise HTTPException(409, 'An offering with enrollments cannot change course or term.')
    if model is m.Enrollment:
        if existing and any(data[field] != getattr(existing, field) for field in ['student_id', 'course_offering_id']):
            raise HTTPException(409, 'Enrollment student and offering cannot be changed.')
        student = reference(db, m.Student, data['student_id'], 'student_id')
        offering = reference(db, m.CourseOffering, data['course_offering_id'], 'course_offering_id')
        # PostgreSQL deployments serialize seat allocation by locking the parent.
        db.execute(select(m.CourseOffering).where(m.CourseOffering.id == offering.id).with_for_update())
        if data['status'] == 'ENROLLED':
            if student.status != 'ACTIVE' or offering.status != 'ACTIVE':
                raise HTTPException(409, 'Student and offering must be active.')
            q = select(func.count()).select_from(m.Enrollment).where(m.Enrollment.course_offering_id == offering.id, m.Enrollment.status == 'ENROLLED')
            if existing:
                q = q.where(m.Enrollment.id != existing.id)
            if db.scalar(q) >= offering.capacity:
                raise HTTPException(409, 'Course offering is at capacity.')


def save(db, resource, payload, user, ident=None):
    model, schema, _, _ = RESOURCES[resource]
    existing = get_authorized(db, model, ident, user) if ident else None
    submitted = payload.model_dump(exclude_unset=bool(existing))
    if existing:
        merged = {field: getattr(existing, field) for field in schema.model_fields if field != 'password'}
        # Validate other fields without requiring a password on PATCH.
        if model is m.User:
            merged['password'] = 'placeholder-not-persisted'
        merged.update(submitted)
        try:
            data = schema.model_validate(merged).model_dump()
        except ValidationError as exc:
            from fastapi.exceptions import RequestValidationError
            raise RequestValidationError(exc.errors()) from exc
        if model is m.User and 'password' not in submitted:
            data.pop('password')
    else:
        data = submitted
    validate_business(db, model, data, user, existing)
    if model is m.User:
        if existing and any(field in submitted for field in ['password', 'role', 'status']):
            db.execute(delete(m.Token).where(m.Token.user_id == existing.id))
        if 'password' in data:
            data['password_hash'] = password_hash.hash(data.pop('password'))
    obj = existing or model()
    for field, value in data.items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return success(present(db, [obj])[0], 'Resource updated.' if existing else 'Resource created.')


def remove(db, resource, ident, user):
    model = RESOURCES[resource][0]
    obj = get_authorized(db, model, ident, user)
    if model is m.User:
        if obj.id == user.id:
            raise HTTPException(409, 'You cannot delete your own account.')
    else:
        require_staff(user)
    db.delete(obj)
    db.commit()
