
import sqlite3
import hashlib
import secrets
from pathlib import Path


# Database location
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_success.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# Create database tables

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            institution TEXT NOT NULL DEFAULT '',
            course_name TEXT NOT NULL DEFAULT '',
            department TEXT NOT NULL DEFAULT '',
            current_semester TEXT NOT NULL DEFAULT '',
            academic_year TEXT NOT NULL DEFAULT ''
        )
    """)

    # Add profile fields to existing student accounts without losing data.
    cursor.execute("PRAGMA table_info(students)")
    student_columns = [column[1] for column in cursor.fetchall()]

    profile_columns = {
        "institution": "TEXT NOT NULL DEFAULT ''",
        "course_name": "TEXT NOT NULL DEFAULT ''",
        "department": "TEXT NOT NULL DEFAULT ''",
        "current_semester": "TEXT NOT NULL DEFAULT ''",
        "academic_year": "TEXT NOT NULL DEFAULT ''",
    }

    for column_name, column_definition in profile_columns.items():
        if column_name not in student_columns:
            cursor.execute(
                f"ALTER TABLE students ADD COLUMN {column_name} {column_definition}"
            )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            classes_held INTEGER,
            classes_attended INTEGER,
            assignments_total INTEGER,
            assignments_submitted INTEGER,
            quiz_average REAL,
            exam_score REAL,
            study_hours_weekly REAL,
            is_archived INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (student_id)
                REFERENCES students(student_id)
        )
    """)
    cursor.execute("PRAGMA table_info(academic_records)")
    columns = [column[1] for column in cursor.fetchall()]

    if "is_archived" not in columns:
        cursor.execute("""
            ALTER TABLE academic_records
            ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            classes_held INTEGER,
            classes_attended INTEGER,
            assignments_total INTEGER,
            assignments_submitted INTEGER,
            quiz_average REAL,
            exam_score REAL,
            study_hours_weekly REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id)
                REFERENCES students(student_id)
        )
    """)

    cursor.execute("""
        INSERT INTO academic_history (
            student_id,
            subject,
            classes_held,
            classes_attended,
            assignments_total,
            assignments_submitted,
            quiz_average,
            exam_score,
            study_hours_weekly
        )
        SELECT
            a.student_id,
            a.subject,
            a.classes_held,
            a.classes_attended,
            a.assignments_total,
            a.assignments_submitted,
            a.quiz_average,
            a.exam_score,
            a.study_hours_weekly
        FROM academic_records AS a
        WHERE NOT EXISTS (
            SELECT 1
            FROM academic_history AS h
            WHERE h.student_id = a.student_id
            AND LOWER(h.subject) = LOWER(a.subject)
        )
    """)

    connection.commit()
    connection.close()


# Securely hash passwords
def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    ).hex()

    return password_hash, salt


# Register a new student
def register_student(
    full_name,
    username,
    password,
    institution="",
    course_name="",
    department="",
    current_semester="",
    academic_year=""
):

    if not full_name.strip() or not username.strip():
        raise ValueError("Name and username are required.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    student_id = "STU" + secrets.token_hex(4).upper()
    password_hash, salt = hash_password(password)
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO students (
                student_id, full_name, username, password_hash, password_salt,
                institution, course_name, department, current_semester, academic_year
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            full_name.strip(),
            username.strip().lower(),
            password_hash,
            salt,
            institution.strip(),
            course_name.strip(),
            department.strip(),
            current_semester.strip(),
            academic_year.strip()
        ))
        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError("This username is already registered.")

    finally:
        connection.close()

    return student_id


def get_student_profile(student_id):
    """Return the profile for one student, never another student's data."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute("""
            SELECT student_id, full_name, username, institution, course_name,
                   department, current_semester, academic_year
            FROM students
            WHERE student_id = ?
        """, (student_id,)).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def update_student_profile(
    student_id, full_name, institution, course_name, department,
    current_semester, academic_year
):
    """Update editable profile fields for the authenticated student."""
    if not full_name.strip():
        raise ValueError("Full name cannot be empty.")

    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE students
            SET full_name = ?, institution = ?, course_name = ?, department = ?,
                current_semester = ?, academic_year = ?
            WHERE student_id = ?
        """, (
            full_name.strip(), institution.strip(), course_name.strip(),
            department.strip(), current_semester.strip(), academic_year.strip(),
            student_id
        ))

        if cursor.rowcount == 0:
            raise ValueError("Student profile was not found.")

        connection.commit()
        return "Student profile updated successfully."
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# Authenticate an existing student
def authenticate_student(username, password):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT student_id, full_name, password_hash, password_salt,
               institution, course_name, department, current_semester, academic_year
        FROM students
        WHERE username = ?
    """, (username.strip().lower(),))

    student = cursor.fetchone()
    connection.close()

    if student is None:
        return None

    (student_id, full_name, stored_hash, salt, institution, course_name,
     department, current_semester, academic_year) = student

    entered_hash, _ = hash_password(password, salt)

    if secrets.compare_digest(entered_hash, stored_hash):
        return {
            "student_id": student_id,
            "full_name": full_name,
            "institution": institution,
            "course_name": course_name,
            "department": department,
            "current_semester": current_semester,
            "academic_year": academic_year
        }

    return None


# Retrieve records belonging to one student
def get_student_records(student_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT record_id, student_id, subject, classes_held, classes_attended,
               assignments_total, assignments_submitted, quiz_average, exam_score,
               study_hours_weekly, is_archived
        FROM academic_records
        WHERE student_id = ?
        AND is_archived = 0
    """, (student_id,))

    records = cursor.fetchall()
    connection.close()

    return records


