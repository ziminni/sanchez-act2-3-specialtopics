# Entity Relationship Diagram

Render this Mermaid diagram in a Markdown viewer with Mermaid support. All academic tables and users also have UTC `created_at` and `updated_at` timestamps.

```mermaid
erDiagram
    USERS ||--o{ TOKENS : authenticates
    USERS o|--o| STUDENTS : links_account
    USERS ||--o{ COURSE_OFFERINGS : teaches
    PROGRAMS ||--o{ STUDENTS : contains
    PROGRAMS ||--o{ COURSES : groups
    COURSES ||--o{ COURSE_OFFERINGS : offered_as
    ACADEMIC_TERMS ||--o{ COURSE_OFFERINGS : schedules
    STUDENTS ||--o{ ENROLLMENTS : registers
    COURSE_OFFERINGS ||--o{ ENROLLMENTS : accepts
    ENROLLMENTS ||--o| GRADES : receives

    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        string role
        string status
    }
    TOKENS {
        int id PK
        string digest UK
        int user_id FK
        datetime expires_at
    }
    PROGRAMS {
        int id PK
        string code UK
        string name
        text description
        string status
    }
    STUDENTS {
        int id PK
        int user_id FK,UK "nullable"
        string student_number UK
        string first_name
        string middle_name "nullable"
        string last_name
        string suffix "nullable"
        date birth_date "nullable"
        string email "nullable"
        string contact_number "nullable"
        text address "nullable"
        int program_id FK
        int year_level
        string status
    }
    COURSES {
        int id PK
        int program_id FK
        string course_code UK
        string course_title
        text description
        float units
        string status
    }
    ACADEMIC_TERMS {
        int id PK
        string academic_year
        string semester
        date start_date
        date end_date
        string status
    }
    COURSE_OFFERINGS {
        int id PK
        int course_id FK
        int academic_term_id FK
        int instructor_id FK
        string section
        string schedule
        string room
        int capacity
        string status
    }
    ENROLLMENTS {
        int id PK
        int student_id FK
        int course_offering_id FK
        date enrollment_date
        string status
    }
    GRADES {
        int id PK
        int enrollment_id FK,UK
        float midterm_grade "nullable"
        float final_grade "nullable"
        string remarks "nullable"
    }
```

Composite unique keys: `(academic_year, semester)` on terms, `(course_id, academic_term_id, section)` on offerings, and `(student_id, course_offering_id)` on enrollments.

An account linked to a student must have the STUDENT role; an offering's instructor must be an active INSTRUCTOR. Those cross-table role rules are enforced in the service layer. Most foreign keys use RESTRICT on deletion; tokens use CASCADE when an account is deleted. SQLite foreign-key enforcement is enabled on application connections.
