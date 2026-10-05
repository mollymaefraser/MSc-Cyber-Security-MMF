# Secure E-Learning Platform: Design, Implementation and Testing Report

## 1. Introduction

This report describes the design, implementation and testing of a secure e-learning platform built with object-oriented design and Test-Driven Development (TDD). Students can register, browse published courses and enrol. Instructors create and publish courses and view their rosters. Administrators manage roles.

The system is written in Python 3 using only the standard library. It has three modules (User Management, Course Management and Enrolment Management) behind a presentation layer, and it has 137 automated tests with 100% line and branch coverage.

Section 2 covers Task 1 (architecture), Section 3 covers Task 2 (implementation and TDD), and Section 4 covers Task 3 (testing, refactoring and results). Section 5 is an honest list of limitations. The figures are text, so the report can be pasted anywhere. The test figures are copied from the real terminal output of each run (with file paths shortened).

---

## 2. Task 1: Software Architecture

### 2.1 Choice of architecture style

I chose a layered architecture, built as a modular monolith. The code is divided into a presentation layer, a business logic layer and a data access layer, and the business logic is further divided into three modules that each own their service and repository.

```
   Client: browser or mobile app (out of scope)
   sends a session token over HTTPS
                                   |
                                   v
+--------------------------------------------------------------------+
| PRESENTATION LAYER                                                 |
| ApiController: authenticates the token, checks input shape,        |
| calls one service method, maps outcomes to status codes.           |
| No business rules, no SQL, never leaks internals.                  |
+--------------------------------------------------------------------+
                                   |
                                   v
+--------------------------------------------------------------------+
| BUSINESS LOGIC LAYER                                               |
| +----------------+  +----------------+  +----------------+         |
| | USER           |  | COURSE         |  | ENROLMENT      |         |
| | MANAGEMENT     |  | MANAGEMENT     |  | MANAGEMENT     |         |
| | UserService    |  | CourseService  |  | EnrolmentSvc   |         |
| | PasswordPolicy |  | validation     |  | student only   |         |
| | PasswordHasher |  | ownership      |  | capacity       |         |
| | SessionManager |  | draft rules    |  | no duplicates  |         |
| | LoginThrottle  |  | safe search    |  | rosters        |         |
| +----------------+  +----------------+  +----------------+         |
+--------------------------------------------------------------------+
                                   |
                                   v
+--------------------------------------------------------------------+
| DATA ACCESS LAYER                                                  |
| +----------------+  +----------------+  +----------------+         |
| | UserRepository |  | CourseRepo     |  | EnrolmentRepo  |         |
| | parameterised  |  | escaped LIKE   |  | atomic check   |         |
| | queries        |  | search         |  | and insert     |         |
| +----------------+  +----------------+  +----------------+         |
+--------------------------------------------------------------------+
                                   |
                                   v
+--------------------------------------------------------------------+
| STORAGE                                                            |
| SQLite database (swappable for PostgreSQL)                         |
| foreign keys, CHECK constraints, UNIQUE email,                     |
| composite primary key on enrolments                                |
+--------------------------------------------------------------------+

+--------------------------------------------------------------------+
| CROSS CUTTING SECURITY (applies to every layer)                    |
| Authentication: salted scrypt, hashed session tokens, expiry       |
| Brute force defence: per client lockout                            |
| Authorisation: require_role, ownership checks, deny by default     |
| Input validation: allow lists and size limits                      |
| Parameterised SQL only, database constraints as a backstop         |
| Audit log of events (never secrets), generic error messages        |
+--------------------------------------------------------------------+
```

Figure 1: Layered modular monolith. Dependencies point downwards only.

The justification, judged against the three requirements in the brief:

Scalability. A modular monolith scales vertically and, once session storage is externalised, horizontally by running several identical copies behind a load balancer. It does not scale each module independently, which is what microservices offer. For an e-learning platform at this stage that benefit does not justify the cost, because the three modules are not yet under different loads. Because each module has its own service and repository and talks to the others only through service calls, any of them can be extracted into a separate service later without rewriting the others.

Maintainability. Layering separates concerns: the controller contains no business rules, services contain no SQL, and repositories contain no business rules. A change such as swapping SQLite for PostgreSQL touches only the data access layer. A change to the password rules touches only one class. A single codebase with one test suite is far easier for one developer to understand and test than several services.

Security. A monolith has a smaller attack surface than microservices. There is no network traffic between services to encrypt and authenticate, no service-to-service credentials to manage and no distributed authorisation to get wrong. Every request passes through one authentication and authorisation path, and it is easy to see where each control sits.

Microservices would be the better choice if modules needed independent deployment, different technology stacks, or very different scaling profiles. A single unstructured monolith was rejected because it would make the security controls and the tests harder to reason about.

### 2.2 Key modules

User Management. Registration, authentication, sessions, password changes and role management. Classes: UserService, PasswordPolicy with its rules, PasswordHasher, SessionManager, LoginThrottle and SqliteUserRepository.

