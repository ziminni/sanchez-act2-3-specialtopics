from datetime import date, datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, create_model, model_validator

Status = Literal['ACTIVE', 'INACTIVE']
Role = Literal['ADMIN', 'REGISTRAR', 'INSTRUCTOR', 'STUDENT']


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class UserCreate(Input):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(min_length=12, max_length=128)
    role: Role
    status: Status = 'ACTIVE'


class ProgramCreate(Input):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: Status = 'ACTIVE'


class StudentCreate(Input):
    user_id: int | None = Field(default=None, gt=0)
    student_number: str = Field(min_length=1, max_length=30)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    suffix: str | None = Field(default=None, max_length=20)
    birth_date: date | None = None
    email: EmailStr | None = None
    contact_number: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=2000)
    program_id: int = Field(gt=0)
    year_level: int = Field(ge=1, le=6)
    status: Status = 'ACTIVE'


class CourseCreate(Input):
    program_id: int = Field(gt=0)
    course_code: str = Field(min_length=1, max_length=30)
    course_title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    units: float = Field(gt=0, le=12)
    status: Status = 'ACTIVE'


class TermCreate(Input):
    academic_year: str = Field(pattern=r'^\d{4}-\d{4}$')
    semester: Literal['FIRST', 'SECOND', 'SUMMER']
    start_date: date
    end_date: date
    status: Status = 'ACTIVE'

    @model_validator(mode='after')
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError('end_date must be on or after start_date')
        start, end = map(int, self.academic_year.split('-'))
        if end != start + 1:
            raise ValueError('academic_year must contain consecutive years')
        return self


class OfferingCreate(Input):
    course_id: int = Field(gt=0)
    academic_term_id: int = Field(gt=0)
    instructor_id: int = Field(gt=0)
    section: str = Field(min_length=1, max_length=30)
    schedule: str | None = Field(default=None, max_length=200)
    room: str | None = Field(default=None, max_length=50)
    capacity: int = Field(gt=0, le=1000)
    status: Status = 'ACTIVE'


class EnrollmentCreate(Input):
    student_id: int = Field(gt=0)
    course_offering_id: int = Field(gt=0)
    enrollment_date: date = Field(default_factory=date.today)
    status: Literal['ENROLLED', 'DROPPED', 'COMPLETED'] = 'ENROLLED'


class GradeCreate(Input):
    enrollment_id: int = Field(gt=0)
    midterm_grade: float | None = Field(default=None, ge=0, le=100)
    final_grade: float | None = Field(default=None, ge=0, le=100)
    remarks: str | None = Field(default=None, max_length=250)


class Login(Input):
    email: EmailStr
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(min_length=1, max_length=128)


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    message: str
    errors: dict[str, list[str]] = Field(default_factory=dict)


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int
    last_page: int


class LoginData(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int


class LoginResponse(BaseModel):
    success: Literal[True] = True
    message: str
    data: LoginData


def update_schema(schema):
    # Optional to omit; merged data is revalidated against the create schema.
    fields = {}
    for name, field in schema.model_fields.items():
        import copy
        info = copy.deepcopy(field)
        info.default = None
        info.default_factory = None
        fields[name] = (field.annotation | None, info)
    return create_model(schema.__name__.replace('Create', 'Update'), __base__=Input, **fields)


# Read-only names of referenced records, so clients can show people and subjects instead of IDs.
_SUBJECT_NAMES = ['course_code', 'course_title', 'term_name']
_ENROLLMENT_NAMES = ['student_name', 'student_number', *_SUBJECT_NAMES, 'section']
REFERENCE_NAMES = {
    'StudentCreate': ['program_name', 'account_email'],
    'CourseCreate': ['program_name'],
    'OfferingCreate': [*_SUBJECT_NAMES, 'instructor_name'],
    'EnrollmentCreate': _ENROLLMENT_NAMES,
    'GradeCreate': _ENROLLMENT_NAMES,
}


def read_schema(schema):
    fields = {name: (field.annotation, field) for name, field in schema.model_fields.items() if name != 'password'}
    fields.update({name: (str | None, None) for name in REFERENCE_NAMES.get(schema.__name__, [])})
    return create_model(schema.__name__.replace('Create', 'Read'), __config__=ConfigDict(from_attributes=True), id=(int, ...), created_at=(datetime, ...), updated_at=(datetime, ...), **fields)


def response_schema(name, data_type, collection=False):
    fields = dict(success=(Literal[True], True), message=(str, ...), data=(data_type, ...))
    if collection:
        fields['meta'] = (PageMeta, ...)
    return create_model(name, **fields)
