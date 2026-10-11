"""Export OpenAPI and a runnable Postman collection, without accessing the DB."""
import json
from pathlib import Path
from .main import app
from .services import RESOURCES

EXAMPLES = {
    'users': {'name': 'Demo User', 'email': 'new@example.com', 'password': 'Example-only-password-123', 'role': 'STUDENT'},
    'programs': {'code': 'BSCE', 'name': 'Computer Engineering', 'description': 'Engineering program'},
    'students': {'student_number': '2026-00101', 'first_name': 'Maria', 'last_name': 'Reyes', 'email': 'maria@example.com', 'program_id': 1, 'year_level': 1},
    'courses': {'program_id': 1, 'course_code': 'CS101', 'course_title': 'Introduction to Programming', 'units': 3},
    'academic-terms': {'academic_year': '2027-2028', 'semester': 'FIRST', 'start_date': '2027-08-01', 'end_date': '2027-12-20'},
    'course-offerings': {'course_id': 1, 'academic_term_id': 1, 'instructor_id': 3, 'section': 'B', 'schedule': 'Tuesday 09:00-10:30', 'room': 'R101', 'capacity': 30},
    'enrollments': {'student_id': 1, 'course_offering_id': 2, 'enrollment_date': '2026-08-01', 'status': 'ENROLLED'},
    'grades': {'enrollment_id': 1, 'midterm_grade': 85, 'final_grade': 90, 'remarks': 'Passed'},
}


def enrich_openapi(schema):
    for resource, (_, model, _, _) in RESOURCES.items():
        sample = EXAMPLES[resource]
        for method in ['post', 'patch']:
            path = f'/api/v1/{resource}' + ('/{ident}' if method == 'patch' else '')
            schema['paths'][path][method]['requestBody']['content']['application/json']['example'] = sample
        read = {**model.model_validate(sample).model_dump(mode='json'), 'id': 101, 'created_at': '2026-09-08T00:00:00', 'updated_at': '2026-09-08T00:00:00'}
        read.pop('password', None)
        for suffix, methods in [('', ['get', 'post']), ('/{ident}', ['get', 'patch'])]:
            for method in methods:
                status = '201' if method == 'post' else '200'
                content = {'success': True, 'message': 'Request successful.', 'data': [read] if method == 'get' and not suffix else read}
                if isinstance(content['data'], list):
                    content['meta'] = {'page': 1, 'per_page': 20, 'total': 1, 'last_page': 1}
                schema['paths'][f'/api/v1/{resource}{suffix}'][method]['responses'][status]['content']['application/json']['example'] = content
    schema['paths']['/api/v1/auth/login']['post']['requestBody']['content']['application/json']['example'] = {'email': 'admin@example.com', 'password': 'Use your local SEED_PASSWORD'}
    return schema