Course Management. Creating, publishing, viewing, listing and searching courses. Classes: CourseService and SqliteCourseRepository. Rules include that only instructors and administrators can create courses, only the owner or an administrator can publish a course, and drafts are invisible to everyone else.

Enrolment Management. Enrolling and unenrolling students, listing a student's courses and viewing a course roster. Classes: EnrolmentService and SqliteEnrolmentRepository. Rules include that only students can enrol, only in published courses, never twice, and never beyond the course capacity.

Shared components. ApiController (presentation layer), Database (connection and transactions), AuditLog, require_role (authorisation helper) and an exception hierarchy rooted at ELearnError.

A natural next module would be Content Management (lessons, quizzes, submissions), which would follow the same pattern of service plus repository.

### 2.3 Object-oriented design

Encapsulation: services hide their repositories, the session store and the throttle, and expose only a small set of public methods. Course and User are immutable dataclasses, so their state cannot be changed after creation.

Abstraction and polymorphism: PasswordRule is an interface implemented by LengthRule, CharacterMixRule and CommonPasswordRule. A PasswordPolicy runs any list of rules, so a new rule can be added without changing existing code (the Strategy pattern, and the Open/Closed Principle).

Single responsibility: each class has one job. Hashing, session handling, throttling, validation and persistence are all separate.

Dependency injection: every service receives its collaborators (repositories, clock, audit log, hasher, policy) through its constructor. This is what made it possible to test with a fake clock and a low-cost hasher.

The Facade pattern is used by ApiController, which gives a client one simple entry point over the three services.

### 2.4 Security considerations

The table lists each threat, the control that addresses it, and the evidence that the control works.

| Threat | Control | Test evidence |
|---|---|---|
| Stolen database leaks passwords | Salted scrypt hashes with a per-password random salt. The cost parameter is stored in the hash so it can be raised later | Tests for no plain text storage, different hashes for equal passwords, round trip and malformed hashes |
| Weak passwords | PasswordPolicy: length 10 to 128, letter and digit, common password blocklist. Maximum length also limits hashing abuse | PasswordPolicy tests, weak password tests |
| Brute force login | Lockout after 5 failures per client and account for 5 minutes, checked before any hashing | Throttle tests, controller returns 429 |
| Username enumeration | Same generic message for unknown user and wrong password. A dummy hash is verified for unknown users so response time is similar | Test comparing both error messages |
| Session theft or reuse | Random 256 bit tokens, only SHA-256 digests stored server side, 30 minute expiry, logout, and all sessions revoked on password change | Session and password change tests |
| SQL injection | Parameterised queries everywhere, strict input validation, escaped LIKE wildcards in search | Injection tests for email, search and course id, and tables confirmed intact afterwards |
| Privilege escalation | Role based access control with deny by default through require_role, plus ownership checks. Only an administrator can change roles. Self-registration always creates a student | Role tests, authorisation tests in every module |
| Information disclosure | Drafts hidden from students and other instructors, generic error messages, 500 responses never include exception text | Visibility tests, controller 500 test |
| Over-enrolment under concurrency | Capacity check and insert happen in one locked transaction | Test with ten threads racing for the last seat |
| Tampering and repudiation | Audit log of registrations, failed logins, lockouts, role changes, course and enrolment events. It records identifiers and never secrets | Audit tests, including that no password appears |
| Bad data bypassing the application | Database constraints (CHECK, UNIQUE, foreign keys) as a second line of defence | Tests that insert invalid rows directly |
| Data in transit | Not implemented in this code. A real deployment must terminate TLS (HTTPS) at a reverse proxy | See Section 5 |

Encryption at rest and in transit is therefore addressed as follows: passwords are protected by hashing, tokens by hashing, and transport encryption is a deployment requirement that sits outside the application code.

---

## 3. Task 2: Implementation and TDD

### 3.1 Approach

For each feature I wrote the tests first, ran them to confirm they failed (red), wrote the simplest code that made them pass (green), and then refactored with the tests as a safety net. The output blocks below are copied from the actual runs, with file paths shortened.

The User Management module was built entirely this way, in three cycles plus a refactoring step. Course Management, Enrolment Management and the controller were then built test first as well.

Source files: elearn/users.py, elearn/courses.py, elearn/enrolment.py, elearn/controller.py, elearn/security.py, elearn/audit.py, elearn/database.py and elearn/errors.py.

### 3.2 Cycle 1: Registration

Tests written first covered successful registration, email normalisation, duplicate emails, invalid emails, weak and over-long passwords, hashing, salting and SQL injection in the email field. With no users module in existence, the run failed with a ModuleNotFoundError, which is the expected red state.

