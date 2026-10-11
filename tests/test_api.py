from datetime import datetime, timedelta
import pytest
from sqlalchemy import select
from app import models as m
from app.security import digest_token
from conftest import PASSWORD

P = '/api/v1'


def create(client, auth, resource, body, role='admin', expected=201):
    response = client.post(f'{P}/{resource}', json=body, headers=auth(role))
    assert response.status_code == expected, response.text
    return response


def test_health_and_documentation(client):
    assert client.get(P + '/health').json()['data']['status'] == 'ok'
    assert client.get('/api/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    assert schema['paths'][P + '/students']['post']['requestBody']['content']['application/json']['schema']['$ref'].endswith('StudentCreate')
    assert 'password_hash' not in str(schema)
    assert schema['paths'][P + '/students']['get']['security']


def test_auth_login_logout_and_invalid_tokens(client, auth):
    assert client.get(P + '/students').status_code == 401
    assert client.get(P + '/students', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert client.post(P + '/auth/login', json={'email': 'admin@example.com', 'password': 'wrong'}).status_code == 401
    assert client.post(P + '/auth/login', json={'email': 'nobody@example.com', 'password': PASSWORD}).status_code == 401
    headers = auth()
    data = client.get(P + '/auth/me', headers=headers).json()['data']
    assert data['role'] == 'ADMIN'
    assert 'password_hash' not in data
    assert client.post(P + '/auth/logout', headers=headers).status_code == 204
    assert client.get(P + '/auth/me', headers=headers).status_code == 401


def test_expired_token_and_hashed_storage(setup, auth):
    client, factory = setup
    headers = auth()
    with factory() as db:
        token = db.scalar(select(m.Token))
        assert token.digest == digest_token(headers['Authorization'].split()[1])
        assert db.get(m.User, 1).password_hash.startswith('$argon2id$')
        token.expires_at = m.now() - timedelta(seconds=1)
        db.commit()
    assert client.get(P + '/auth/me', headers=headers).status_code == 401


def test_student_crud_validation_and_duplicates(client, auth):
    body = {'student_number': 'NEW-001', 'first_name': 'Carla', 'last_name': 'Reyes', 'program_id': 1, 'year_level': 1, 'email': 'carla@example.com'}
    ident = create(client, auth, 'students', body).json()['data']['id']
    assert client.get(f'{P}/students/{ident}', headers=auth()).json()['data']['first_name'] == 'Carla'
    response = client.patch(f'{P}/students/{ident}', headers=auth(), json={'year_level': 3})
    assert response.status_code == 200 and response.json()['data']['year_level'] == 3
    create(client, auth, 'students', body, expected=409)
    for changes in [{'email': 'bad'}, {'program_id': 999}, {'year_level': 0}, {'status': 'UNKNOWN'}, {'first_name': '   '}, {'birth_date': '2999-01-01'}]:
        create(client, auth, 'students', {**body, 'student_number': 'NEW-002', **changes}, expected=422)
    assert client.patch(f'{P}/students/{ident}', headers=auth(), json={'first_name': None}).status_code == 422
    assert client.patch(f'{P}/students/{ident}', headers=auth(), json={'email': None}).status_code == 200
    assert client.delete(f'{P}/students/{ident}', headers=auth()).status_code == 204
    assert client.get(f'{P}/students/{ident}', headers=auth()).status_code == 404


@pytest.mark.parametrize('role', ['student', 'instructor', 'otherstudent'])
def test_forbidden_student_writes(client, auth, role):
    create(client, auth, 'students', {'student_number': 'HACK', 'first_name': 'X', 'last_name': 'Y', 'program_id': 1, 'year_level': 1}, role=role, expected=403)
    assert client.patch(P + '/students/1', headers=auth(role), json={'year_level': 4}).status_code == 403
    assert client.delete(P + '/students/1', headers=auth(role)).status_code == 403


def test_student_object_level_access_and_scoped_lists(client, auth):
    headers = auth('student')
    for suffix in ['', '/enrollments', '/grades', '/academic-record']:
        assert client.get(P + '/students/1' + suffix, headers=headers).status_code == 200
        assert client.get(P + '/students/2' + suffix, headers=headers).status_code == 403
    assert [r['id'] for r in client.get(P + '/students', headers=headers).json()['data']] == [1]
    assert [r['id'] for r in client.get(P + '/enrollments', headers=headers).json()['data']] == [1]
    assert client.get(P + '/enrollments/2', headers=headers).status_code == 403
    assert client.get(P + '/users', headers=headers).status_code == 403


def test_registrar_permissions(client, auth):
    headers = auth('registrar')
    create(client, auth, 'programs', {'code': 'BSCS', 'name': 'Computer Science'}, role='registrar')
    assert client.get(P + '/users', headers=headers).status_code == 403
    # Grading belongs to the assigned instructor, so the registrar has no grade access.
    assert client.get(P + '/grades', headers=headers).status_code == 403
    assert client.get(P + '/grades/1', headers=headers).status_code == 403
    assert client.get(P + '/students/1/grades', headers=headers).status_code == 403
    create(client, auth, 'grades', {'enrollment_id': 1, 'final_grade': 80}, role='registrar', expected=403)
    assert client.patch(P + '/grades/1', headers=headers, json={'final_grade': 80}).status_code == 403
    # The read-only transcript, including the computed GWA, stays available to the registrar.
    transcript = client.get(P + '/students/1/academic-record', headers=headers)
    assert transcript.status_code == 200 and transcript.json()['data']['gwa'] == 90.0


def test_enrollment_references_duplicate_capacity_and_immutable_links(client, auth):
    create(client, auth, 'enrollments', {'student_id': 1, 'course_offering_id': 1}, expected=409)
    create(client, auth, 'enrollments', {'student_id': 999, 'course_offering_id': 1}, expected=422)
    create(client, auth, 'enrollments', {'student_id': 1, 'course_offering_id': 999}, expected=422)
    create(client, auth, 'enrollments', {'student_id': 2, 'course_offering_id': 1})
    student = create(client, auth, 'students', {'student_number': 'THIRD', 'first_name': 'C', 'last_name': 'D', 'program_id': 1, 'year_level': 1}).json()['data']
    create(client, auth, 'enrollments', {'student_id': student['id'], 'course_offering_id': 1}, expected=409)
    assert client.patch(P + '/enrollments/1', headers=auth(), json={'student_id': 2}).status_code == 409
    assert client.patch(P + '/course-offerings/1', headers=auth(), json={'capacity': 1}).status_code == 409
    assert client.patch(P + '/enrollments/1', headers=auth(), json={'status': 'DROPPED'}).status_code == 200
    create(client, auth, 'enrollments', {'student_id': student['id'], 'course_offering_id': 1})
    assert client.patch(P + '/enrollments/1', headers=auth(), json={'status': 'ENROLLED'}).status_code == 409


def test_instructor_grades_and_offering_scope(client, auth):
    headers = auth('instructor')
    assert client.patch(P + '/grades/1', headers=headers, json={'final_grade': 95}).status_code == 200
    assert client.patch(P + '/grades/1', headers=auth('otherinstructor'), json={'final_grade': 60}).status_code == 403
    assert client.patch(P + '/grades/1', headers=auth('student'), json={'final_grade': 100}).status_code == 403
    create(client, auth, 'grades', {'enrollment_id': 2, 'final_grade': 85}, role='instructor', expected=403)
    create(client, auth, 'grades', {'enrollment_id': 2, 'final_grade': 85}, role='otherinstructor')
    create(client, auth, 'grades', {'enrollment_id': 999, 'final_grade': 85}, expected=422)
    create(client, auth, 'grades', {'enrollment_id': 1, 'final_grade': 101}, expected=422)
    create(client, auth, 'grades', {'enrollment_id': 1, 'final_grade': 85}, expected=409)
    assert client.patch(P + '/grades/1', headers=auth(), json={'enrollment_id': 2}).status_code == 409
    assert [r['id'] for r in client.get(P + '/course-offerings', headers=headers).json()['data']] == [1]
    assert client.get(P + '/course-offerings/2/students', headers=headers).status_code == 403
    roster = client.get(P + '/course-offerings/1/students', headers=headers).json()['data'][0]
    assert roster['student_number'] == '2026-00001' and 'email' not in roster


def test_instructor_students_and_their_records(client, auth):
    headers = auth('instructor')
    # Student 1 is in the instructor's offering; student 2 is in another instructor's.
    assert client.get(P + '/students/1/academic-record', headers=headers).status_code == 200
    assert client.get(P + '/students/2/academic-record', headers=headers).status_code == 403
    assert client.get(P + '/students/999/academic-record', headers=headers).status_code == 404
    assert client.get(P + '/students/1', headers=headers).status_code == 403
    body = client.get(P + '/my-students', headers=headers).json()
    assert [row['student_number'] for row in body['data']] == ['2026-00001'] and body['meta']['total'] == 1
    row = body['data'][0]
    assert (row['program_name'], row['subjects'][0]['course_code'], row['subjects'][0]['section']) == ('Information Technology', 'IT101', 'A1')
    assert 'email' not in row and 'contact_number' not in row
    assert client.get(P + '/my-students?search=santos', headers=headers).json()['meta']['total'] == 0
    for role in ['admin', 'registrar', 'student']:
        assert client.get(P + '/my-students', headers=auth(role)).status_code == 403


def test_search_filter_sort_pagination(client, auth):
    headers = auth()
    assert client.get(P + '/students?search=dela', headers=headers).json()['meta']['total'] == 1
    assert client.get(P + '/students?program_id=1&year_level=2&status=ACTIVE', headers=headers).json()['data'][0]['first_name'] == 'Ben'
    result = client.get(P + '/students?sort=-last_name&page=2&per_page=1', headers=headers).json()
    assert result['data'][0]['last_name'] == 'Dela Cruz'
    assert result['meta'] == {'page': 2, 'per_page': 1, 'total': 2, 'last_page': 2}
    for query in ['per_page=101', 'page=0', 'sort=password_hash', 'sort=id;DROP TABLE students', 'unknown=1', 'course_id=1']:
        assert client.get(P + '/students?' + query, headers=headers).status_code == 422
    assert client.get(P + '/students?search=%25', headers=headers).json()['meta']['total'] == 0
    assert client.get(P + '/students?search=%27%20OR%201=1--', headers=headers).json()['meta']['total'] == 0


def test_academic_record(client, auth):
    response = client.get(P + '/students/1/academic-record', headers=auth('student'))
    assert response.status_code == 200
    body = response.json()['data']
    term = body['terms'][0]
    assert term['academic_year'] == '2026-2027'
    assert term['courses'][0]['course_code'] == 'IT101'
    assert term['courses'][0]['final_grade'] == 90
    assert response.json()['meta']['total'] == 1
    assert (body['gwa'], body['units']) == (90.0, 3)
    assert (term['gwa'], term['units']) == (90.0, 3)


def test_responses_name_referenced_records(client, auth):
    headers = auth()
    student = client.get(P + '/students/1', headers=headers).json()['data']
    assert (student['program_name'], student['account_email']) == ('Information Technology', 'student@example.com')
    offering = client.get(P + '/course-offerings/1', headers=headers).json()['data']
    assert (offering['course_code'], offering['course_title'], offering['term_name'], offering['instructor_name']) == ('IT101', 'Programming', '2026-2027 First semester', 'INSTRUCTOR')
    enrollment = client.get(P + '/enrollments?student_id=1', headers=headers).json()['data'][0]
    assert (enrollment['student_name'], enrollment['student_number'], enrollment['course_code'], enrollment['section']) == ('Ana Dela Cruz', '2026-00001', 'IT101', 'A1')
    grade = client.get(P + '/students/1/grades', headers=auth('student')).json()['data'][0]
    assert (grade['student_name'], grade['course_title'], grade['term_name']) == ('Ana Dela Cruz', 'Programming', '2026-2027 First semester')
    record = client.get(P + '/students/1/academic-record', headers=headers).json()['data']
    assert (record['student_name'], record['student_number']) == ('Ana Dela Cruz', '2026-00001')
    # Names are derived for display only; clients cannot submit them.
    assert client.patch(P + '/enrollments/1', headers=headers, json={'student_name': 'Someone'}).status_code == 422


def test_gwa_is_computed_per_subject_and_never_submitted(client, auth):
    # Only per-subject grades are accepted; an overall average in the body is rejected.
    create(client, auth, 'grades', {'enrollment_id': 2, 'gwa': 90}, expected=422)
    course = create(client, auth, 'courses', {'program_id': 1, 'course_code': 'PE101', 'course_title': 'Physical Education', 'units': 1}).json()['data']
    term = create(client, auth, 'academic-terms', {'academic_year': '2027-2028', 'semester': 'FIRST', 'start_date': '2027-08-01', 'end_date': '2027-12-01'}).json()['data']
    offering = create(client, auth, 'course-offerings', {'course_id': course['id'], 'academic_term_id': term['id'], 'instructor_id': 3, 'section': 'PE-A', 'capacity': 30}).json()['data']
    enrollment = create(client, auth, 'enrollments', {'student_id': 1, 'course_offering_id': offering['id']}).json()['data']
    create(client, auth, 'grades', {'enrollment_id': enrollment['id'], 'final_grade': 100}, role='instructor')
    # (90 x 3 units + 100 x 1 unit) / 4 units = 92.5
    record = client.get(P + '/students/1/academic-record', headers=auth('student')).json()['data']
    assert (record['gwa'], record['units']) == (92.5, 4)
    terms = {item['academic_term_id']: item for item in record['terms']}
    assert terms[1]['gwa'] == 90.0 and terms[term['id']]['gwa'] == 100.0
    # Dropping the subject removes it from the computed average.
    assert client.patch(f'{P}/enrollments/{enrollment["id"]}', headers=auth(), json={'status': 'DROPPED'}).status_code == 200
    assert client.get(P + '/students/1/academic-record', headers=auth('student')).json()['data']['gwa'] == 90.0


def test_terms_courses_offerings_and_integrity(client, auth):
    course = create(client, auth, 'courses', {'program_id': 1, 'course_code': 'IT102', 'course_title': 'Databases', 'units': 3}).json()['data']
    subjects = client.get(P + '/courses?program_id=1', headers=auth()).json()['data']
    assert {subject['course_code'] for subject in subjects} >= {'IT101', 'IT102'}
    create(client, auth, 'courses', {'program_id': 1, 'course_code': 'IT102', 'course_title': 'Duplicate', 'units': 3}, expected=409)
    term = create(client, auth, 'academic-terms', {'academic_year': '2026-2027', 'semester': 'SECOND', 'start_date': '2027-01-01', 'end_date': '2027-05-01'}).json()['data']
    assert client.patch(f'{P}/academic-terms/{term["id"]}', headers=auth(), json={'end_date': '2020-01-01'}).status_code == 422
    create(client, auth, 'academic-terms', {'academic_year': '2026-2029', 'semester': 'SECOND', 'start_date': '2027-01-01', 'end_date': '2027-05-01'}, expected=422)
    body = {'course_id': course['id'], 'academic_term_id': term['id'], 'instructor_id': 3, 'section': 'NEW', 'capacity': 20}
    offering = create(client, auth, 'course-offerings', body).json()['data']
    create(client, auth, 'course-offerings', {**body, 'section': 'BAD', 'instructor_id': 5}, expected=422)
    assert client.delete(P + '/programs/1', headers=auth()).status_code == 409
    assert client.delete(P + '/enrollments/1', headers=auth()).status_code == 409
    assert client.delete(f'{P}/course-offerings/{offering["id"]}', headers=auth()).status_code == 204
    assert client.delete(f'{P}/courses/{course["id"]}', headers=auth()).status_code == 204
    assert client.delete(f'{P}/academic-terms/{term["id"]}', headers=auth()).status_code == 204


def test_user_management_and_revocation(client, auth):
    body = {'name': 'New User', 'email': 'new@example.com', 'password': PASSWORD, 'role': 'STUDENT'}
    user = create(client, auth, 'users', body).json()['data']
    assert 'password_hash' not in user and 'password' not in user
    token = client.post(P + '/auth/login', json={'email': body['email'], 'password': PASSWORD}).json()['data']['access_token']
    assert client.patch(f'{P}/users/{user["id"]}', headers=auth(), json={'status': 'INACTIVE'}).status_code == 200
    assert client.get(P + '/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401
    assert client.post(P + '/auth/login', json={'email': body['email'], 'password': PASSWORD}).status_code == 401
    assert client.patch(P + '/users/1', headers=auth(), json={'role': 'STUDENT'}).status_code == 409
    assert client.patch(P + '/users/3', headers=auth(), json={'role': 'STUDENT'}).status_code == 409
    assert client.delete(P + '/users/1', headers=auth()).status_code == 409
    assert client.delete(f'{P}/users/{user["id"]}', headers=auth()).status_code == 204


def test_error_responses_are_safe(client, auth):
    r = client.get(P + '/students/999', headers=auth())
    assert r.status_code == 404 and r.json()['success'] is False
    r = client.post(P + '/students', headers=auth(), json={'password': 'must-not-echo-this'})
    assert r.status_code == 422 and 'must-not-echo-this' not in r.text
    assert 'errors' in r.json()
    r = client.get('/missing')
    assert r.status_code == 404 and r.json()['success'] is False


def test_frontend_instructor_directory_is_minimal_and_restricted(client, auth):
    response = client.get(P + '/instructors?per_page=1', headers=auth('registrar'))
    assert response.status_code == 200
    assert response.json()['meta']['total'] == 2
    assert set(response.json()['data'][0]) == {'id', 'name', 'status'}
    assert client.get(P + '/instructors', headers=auth('student')).status_code == 403
    assert client.get(P + '/instructors', headers=auth('instructor')).status_code == 403
    assert client.get(P + '/instructors').status_code == 401


def test_frontend_cors_allows_only_configured_origins(client):
    allowed = client.options(P + '/students', headers={'Origin': 'http://127.0.0.1:5173', 'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'Authorization'})
    assert allowed.status_code == 200
    assert allowed.headers['access-control-allow-origin'] == 'http://127.0.0.1:5173'
    denied = client.options(P + '/students', headers={'Origin': 'https://untrusted.example', 'Access-Control-Request-Method': 'GET'})
    assert denied.status_code == 400
    assert 'access-control-allow-origin' not in denied.headers
