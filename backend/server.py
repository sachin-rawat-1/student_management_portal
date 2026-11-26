import hashlib
import hmac
import json
import math
import secrets
import time
from datetime import date
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

from database import connect_database

PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
HOST = "127.0.0.1"
PORT = 8000
SESSION_TIMEOUT = 1800
sessions = {}

PUBLIC_FILES = {"/", "/index.html", "/login.html", "/style.css", "/login.js"}
PROTECTED_FILES = {
    "/dashboard.html", "/students.html", "/view_students.html",
    "/attendance.html", "/marks.html", "/reports.html",
    "/app.js", "/students.js", "/view_students.js",
    "/attendance.js", "/marks.js", "/reports.js", "/logout.js"
}

class StudentPortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, data, status=200, extra_headers=None):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:;")
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError:
            raise ValueError("Invalid request size.")
        if length < 1 or length > 20000:
            raise ValueError("Request body is empty or too large.")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Invalid JSON.")
        if not isinstance(data, dict):
            raise ValueError("A JSON object is required.")
        return data

    def get_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        morsel = cookie.get("student_portal_session")
        return morsel.value if morsel else None

    def current_session(self):
        token = self.get_token()
        if not token:
            return None
        session = sessions.get(token)
        if not session:
            return None
        now = time.time()
        if now - session["last_activity"] > SESSION_TIMEOUT:
            sessions.pop(token, None)
            return None
        session["last_activity"] = now
        return session

    def authenticated(self):
        return self.current_session() is not None

    def same_origin(self):
        # Use exactly http://127.0.0.1:8000 in the browser.
        origin = self.headers.get("Origin")
        return origin == f"http://{HOST}:{PORT}"

    def do_GET(self):
        path = unquote(urlparse(self.path).path)

        if path.startswith("/api/") and not self.authenticated():
            self.send_json({"error": "Please log in first."}, 401)
            return

        if path in PROTECTED_FILES and not self.authenticated():
            self.send_response(302)
            self.send_header("Location", "/login.html")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return

        if path == "/api/me":
            session = self.current_session()
            self.send_json({"username": session["username"]})
            return

        if path == "/api/dashboard":
            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT COUNT(*) AS total_students FROM students")
                total_students = cur.fetchone()["total_students"]
                cur.execute("SELECT COUNT(DISTINCT course) AS total_courses FROM students")
                total_courses = cur.fetchone()["total_courses"]
                cur.execute("SELECT COUNT(*) AS total_attendance FROM attendance")
                total_attendance = cur.fetchone()["total_attendance"]
                cur.execute("SELECT COUNT(*) AS total_marks FROM marks")
                total_marks = cur.fetchone()["total_marks"]
                self.send_json({
                    "total_students": total_students,
                    "total_courses": total_courses,
                    "attendance_records": total_attendance,
                    "marks_records": total_marks
                })
            except Exception as exc:
                print("Dashboard error:", exc)
                self.send_json({"error": "Unable to load dashboard."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/students":
            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("""SELECT id, roll_no, name, email, phone, course,
                                      semester, created_at
                               FROM students ORDER BY roll_no""")
                self.send_json(cur.fetchall())
            except Exception as exc:
                print("Student retrieval error:", exc)
                self.send_json({"error": "Unable to retrieve students."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/attendance":
            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("""SELECT a.id, s.id AS student_id, s.roll_no, s.name,
                                      a.attendance_date, a.status
                               FROM attendance a
                               JOIN students s ON s.id = a.student_id
                               ORDER BY a.attendance_date DESC, s.roll_no""")
                rows = cur.fetchall()
                for row in rows:
                    row["attendance_date"] = row["attendance_date"].isoformat()
                self.send_json(rows)
            except Exception as exc:
                print("Attendance retrieval error:", exc)
                self.send_json({"error": "Unable to retrieve attendance."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/marks":
            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("""SELECT m.id, s.id AS student_id, s.roll_no, s.name,
                                      m.subject, m.marks_obtained, m.total_marks
                               FROM marks m
                               JOIN students s ON s.id = m.student_id
                               ORDER BY s.roll_no, m.subject""")
                rows = cur.fetchall()
                for row in rows:
                    row["marks_obtained"] = float(row["marks_obtained"])
                    row["total_marks"] = float(row["total_marks"])
                self.send_json(rows)
            except Exception as exc:
                print("Marks retrieval error:", exc)
                self.send_json({"error": "Unable to retrieve marks."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/reports":
            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("""
                    SELECT s.id, s.roll_no, s.name, s.course, s.semester,
                           COALESCE(att.total_days, 0) AS total_days,
                           COALESCE(att.present_days, 0) AS present_days,
                           COALESCE(mk.total_obtained, 0) AS total_obtained,
                           COALESCE(mk.total_possible, 0) AS total_possible
                    FROM students s
                    LEFT JOIN (
                        SELECT student_id, COUNT(*) AS total_days,
                               SUM(status = 'Present') AS present_days
                        FROM attendance GROUP BY student_id
                    ) att ON att.student_id = s.id
                    LEFT JOIN (
                        SELECT student_id, SUM(marks_obtained) AS total_obtained,
                               SUM(total_marks) AS total_possible
                        FROM marks GROUP BY student_id
                    ) mk ON mk.student_id = s.id
                    ORDER BY s.roll_no
                """)
                rows = cur.fetchall()
                for row in rows:
                    row["attendance_percentage"] = (
                        round(row["present_days"] * 100 / row["total_days"], 2)
                        if row["total_days"] else None
                    )
                    row["marks_percentage"] = (
                        round(float(row["total_obtained"]) * 100 / float(row["total_possible"]), 2)
                        if row["total_possible"] else None
                    )
                    row["total_obtained"] = float(row["total_obtained"])
                    row["total_possible"] = float(row["total_possible"])
                self.send_json(rows)
            except Exception as exc:
                print("Report error:", exc)
                self.send_json({"error": "Unable to generate reports."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        # Restrict static file serving to files in the project frontend.
        if path not in PUBLIC_FILES and path not in PROTECTED_FILES:
            self.send_error(404, "Not found")
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/login":
            if not self.same_origin():
                self.send_json({"error": "Invalid request origin. Open the portal at http://127.0.0.1:8000."}, 403)
                return
            try:
                data = self.read_json()
                username = str(data.get("username", "")).strip()
                password = data.get("password", "")
                if not username or len(username) > 50 or not isinstance(password, str) or not password or len(password) > 1024:
                    raise ValueError
            except (ValueError, TypeError):
                self.send_json({"error": "Enter a valid username and password."}, 400)
                return

            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            admin = None
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id, username, password_hash FROM admins WHERE username=%s", (username,))
                admin = cur.fetchone()
            except Exception as exc:
                print("Login database error:", exc)
                self.send_json({"error": "Unable to process login."}, 500)
                return
            finally:
                if cur: cur.close()
                conn.close()

            valid = False
            if admin:
                try:
                    algorithm, salt_hex, key_hex = admin["password_hash"].split("$")
                    if algorithm == "scrypt":
                        salt = bytes.fromhex(salt_hex)
                        expected = bytes.fromhex(key_hex)
                        actual = hashlib.scrypt(
                            password.encode("utf-8"), salt=salt,
                            n=2**14, r=8, p=1, dklen=len(expected)
                        )
                        valid = hmac.compare_digest(actual, expected)
                except (ValueError, TypeError):
                    valid = False

            if not valid:
                self.send_json({"error": "Invalid username or password."}, 401)
                return

            token = secrets.token_urlsafe(32)
            sessions[token] = {
                "admin_id": admin["id"],
                "username": admin["username"],
                "last_activity": time.time()
            }
            self.send_json(
                {"message": "Login successful."},
                200,
                {"Set-Cookie": f"student_portal_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_TIMEOUT}"}
            )
            return

        if path == "/api/logout":
            if not self.same_origin():
                self.send_json({"error": "Invalid request origin."}, 403)
                return
            token = self.get_token()
            if token:
                sessions.pop(token, None)
            self.send_json(
                {"message": "Logged out."},
                200,
                {"Set-Cookie": "student_portal_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"}
            )
            return

        if not self.authenticated():
            self.send_json({"error": "Please log in first."}, 401)
            return
        if not self.same_origin():
            self.send_json({"error": "Invalid request origin."}, 403)
            return

        try:
            data = self.read_json()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, 400)
            return

        if path == "/api/students":
            try:
                roll = str(data.get("roll", "")).strip()
                name = str(data.get("name", "")).strip()
                email = str(data.get("email", "")).strip()
                phone = str(data.get("phone", "")).strip()
                course = str(data.get("course", "")).strip()
                semester = int(data.get("semester", 0))
                if not all([roll, name, email, phone, course]):
                    raise ValueError
                if len(roll) > 20 or len(name) > 100 or len(email) > 100 or len(phone) > 15 or len(course) > 100 or not 1 <= semester <= 8:
                    raise ValueError
                if "@" not in email or "." not in email.split("@")[-1]:
                    raise ValueError
            except (ValueError, TypeError):
                self.send_json({"error": "Enter valid student details."}, 400)
                return

            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("""INSERT INTO students
                    (roll_no, name, email, phone, course, semester)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (roll, name, email, phone, course, semester))
                conn.commit()
                self.send_json({"message": "Student added successfully.", "id": cur.lastrowid}, 201)
            except Exception as exc:
                conn.rollback()
                if getattr(exc, "errno", None) == 1062:
                    self.send_json({"error": "That roll number already exists."}, 409)
                else:
                    print("Add student error:", exc)
                    self.send_json({"error": "Unable to save student."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/attendance":
            try:
                student_id = int(data.get("student_id", 0))
                attendance_date = date.fromisoformat(str(data.get("attendance_date", "")))
                status = str(data.get("status", ""))
                if student_id <= 0 or status not in ("Present", "Absent") or attendance_date > date.today():
                    raise ValueError
            except (ValueError, TypeError):
                self.send_json({"error": "Enter valid attendance details; future dates are not allowed."}, 400)
                return

            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("""INSERT INTO attendance (student_id, attendance_date, status)
                               VALUES (%s, %s, %s)
                               ON DUPLICATE KEY UPDATE status=VALUES(status)""",
                            (student_id, attendance_date, status))
                conn.commit()
                self.send_json({"message": "Attendance saved successfully."}, 201)
            except Exception as exc:
                conn.rollback()
                if getattr(exc, "errno", None) == 1452:
                    self.send_json({"error": "Student not found."}, 400)
                else:
                    print("Attendance save error:", exc)
                    self.send_json({"error": "Unable to save attendance."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        if path == "/api/marks":
            try:
                student_id = int(data.get("student_id", 0))
                subject = str(data.get("subject", "")).strip()
                obtained = float(data.get("marks_obtained", -1))
                total = float(data.get("total_marks", 0))
                if not subject or len(subject) > 100 or student_id <= 0:
                    raise ValueError
                if not math.isfinite(obtained) or not math.isfinite(total):
                    raise ValueError
                if obtained < 0 or total <= 0 or obtained > total or obtained > 999.99 or total > 999.99:
                    raise ValueError
            except (ValueError, TypeError):
                self.send_json({"error": "Enter valid marks; obtained marks must not exceed maximum marks."}, 400)
                return

            conn = connect_database()
            if conn is None:
                self.send_json({"error": "Database connection failed."}, 500)
                return
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("""INSERT INTO marks
                               (student_id, subject, marks_obtained, total_marks)
                               VALUES (%s, %s, %s, %s)
                               ON DUPLICATE KEY UPDATE
                                 marks_obtained=VALUES(marks_obtained),
                                 total_marks=VALUES(total_marks)""",
                            (student_id, subject, obtained, total))
                conn.commit()
                self.send_json({"message": "Marks saved successfully. Existing marks for this subject were updated if present."}, 201)
            except Exception as exc:
                conn.rollback()
                if getattr(exc, "errno", None) == 1452:
                    self.send_json({"error": "Student not found."}, 400)
                else:
                    print("Marks save error:", exc)
                    self.send_json({"error": "Unable to save marks."}, 500)
            finally:
                if cur: cur.close()
                conn.close()
            return

        self.send_json({"error": "Endpoint not found."}, 404)

    def do_PUT(self):
        if not self.authenticated():
            self.send_json({"error": "Please log in first."}, 401)
            return
        if not self.same_origin():
            self.send_json({"error": "Invalid request origin."}, 403)
            return

        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "students"]:
            self.send_json({"error": "Endpoint not found."}, 404)
            return
        try:
            student_id = int(parts[2])
            data = self.read_json()
            roll = str(data.get("roll", "")).strip()
            name = str(data.get("name", "")).strip()
            email = str(data.get("email", "")).strip()
            phone = str(data.get("phone", "")).strip()
            course = str(data.get("course", "")).strip()
            semester = int(data.get("semester", 0))
            if student_id <= 0 or not all([roll, name, email, phone, course]):
                raise ValueError
            if len(roll) > 20 or len(name) > 100 or len(email) > 100 or len(phone) > 15 or len(course) > 100 or not 1 <= semester <= 8:
                raise ValueError
            if "@" not in email or "." not in email.split("@")[-1]:
                raise ValueError
        except (ValueError, TypeError):
            self.send_json({"error": "Enter valid student information."}, 400)
            return

        conn = connect_database()
        if conn is None:
            self.send_json({"error": "Database connection failed."}, 500)
            return
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("""UPDATE students SET roll_no=%s, name=%s, email=%s,
                           phone=%s, course=%s, semester=%s WHERE id=%s""",
                        (roll, name, email, phone, course, semester, student_id))
            if cur.rowcount == 0:
                cur.execute("SELECT id FROM students WHERE id=%s", (student_id,))
                if cur.fetchone() is None:
                    self.send_json({"error": "Student not found."}, 404)
                    return
            conn.commit()
            self.send_json({"message": "Student updated successfully."})
        except Exception as exc:
            conn.rollback()
            if getattr(exc, "errno", None) == 1062:
                self.send_json({"error": "That roll number already exists."}, 409)
            else:
                print("Update student error:", exc)
                self.send_json({"error": "Unable to update student."}, 500)
        finally:
            if cur: cur.close()
            conn.close()

    def do_DELETE(self):
        if not self.authenticated():
            self.send_json({"error": "Please log in first."}, 401)
            return
        if not self.same_origin():
            self.send_json({"error": "Invalid request origin."}, 403)
            return

        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "students"]:
            self.send_json({"error": "Endpoint not found."}, 404)
            return
        try:
            student_id = int(parts[2])
            if student_id <= 0:
                raise ValueError
        except ValueError:
            self.send_json({"error": "Invalid student ID."}, 400)
            return

        conn = connect_database()
        if conn is None:
            self.send_json({"error": "Database connection failed."}, 500)
            return
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
            if cur.rowcount == 0:
                self.send_json({"error": "Student not found."}, 404)
                return
            conn.commit()
            self.send_json({"message": "Student deleted successfully."})
        except Exception as exc:
            conn.rollback()
            print("Delete student error:", exc)
            self.send_json({"error": "Unable to delete student."}, 500)
        finally:
            if cur: cur.close()
            conn.close()

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), StudentPortalHandler)
    print("Student Management Portal is running.")
    print(f"Open http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