```
$ python3 -m unittest tests.test_users -v
test_users (unittest.loader._FailedTest.test_users) ... ERROR

======================================================================
ERROR: test_users (unittest.loader._FailedTest.test_users)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_users
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_users.py", line 5, in <module>
    from elearn.users import PasswordHasher, Role, SqliteUserRepository, UserService
ModuleNotFoundError: No module named 'elearn.users'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Figure 2: Registration tests written first fail because the module does not exist.

I then wrote the simplest implementation. The password checks were deliberately written inline in the register method, which is a smell I knew I would refactor later. All 9 tests passed.

```
$ python3 -m unittest tests.test_users -v
test_duplicate_email_is_rejected_case_insensitively (RegistrationTests) ... ok
test_email_is_normalised_to_lower_case_and_trimmed (RegistrationTests) ... ok
test_invalid_emails_are_rejected (RegistrationTests) ... ok
test_password_is_never_stored_in_plain_text (RegistrationTests) ... ok
test_register_returns_a_student_with_an_id (RegistrationTests) ... ok
test_same_password_produces_different_hashes_because_of_salting (RegistrationTests) ... ok
test_sql_injection_in_email_is_rejected_and_tables_survive (RegistrationTests) ... ok
test_very_long_password_is_rejected_to_prevent_hashing_abuse (RegistrationTests) ... ok
test_weak_passwords_are_rejected (RegistrationTests) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.025s