def update_student_record(
    record_id,
    student_id,
    subject,
    classes_held,
    classes_attended,
    assignments_total,
    assignments_submitted,
    quiz_average,
    exam_score,
    study_hours_weekly
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT subject
            FROM academic_records
            WHERE record_id = ? AND student_id = ?
        """, (record_id, student_id))

        existing = cursor.fetchone()

        if not existing:
            return "Record not found."

        if existing[0].lower() != subject.strip().lower():
            return "Subject name cannot be changed here."

        return add_student_record(
            student_id,
            subject,
            classes_held,
            classes_attended,
            assignments_total,
            assignments_submitted,
            quiz_average,
            exam_score,
            study_hours_weekly
        )

    finally:
        connection.close()



def get_student_history(student_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            subject,
            classes_attended,
            classes_held,
            assignments_submitted,
            assignments_total,
            quiz_average,
            exam_score,
            study_hours_weekly,
            recorded_at
        FROM academic_history
        WHERE student_id = ?
        ORDER BY recorded_at ASC
    """, (student_id,))

    history = cursor.fetchall()

    connection.close()

    return history


def delete_student_record(record_id, student_id):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE academic_records
            SET is_archived = 1
            WHERE record_id = ?
            AND student_id = ?
            AND is_archived = 0
        """, (record_id, student_id))

        if cursor.rowcount == 0:
            return "Record not found or already archived."

        connection.commit()
        return "Academic record archived successfully."

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_archived_student_records(student_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM academic_records
        WHERE student_id = ?
        AND is_archived = 1
    """, (student_id,))

    records = cursor.fetchall()
    connection.close()

    return records

def restore_student_record(record_id, student_id):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE academic_records
            SET is_archived = 0
            WHERE record_id = ?
            AND student_id = ?
            AND is_archived = 1
        """, (record_id, student_id))

        if cursor.rowcount == 0:
            return "Archived record not found."

        connection.commit()
        return "Academic record restored successfully."

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()       

def add_student_record(
    student_id,
    subject,
    classes_held,
    classes_attended,
    assignments_total,
    assignments_submitted,
    quiz_average,
    exam_score,
    study_hours_weekly
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        new_values = (
            classes_held,
            classes_attended,
            assignments_total,
            assignments_submitted,
            quiz_average,
            exam_score,
            study_hours_weekly
        )

        cursor.execute("""
            SELECT
                record_id,
                subject,
                classes_held,
                classes_attended,
                assignments_total,
                assignments_submitted,
                quiz_average,
                exam_score,
                study_hours_weekly
            FROM academic_records
            WHERE student_id = ?
            AND LOWER(subject) = LOWER(?)
            AND is_archived = 0
        """, (student_id, subject))

        existing_record = cursor.fetchone()

        if existing_record:
            old_values = tuple(existing_record[2:])

            if old_values == new_values:
                return "No changes detected."

            cursor.execute("""
                UPDATE academic_records
                SET
                    classes_held = ?,
                    classes_attended = ?,
                    assignments_total = ?,
                    assignments_submitted = ?,
                    quiz_average = ?,
                    exam_score = ?,
                    study_hours_weekly = ?
                WHERE record_id = ?
            """, (*new_values, existing_record[0]))

        else:
            cursor.execute("""
                INSERT INTO academic_records (
                    student_id,
                    subject,
                    classes_held,
                    classes_attended,
                    assignments_total,
                    assignments_submitted,
                    quiz_average,
                    exam_score,
                    study_hours_weekly
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, subject, *new_values))

        cursor.execute("""
            SELECT
                student_id,
                subject,
                classes_held,
                classes_attended,
                assignments_total,
                assignments_submitted,
                quiz_average,
                exam_score,
                study_hours_weekly
            FROM academic_records
            WHERE student_id = ?
            AND LOWER(subject) = LOWER(?)
        """, (student_id, subject))

        record = cursor.fetchone()

        cursor.execute("""
            INSERT INTO academic_history (
                student_id,
                subject,
                classes_held,
                classes_attended,
                assignments_total,
                assignments_submitted,
                quiz_average,
                exam_score,
                study_hours_weekly
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record)

        connection.commit()
        return "Academic record saved successfully."

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()



if __name__ == "__main__":

    initialize_database()

    print("Student Success AI Database")
    print("---------------------------")
    print("Database initialized successfully!")