def request(name, method, path, body=None, expected=200, save=None, noauth=False):
    item = {'name': name, 'request': {'method': method, 'header': [], 'url': '{{base_url}}/api/v1' + path, 'description': f'Expected HTTP {expected}. Run against the seeded local database.'}}
    if noauth:
        item['request']['auth'] = {'type': 'noauth'}
    if body is not None:
        item['request']['header'] = [{'key': 'Content-Type', 'value': 'application/json'}]
        raw = json.dumps(body, indent=2)
        # Postman replaces numeric variables before JSON parsing.
        for key in ['program_id', 'course_id', 'term_id', 'offering_id', 'student_id', 'enrollment_id']:
            raw = raw.replace('"{{' + key + '}}"', '{{' + key + '}}')
        item['request']['body'] = {'mode': 'raw', 'raw': raw, 'options': {'raw': {'language': 'json'}}}
    script = [f'pm.test("HTTP {expected}", () => pm.response.to.have.status({expected}));']
    if save:
        variable, field = save
        script.append(f'if (pm.response.code === {expected}) pm.collectionVariables.set("{variable}", pm.response.json().data.{field});')
    item['event'] = [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': script}}]
    return item


def export():
    docs = Path('docs')
    docs.mkdir(exist_ok=True)
    (docs / 'openapi.json').write_text(json.dumps(app.openapi(), indent=2) + '\n')
    login = lambda role: request('Login as ' + role, 'POST', '/auth/login', {'email': role + '@example.com', 'password': '{{password}}'}, save=('token', 'access_token'), noauth=True)
    groups = [{'name': 'Authentication', 'item': [login('admin'), request('Current user', 'GET', '/auth/me'), request('Missing authentication', 'GET', '/students', expected=401, noauth=True), request('Invalid password', 'POST', '/auth/login', {'email': 'admin@example.com', 'password': 'incorrect'}, expected=401, noauth=True)]}]
    bodies = {
        'users': {**EXAMPLES['users'], 'email': 'demo{{run_id}}@example.com', 'password': '{{password}}'},
        'programs': {'code': 'P{{run_id}}', 'name': 'Demonstration program'},
        'students': {**EXAMPLES['students'], 'student_number': 'S{{run_id}}', 'program_id': '{{program_id}}'},
        'courses': {**EXAMPLES['courses'], 'program_id': '{{program_id}}', 'course_code': 'C{{run_id}}'},
        'academic-terms': {**EXAMPLES['academic-terms']},
        'course-offerings': {**EXAMPLES['course-offerings'], 'course_id': '{{course_id}}', 'academic_term_id': '{{term_id}}'},
        'enrollments': {**EXAMPLES['enrollments'], 'student_id': '{{student_id}}', 'course_offering_id': '{{offering_id}}'},
        'grades': {**EXAMPLES['grades'], 'enrollment_id': '{{enrollment_id}}'},
    }
    variables = {'users': 'user_id', 'programs': 'program_id', 'students': 'student_id', 'courses': 'course_id', 'academic-terms': 'term_id', 'course-offerings': 'offering_id', 'enrollments': 'enrollment_id', 'grades': 'grade_id'}
    patches = {'users': {'name': 'Updated User'}, 'programs': {'name': 'Updated program'}, 'students': {'year_level': 2}, 'courses': {'units': 4}, 'academic-terms': {'status': 'ACTIVE'}, 'course-offerings': {'room': 'R202'}, 'enrollments': {'status': 'ENROLLED'}, 'grades': {'final_grade': 92}}
    for resource in RESOURCES:
        key = variables[resource]
        path = '/' + resource
        items = []
        if resource == 'academic-terms':
            # Demonstrate successful creation/deletion, then reuse a seeded term for repeated runs.
            items.append(request('Create demonstration term', 'POST', path, bodies[resource], expected=201, save=('temporary_term_id', 'id')))
            items.append(request('Delete unused demonstration term', 'DELETE', path + '/{{temporary_term_id}}', expected=204))
            items.append(request('Read seeded term', 'GET', path + '/1', save=('term_id', 'id')))
            items.append(request('Reject duplicate term', 'POST', path, {'academic_year': '2026-2027', 'semester': 'FIRST', 'start_date': '2026-08-01', 'end_date': '2026-12-20'}, expected=409))
        else:
            items.append(request('Create ' + resource, 'POST', path, bodies[resource], expected=201, save=(key, 'id')))
        items.extend([request('List ' + resource, 'GET', path + '?page=1&per_page=20'), request('Retrieve ' + resource, 'GET', path + '/{{' + key + '}}'), request('Update ' + resource, 'PATCH', path + '/{{' + key + '}}', patches[resource])])
        if resource == 'users':
            items.append(request('Delete unused user', 'DELETE', path + '/{{user_id}}', expected=204))
        elif resource != 'grades':
            items.append(request('Protect referenced record from deletion', 'DELETE', path + '/1', expected=409))
        if resource in {'students', 'enrollments'}:
            items.append(request('Reject duplicate ' + resource, 'POST', path, bodies[resource], expected=409))
        if resource == 'students':
            items += [request('Search filter sort and paginate', 'GET', path + '?search=Student&program_id=1&status=ACTIVE&sort=-last_name&page=1&per_page=10'), request('Reject invalid email', 'POST', path, {**bodies[resource], 'email': 'invalid'}, expected=422), request('Not found', 'GET', path + '/99999999', expected=404)]
        groups.append({'name': resource, 'item': items})
    groups.append({'name': 'Academic Records', 'item': [request('Student enrollments', 'GET', '/students/{{student_id}}/enrollments'), request('Student grades', 'GET', '/students/{{student_id}}/grades'), request('Student academic record', 'GET', '/students/{{student_id}}/academic-record'), request('Offering roster', 'GET', '/course-offerings/{{offering_id}}/students')]})
    role_checks = [
        login('instructor'),
        request('Assigned offerings only', 'GET', '/course-offerings'),
        request('Authorized grade update', 'PATCH', '/grades/{{grade_id}}', {'final_grade': 94}),
        request('Forbidden other offering', 'GET', '/course-offerings/2/students', expected=403),
        login('registrar'),
        request('Registrar cannot read grades', 'GET', '/grades', expected=403),
        request('Registrar cannot submit grades', 'PATCH', '/grades/{{grade_id}}', {'final_grade': 94}, expected=403),
        request('Registrar reads transcript and computed GWA', 'GET', '/students/{{student_id}}/academic-record'),
        login('student'),
        request('Own academic record', 'GET', '/students/1/academic-record'),
        request('Forbidden other record', 'GET', '/students/2/academic-record', expected=403),
        request('Forbidden grade update', 'PATCH', '/grades/1', {'final_grade': 100}, expected=403),
        request('Logout', 'POST', '/auth/logout', expected=204),
        request('Reject revoked token', 'GET', '/auth/me', expected=401),
    ]
    groups.append({'name': 'Role checks and logout', 'item': role_checks})
    collection = {'info': {'name': 'Student Information API Laboratory', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json', 'description': 'Run against a freshly seeded database. Set password to your local SEED_PASSWORD. Run folders in order. Positive and negative requests assert expected status. The assigned instructor encodes each subject grade and administrators retain oversight; the registrar has no grade access but keeps the read-only transcript. Academic records add a computed GWA that is never submitted by a client. Subsequent runs create additional synthetic records.'}, 'auth': {'type': 'bearer', 'bearer': [{'key': 'token', 'value': '{{token}}', 'type': 'string'}]}, 'variable': [{'key': 'base_url', 'value': 'http://127.0.0.1:8000'}, {'key': 'password', 'value': ''}, {'key': 'token', 'value': ''}], 'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': ['if (pm.info.requestName === "Login as admin") pm.collectionVariables.set("run_id", Date.now().toString());']}}], 'item': groups}
    (docs / 'postman_collection.json').write_text(json.dumps(collection, indent=2) + '\n')
    print('Exported docs/openapi.json and docs/postman_collection.json')


if __name__ == '__main__':
    export()