OK
```

Figure 3: Registration implemented, 9 tests pass.

### 3.3 Cycle 2: Authentication and sessions

I added 11 tests for login, wrong password, unknown user, non-string credentials, token uniqueness, expiry (using a fake clock so no test waits), logout, forged tokens and token storage. They failed because the session constants and methods did not exist.

```
$ python3 -m unittest tests.test_users
E
======================================================================
ERROR: test_users (unittest.loader._FailedTest.test_users)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_users
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_users.py", line 5, in <module>
    from elearn.users import (SESSION_TTL_SECONDS, PasswordHasher, Role, SqliteUserRepository,
ImportError: cannot import name 'SESSION_TTL_SECONDS' from 'elearn.users' (elearn/users.py)


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Figure 4: New authentication tests fail before the implementation.

After implementing SessionManager and authenticate, 20 tests passed.

```
$ python3 -m unittest tests.test_users -v
test_forged_and_malformed_tokens_are_rejected (AuthenticationTests) ... ok
test_login_is_case_insensitive_on_email (AuthenticationTests) ... ok
test_login_returns_a_token_that_resolves_to_the_user (AuthenticationTests) ... ok
test_logout_invalidates_the_token (AuthenticationTests) ... ok
test_non_string_credentials_are_rejected_cleanly (AuthenticationTests) ... ok
test_session_expires_after_the_time_to_live (AuthenticationTests) ... ok
test_session_is_still_valid_just_before_expiry (AuthenticationTests) ... ok
test_session_tokens_are_not_stored_in_plain_text (AuthenticationTests) ... ok
test_tokens_are_unique_and_unguessably_long (AuthenticationTests) ... ok
test_unknown_user_gets_the_same_error_as_a_wrong_password (AuthenticationTests) ... ok
test_wrong_password_is_rejected (AuthenticationTests) ... ok
test_duplicate_email_is_rejected_case_insensitively (RegistrationTests) ... ok
test_email_is_normalised_to_lower_case_and_trimmed (RegistrationTests) ... ok
test_invalid_emails_are_rejected (RegistrationTests) ... ok
test_password_is_never_stored_in_plain_text (RegistrationTests) ... ok
test_register_returns_a_student_with_an_id (RegistrationTests) ... ok
test_same_password_produces_different_hashes_because_of_salting (RegistrationTests) ... ok
test_sql_injection_in_email_is_rejected_and_tables_survive (RegistrationTests) ... ok
test_very_long_password_is_rejected_to_prevent_hashing_abuse (RegistrationTests) ... ok
test_weak_passwords_are_rejected (RegistrationTests) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.122s

OK
```

Figure 5: Authentication and sessions implemented, 20 tests pass.

### 3.4 Cycle 3: Lockout, password change, roles and audit

Tests for lockout, lockout expiry, per-client scoping, counter reset, password change, session revocation, administrator-only role changes and the audit log were added first.

```
$ python3 -m unittest tests.test_users
E
======================================================================
ERROR: test_users (unittest.loader._FailedTest.test_users)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_users
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_users.py", line 4, in <module>
    from elearn.audit import AuditLog
ModuleNotFoundError: No module named 'elearn.audit'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Figure 6: Cycle 3 tests fail because the audit module and new features do not exist.

After implementation, 35 tests passed.

```
$ python3 -m unittest tests.test_users -v
test_audit_log_never_contains_passwords (AuditTests) ... ok
test_registration_and_failed_login_are_recorded (AuditTests) ... ok
test_forged_and_malformed_tokens_are_rejected (AuthenticationTests) ... ok
test_login_is_case_insensitive_on_email (AuthenticationTests) ... ok
test_login_returns_a_token_that_resolves_to_the_user (AuthenticationTests) ... ok
test_logout_invalidates_the_token (AuthenticationTests) ... ok
test_non_string_credentials_are_rejected_cleanly (AuthenticationTests) ... ok
test_session_expires_after_the_time_to_live (AuthenticationTests) ... ok
test_session_is_still_valid_just_before_expiry (AuthenticationTests) ... ok
test_session_tokens_are_not_stored_in_plain_text (AuthenticationTests) ... ok
test_tokens_are_unique_and_unguessably_long (AuthenticationTests) ... ok
test_unknown_user_gets_the_same_error_as_a_wrong_password (AuthenticationTests) ... ok
test_wrong_password_is_rejected (AuthenticationTests) ... ok
test_changing_password_revokes_existing_sessions (ChangePasswordTests) ... ok
test_new_password_works_and_old_password_stops_working (ChangePasswordTests) ... ok
test_weak_new_password_is_rejected_and_old_one_still_works (ChangePasswordTests) ... ok
test_wrong_current_password_is_rejected (ChangePasswordTests) ... ok
test_client_is_locked_out_after_five_failures_even_with_the_right_password (LoginThrottleTests) ... ok
test_lockout_expires_after_the_window (LoginThrottleTests) ... ok
test_lockout_is_scoped_to_the_client_not_global (LoginThrottleTests) ... ok
test_successful_login_resets_the_failure_count (LoginThrottleTests) ... ok
test_duplicate_email_is_rejected_case_insensitively (RegistrationTests) ... ok
test_email_is_normalised_to_lower_case_and_trimmed (RegistrationTests) ... ok
test_invalid_emails_are_rejected (RegistrationTests) ... ok
test_password_is_never_stored_in_plain_text (RegistrationTests) ... ok
test_register_returns_a_student_with_an_id (RegistrationTests) ... ok
test_same_password_produces_different_hashes_because_of_salting (RegistrationTests) ... ok
test_sql_injection_in_email_is_rejected_and_tables_survive (RegistrationTests) ... ok
test_very_long_password_is_rejected_to_prevent_hashing_abuse (RegistrationTests) ... ok
test_weak_passwords_are_rejected (RegistrationTests) ... ok
test_a_student_cannot_promote_themselves (RoleManagementTests) ... ok
test_admin_can_promote_a_student_to_instructor (RoleManagementTests) ... ok
test_bootstrap_admin_creates_an_admin (RoleManagementTests) ... ok
test_invalid_role_value_is_rejected (RoleManagementTests) ... ok
test_promoting_an_unknown_user_raises_not_found (RoleManagementTests) ... ok

----------------------------------------------------------------------
Ran 35 tests in 0.322s

OK
```

Figure 7: Cycle 3 complete, 35 tests pass.

### 3.5 Cycle 5: Courses and enrolment

Cycle 4 was the password policy refactor, described in Section 4.2. For cycle 5, I wrote the tests for the Course and Enrolment modules and the shared authorisation helper before any of that code existed. They covered validation, ownership, draft visibility, search safety, capacity, duplicates and roles.

```
$ python3 -m unittest tests.test_security tests.test_courses tests.test_enrolment
EE
======================================================================
ERROR: test_security (unittest.loader._FailedTest.test_security)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_security
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_security.py", line 4, in <module>
    from elearn.security import require_role
ModuleNotFoundError: No module named 'elearn.security'


======================================================================
ERROR: test_courses (unittest.loader._FailedTest.test_courses)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_courses
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_courses.py", line 4, in <module>
    from tests.world import build_world
  File "tests/world.py", line 6, in <module>
    from elearn.courses import CourseService, SqliteCourseRepository
ModuleNotFoundError: No module named 'elearn.courses'


----------------------------------------------------------------------
Ran 2 tests in 0.000s

FAILED (errors=2)
```

Figure 8: Course, Enrolment and security tests fail before implementation.

After implementation all 45 tests in those three files passed, including the concurrency tests.

```
$ python3 -m unittest tests.test_security tests.test_courses tests.test_enrolment -v
test_allowed_role_passes (RequireRoleTests) ... ok
test_denial_message_does_not_reveal_which_roles_would_work (RequireRoleTests) ... ok
test_other_role_is_denied (RequireRoleTests) ... ok
test_admin_can_create_a_course (CreateCourseTests) ... ok
test_creation_is_audited (CreateCourseTests) ... ok
test_instructor_creates_an_unpublished_course (CreateCourseTests) ... ok
test_invalid_capacities_are_rejected (CreateCourseTests) ... ok
test_invalid_description_is_rejected (CreateCourseTests) ... ok
test_invalid_titles_are_rejected (CreateCourseTests) ... ok
test_student_cannot_create_a_course (CreateCourseTests) ... ok
test_title_is_trimmed (CreateCourseTests) ... ok
test_invalid_search_term_is_rejected (ListAndSearchTests) ... ok
test_list_published_excludes_drafts_and_is_sorted_by_title (ListAndSearchTests) ... ok
test_percent_and_underscore_are_treated_literally (ListAndSearchTests) ... ok
test_search_is_case_insensitive_substring_match (ListAndSearchTests) ... ok
test_search_never_returns_drafts (ListAndSearchTests) ... ok
test_sql_injection_in_search_returns_nothing_and_tables_survive (ListAndSearchTests) ... ok
test_admin_can_publish_any_course (PublishAndViewTests) ... ok
test_another_instructor_cannot_publish_it (PublishAndViewTests) ... ok
test_owner_can_publish (PublishAndViewTests) ... ok
test_published_course_is_visible_to_students (PublishAndViewTests) ... ok
test_publishing_an_unknown_course_raises_not_found (PublishAndViewTests) ... ok
test_student_cannot_publish (PublishAndViewTests) ... ok
test_unknown_course_raises_not_found_for_everyone (PublishAndViewTests) ... ok
test_unpublished_course_is_hidden_from_students_and_other_instructors (PublishAndViewTests) ... ok
test_unpublished_course_is_visible_to_owner_and_admin (PublishAndViewTests) ... ok
test_one_student_enrolling_ten_times_at_once_is_enrolled_once (ConcurrencyTests) ... ok
test_ten_students_racing_for_the_last_seat_yield_exactly_one_winner (ConcurrencyTests) ... ok
test_non_students_are_denied (CoursesForStudentTests) ... ok
test_returns_only_the_students_own_courses_sorted_by_title (CoursesForStudentTests) ... ok
test_a_place_is_freed_when_a_student_unenrols (EnrolTests) ... ok
test_cannot_enrol_in_an_unknown_course (EnrolTests) ... ok
test_cannot_enrol_in_an_unpublished_course (EnrolTests) ... ok
test_enrolling_twice_is_rejected (EnrolTests) ... ok
test_enrolment_is_audited (EnrolTests) ... ok
test_full_course_rejects_further_students (EnrolTests) ... ok
test_instructors_and_admins_cannot_enrol (EnrolTests) ... ok
test_student_can_enrol_in_a_published_course (EnrolTests) ... ok
test_admin_sees_the_roster (RosterTests) ... ok
test_other_instructors_and_students_are_denied (RosterTests) ... ok
test_owner_sees_the_roster_sorted_by_email (RosterTests) ... ok
test_unknown_course_raises_not_found (RosterTests) ... ok
test_non_students_cannot_unenrol (UnenrolTests) ... ok
test_unenrol_removes_the_enrolment (UnenrolTests) ... ok
test_unenrolling_when_not_enrolled_is_rejected (UnenrolTests) ... ok

----------------------------------------------------------------------
Ran 45 tests in 0.649s

OK
```

Figure 9: Course and Enrolment modules implemented, 45 tests pass.

### 3.6 Cycle 6: Presentation layer

The controller tests came first, including a full learning journey (register, log in, create, publish, enrol, view roster, unenrol), status code mapping, and a test that an unexpected error returns a generic 500 without leaking its message.

```
$ python3 -m unittest tests.test_controller
E
======================================================================
ERROR: test_controller (unittest.loader._FailedTest.test_controller)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_controller
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_controller.py", line 4, in <module>
    from elearn.controller import ApiController
ModuleNotFoundError: No module named 'elearn.controller'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Figure 10: Controller tests fail before implementation.

```
$ python3 -m unittest tests.test_controller -v
test_change_password_returns_200_and_revokes_the_session (ControllerTests) ... ok
test_full_course_and_duplicate_enrolment_return_409 (ControllerTests) ... ok
test_full_learning_journey (ControllerTests) ... ok
test_invalid_course_data_returns_400 (ControllerTests) ... ok
test_invalid_course_id_types_return_400_not_a_crash (ControllerTests) ... ok
test_login_failure_returns_a_generic_401 (ControllerTests) ... ok
test_login_success_returns_a_token (ControllerTests) ... ok
test_logout_invalidates_the_token (ControllerTests) ... ok
test_register_duplicate_returns_409 (ControllerTests) ... ok
test_register_returns_201_and_never_exposes_the_password_hash (ControllerTests) ... ok
test_register_weak_password_returns_400_with_the_rules_listed (ControllerTests) ... ok
test_repeated_failures_return_429 (ControllerTests) ... ok
test_unauthenticated_requests_return_401 (ControllerTests) ... ok
test_unexpected_errors_return_a_generic_500_without_leaking_details (ControllerTests) ... ok
test_unknown_course_returns_404 (ControllerTests) ... ok
test_wrong_role_returns_403 (ControllerTests) ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.284s

OK
```

Figure 11: Controller implemented, 16 tests pass.

### 3.7 Key implementation excerpts

Parameterised queries mean user input is never part of the SQL text. This is the repository method that looks up a user:

```python
def find_by_email(self, email: str) -> Optional[tuple]:
    with self._db.transaction() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return (self._to_user(row), row["password_hash"]) if row else None
```

The capacity check and the insert happen inside one transaction, so two students cannot both take the last seat:

```python
with self._db.transaction() as conn:
    row = conn.execute("SELECT capacity FROM courses WHERE id = ?", (course_id,)).fetchone()
    if row is None:
        raise NotFoundError("Course not found")
    if conn.execute("SELECT 1 FROM enrolments WHERE course_id = ? AND student_id = ?",
                    (course_id, student_id)).fetchone():
        raise EnrolmentError("Already enrolled in this course")
    taken = conn.execute("SELECT COUNT(*) FROM enrolments WHERE course_id = ?", (course_id,)).fetchone()[0]
    if taken >= row["capacity"]:
        raise CourseFullError("This course is full")
    conn.execute("INSERT INTO enrolments (course_id, student_id, enrolled_at) VALUES (?, ?, ?)",
                 (course_id, student_id, enrolled_at))
```

Login does not reveal whether an account exists, and a locked out client costs no hashing work:

```python
try:
    self._throttle.check(key)
except TooManyAttemptsError:
    self._audit.record("login_locked_out", client_id=str(client_id), email=key[1])
    raise
...
stored = found[1] if found else self._dummy_hash
password_ok = isinstance(password, str) and self._hasher.verify(password, stored)
if not (found and password_ok):
    self._throttle.record_failure(key)
    self._audit.record("login_failed", client_id=str(client_id), email=key[1])
    raise AuthenticationError("Invalid email or password")
```

---

## 4. Task 3: Testing, Refactoring and Results

### 4.1 Unit tests for all public methods

Tests are in the tests folder, one file per area. The totals are:

| Test file | Tests | What it covers |
|---|---|---|
| test_users.py | 46 | Registration, authentication, sessions, lockout, password change, roles, audit, password policy, edge cases |
| test_courses.py | 23 | Course creation, validation, publishing, visibility, listing, search |
| test_enrolment.py | 19 | Enrolling, capacity, duplicates, unenrolling, rosters, concurrency |
| test_controller.py | 16 | Status codes, full journey, input type checks, generic 500 |
| test_components.py | 30 | Direct tests of the hasher, session manager, throttle, all three repositories, audit log and course helper |
| test_security.py | 3 | require_role |
| Total | 137 | |

The services were tested through their public methods first. Because the brief asks for tests for all public methods, I then added test_components.py so that the lower-level public methods (the repositories, hasher, session manager, throttle and audit log) are tested directly and not just indirectly. I checked this by scanning the source for public methods whose names never appeared in a test, and that scan found 23 before test_components.py was added.

```
$ python3 -m unittest discover -s tests -t .
.........................................................................................................................................
----------------------------------------------------------------------
Ran 137 tests in 1.501s
OK

Tests per file:
     30   test_components
     16   test_controller
     23   test_courses
     19   test_enrolment
      3   test_security
     46   test_users
```

Figure 12: All 137 tests pass, with the number of tests in each file.

### 4.2 Refactoring and improvement based on test results

Refactoring 1: extracting the password policy. The first implementation had all the password checks inline in one long condition, inside register, and the same checks would have had to be repeated for change_password. This was a code smell (a long condition and duplicated logic). I wrote tests for a PasswordPolicy first, then extracted the Strategy classes LengthRule, CharacterMixRule and CommonPasswordRule, and injected the policy into UserService. Every existing test still passed unchanged, which is the evidence that behaviour was preserved. One new capability came from the refactor: the policy now reports every violation together instead of only the first.

```
$ python3 -m unittest tests.test_users
E
======================================================================
ERROR: test_users (unittest.loader._FailedTest.test_users)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_users
Traceback (most recent call last):
  File "/usr/lib/python3.11/unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "tests/test_users.py", line 7, in <module>
    from elearn.users import (LOCKOUT_WINDOW_SECONDS, SESSION_TTL_SECONDS, CharacterMixRule,
ImportError: cannot import name 'CharacterMixRule' from 'elearn.users' (elearn/users.py)


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Figure 13: Tests for the new policy classes written first.

```
$ python3 -m unittest tests.test_users -v
test_audit_log_never_contains_passwords (AuditTests) ... ok
test_registration_and_failed_login_are_recorded (AuditTests) ... ok
test_forged_and_malformed_tokens_are_rejected (AuthenticationTests) ... ok
test_login_is_case_insensitive_on_email (AuthenticationTests) ... ok
test_login_returns_a_token_that_resolves_to_the_user (AuthenticationTests) ... ok
test_logout_invalidates_the_token (AuthenticationTests) ... ok
test_non_string_credentials_are_rejected_cleanly (AuthenticationTests) ... ok
test_session_expires_after_the_time_to_live (AuthenticationTests) ... ok
test_session_is_still_valid_just_before_expiry (AuthenticationTests) ... ok
test_session_tokens_are_not_stored_in_plain_text (AuthenticationTests) ... ok
test_tokens_are_unique_and_unguessably_long (AuthenticationTests) ... ok
test_unknown_user_gets_the_same_error_as_a_wrong_password (AuthenticationTests) ... ok
test_wrong_password_is_rejected (AuthenticationTests) ... ok
test_changing_password_revokes_existing_sessions (ChangePasswordTests) ... ok
test_new_password_works_and_old_password_stops_working (ChangePasswordTests) ... ok
test_weak_new_password_is_rejected_and_old_one_still_works (ChangePasswordTests) ... ok
test_wrong_current_password_is_rejected (ChangePasswordTests) ... ok
test_client_is_locked_out_after_five_failures_even_with_the_right_password (LoginThrottleTests) ... ok
test_lockout_expires_after_the_window (LoginThrottleTests) ... ok
test_lockout_is_scoped_to_the_client_not_global (LoginThrottleTests) ... ok
test_successful_login_resets_the_failure_count (LoginThrottleTests) ... ok
test_character_mix_rule_needs_a_letter_and_a_digit (PasswordPolicyTests) ... ok
test_common_password_rule_is_case_insensitive (PasswordPolicyTests) ... ok
test_custom_policy_can_be_composed_from_rules (PasswordPolicyTests) ... ok
test_default_policy_accepts_a_strong_password (PasswordPolicyTests) ... ok
test_length_rule_enforces_both_bounds (PasswordPolicyTests) ... ok
test_non_string_password_is_rejected (PasswordPolicyTests) ... ok
test_policy_reports_every_violation_not_just_the_first (PasswordPolicyTests) ... ok
test_duplicate_email_is_rejected_case_insensitively (RegistrationTests) ... ok
test_email_is_normalised_to_lower_case_and_trimmed (RegistrationTests) ... ok
test_invalid_emails_are_rejected (RegistrationTests) ... ok
test_password_is_never_stored_in_plain_text (RegistrationTests) ... ok
test_register_returns_a_student_with_an_id (RegistrationTests) ... ok
test_same_password_produces_different_hashes_because_of_salting (RegistrationTests) ... ok
test_sql_injection_in_email_is_rejected_and_tables_survive (RegistrationTests) ... ok
test_very_long_password_is_rejected_to_prevent_hashing_abuse (RegistrationTests) ... ok
test_weak_passwords_are_rejected (RegistrationTests) ... ok
test_a_student_cannot_promote_themselves (RoleManagementTests) ... ok
test_admin_can_promote_a_student_to_instructor (RoleManagementTests) ... ok
test_bootstrap_admin_creates_an_admin (RoleManagementTests) ... ok
test_invalid_role_value_is_rejected (RoleManagementTests) ... ok
test_promoting_an_unknown_user_raises_not_found (RoleManagementTests) ... ok

----------------------------------------------------------------------
Ran 42 tests in 0.305s

OK
```

Figure 14: Policy extracted. 42 tests pass, including all the earlier registration tests.

Refactoring 2: a shared authorisation helper. The administrator check in set_role was written inline. Once the Course and Enrolment modules needed role checks, I moved it into require_role and made set_role use it too, so authorisation behaves identically everywhere.

Defect found by tests. When I added direct tests for the lower-level components, a test that passed a missing (None) stored hash to PasswordHasher.verify failed with an AttributeError instead of returning False. The method only caught ValueError and TypeError. I fixed it to also catch AttributeError. This was a real robustness bug that the earlier, higher-level tests had not exposed.

Gap found from the demo. Running the end-to-end demo showed that a blocked login attempt (the sixth one) left no trace in the audit log, so a lockout was invisible to anyone reviewing it. I wrote a test first, saw it fail, and then added a login_locked_out audit event.

Coverage-driven edge cases. After the first full coverage run, three branches had not been exercised: a malformed email at login, a non-text email at registration, and a valid session for an account that has since been deleted. I wrote tests for each.

### 4.3 Coverage

Branch coverage is 100% across every module, including 72 branches.

```
$ coverage run --branch --source=elearn -m unittest discover -s tests -t . && coverage report -m
Name                   Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------
elearn/__init__.py         0      0      0      0   100%
elearn/audit.py           11      0      0      0   100%
elearn/controller.py      86      0      8      0   100%
elearn/courses.py         89      0     14      0   100%
elearn/database.py        20      0      0      0   100%
elearn/enrolment.py       67      0     10      0   100%
elearn/errors.py          18      0      0      0   100%
elearn/security.py         4      0      2      0   100%
elearn/users.py          239      0     38      0   100%
------------------------------------------------------------------
TOTAL                    534      0     72      0   100%
```

Figure 15: Line and branch coverage report.

Coverage shows that every line ran during the tests. It does not show that the tests would notice a bug. To test that, I wrote a mutation check (mutation_check.py). It deliberately breaks ten security and business rules one at a time, runs the whole suite each time, and restores the file.

```
$ python3 mutation_check.py
CAUGHT    Remove lockout check
CAUGHT    Keep sessions after password change
CAUGHT    Let anyone change roles
CAUGHT    Sessions never expire
SURVIVED  Skip dummy hash for unknown users (timing defence, not unit testable)
CAUGHT    Off-by-one on capacity
CAUGHT    Show drafts to everyone
CAUGHT    Do not escape LIKE wildcards
CAUGHT    Leak internal error text
CAUGHT    Disable require_role

9 caught, 1 survived
```

Figure 16: The suite catches 9 of the 10 deliberately introduced faults.

The one fault that survived was removing the dummy hash that equalises response time for unknown accounts. That is expected: the behaviour is identical apart from timing, which an ordinary unit test cannot observe reliably. It is a known gap in the evidence and is noted in Section 5.

### 4.4 End to end demonstration

The demo script drives the whole platform through the presentation layer. It shows a student registering, a weak password, a duplicate email and a SQL injection attempt being rejected, a student blocked from creating a course, drafts staying hidden until published, a duplicate enrolment refused, a malicious course id rejected, a forged token refused, and an attacker locked out after five failed logins.

```
$ python3 demo.py
--- Accounts and security checks ---
Register student                                     -> 201 {'id': 3, 'email': 'molly@school.example', 'role': 'student'}
Register with a weak password                        -> 400 {'error': 'Password must be at least 10 characters long; Password must contain at least one letter and one digit'}
Register the same email again                        -> 409 {'error': 'An account with that email already exists'}
Register with a SQL injection email                  -> 400 {'error': 'Invalid email address'}
Login with the wrong password                        -> 401 {'error': 'Invalid email or password'}

--- Courses and enrolment ---
Student tries to create a course                     -> 403 {'error': 'Access denied'}
Instructor creates a course                          -> 201 {'id': 1, 'title': 'Secure Software Engineering', 'description': 'OO design and TDD', 'capacity': 2, 'published': False}
Student lists courses (draft is hidden)              -> 200 {'courses': []}
Instructor publishes the course                      -> 200 {'id': 1, 'title': 'Secure Software Engineering', 'description': 'OO design and TDD', 'capacity': 2, 'published': True}
Student enrols                                       -> 201 {'course_id': 1, 'student_id': 3}
Student enrols again                                 -> 409 {'error': 'Already enrolled in this course'}
Student requests the roster                          -> 403 {'error': 'Access denied'}
Instructor requests the roster                       -> 200 {'students': ['molly@school.example']}
Enrol with a malicious course id                     -> 400 {'error': 'Course id must be a whole number'}
Use a forged token                                   -> 401 {'error': 'Invalid or expired session'}

--- Brute force protection ---
Failed login attempt 1                               -> 401 {'error': 'Invalid email or password'}
Failed login attempt 2                               -> 401 {'error': 'Invalid email or password'}
Failed login attempt 3                               -> 401 {'error': 'Invalid email or password'}
Failed login attempt 4                               -> 401 {'error': 'Invalid email or password'}
Failed login attempt 5                               -> 401 {'error': 'Invalid email or password'}
Failed login attempt 6                               -> 429 {'error': 'Too many failed attempts, try again later'}

--- Audit trail (no secrets recorded) ---
login_failed: {'client_id': 'attacker', 'email': 'teacher@school.example'}
login_failed: {'client_id': 'attacker', 'email': 'teacher@school.example'}
login_failed: {'client_id': 'attacker', 'email': 'teacher@school.example'}
login_locked_out: {'client_id': 'attacker', 'email': 'teacher@school.example'}
```

Figure 17: Output of demo.py.

### 4.5 How to run

```
python3 -m unittest discover -s tests -t . -v
python3 demo.py
python3 -m coverage run --branch --source=elearn -m unittest discover -s tests -t .
python3 -m coverage report -m
python3 mutation_check.py
```

Coverage is the only third party tool, and it is optional (pip install coverage).

---

## 5. Limitations and Further Work

These are the points I would raise before using this in production, listed honestly.

1. Transport security is not implemented. TLS must be provided at a reverse proxy, and session tokens must only travel over HTTPS.
2. Sessions and the audit log are held in memory. They are lost on restart and cannot be shared between several running copies, so horizontal scaling needs a shared session store (for example Redis) and a durable audit log.
3. The data layer uses a single SQLite connection guarded by one lock. That is correct and simple, but writes are serialised. A production deployment would use a connection pool and a server database such as PostgreSQL. The repositories are the only code that would change.
4. The lockout is keyed by the client identifier supplied by the caller. Behind a real web server this should be the client IP address, and a per-account limit would also be needed to defend against distributed attacks. I chose per-client scoping deliberately, because a pure per-account lockout lets an attacker lock a victim out.
5. There is no multi-factor authentication, email verification or password reset flow. These are standard requirements for a real platform.
6. Unexpected errors return a generic 500 response, which is correct for the client, but the server does not yet log the underlying exception. A real system must log it for operators.
7. The timing equalisation for unknown accounts is not covered by a unit test, as the mutation check shows.
8. Tests use a deliberately low scrypt cost for speed. The production default is higher, and the hasher records its cost in each hash so it can be increased over time.
9. The presentation layer is a controller class standing in for HTTP handlers. A real deployment would put a web framework in front of it and add CSRF protection, security headers and request rate limiting.
10. The modules share one database schema. Extracting a module into a microservice would require splitting its tables and replacing direct service calls with an API.

---

## 6. Conclusion

The platform meets the brief: a justified layered architecture with a diagram, three modules, a security analysis, a working object-oriented implementation, TDD evidence through red and green runs, tests for every public method, and documented refactoring. The tests drove real improvements, including a refactored password policy, a robustness fix in the hasher and a missing audit event. Coverage is 100%, a mutation check shows the tests catch nine of ten deliberately introduced security faults, and the remaining limitations are stated openly above.

---

## Appendix: Project Files

- elearn/users.py, courses.py, enrolment.py, controller.py, security.py, audit.py, database.py, errors.py
- tests/test_users.py, test_courses.py, test_enrolment.py, test_controller.py, test_components.py, test_security.py, helpers.py, world.py
- demo.py and mutation_check.py
- evidence/ holds the raw terminal output behind every figure
