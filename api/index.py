import os
import psycopg2
import functools
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

# ----------- Flask App Setup -----------

_base = os.path.dirname(os.path.abspath(__file__))
_templates = os.path.join(_base, "..", "app", "templates")
_static = os.path.join(_base, "..", "app", "static")

app = Flask(__name__,
            template_folder=os.path.abspath(_templates),
            static_folder=os.path.abspath(_static))

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")

# ----------- Database -----------

_db_initialized = False


def _get_db():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, connect_timeout=5)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "studentdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres123"),
        connect_timeout=5
    )


def _ensure_tables():
    global _db_initialized
    if _db_initialized:
        return
    conn = _get_db()
    cur = conn.cursor()

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            course VARCHAR(100) NOT NULL
        )
    """)

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL
        )
    """)

    # Seed default admin user if none exist
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (admin_user, generate_password_hash(admin_pass))
        )

    conn.commit()
    cur.close()
    conn.close()
    _db_initialized = True


# ----------- Auth Decorator -----------

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ----------- Auth Routes -----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            _ensure_tables()
            conn = _get_db()
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row and check_password_hash(row[0], password):
                session["username"] = username
                return redirect(url_for("index"))
            else:
                error = "Invalid username or password. Please try again."
        except Exception as e:
            error = f"Database error: {e}"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect(url_for("index"))

    error = None
    success = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            try:
                _ensure_tables()
                conn = _get_db()
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    error = "Username already exists. Please choose another."
                else:
                    cur.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                        (username, generate_password_hash(password))
                    )
                    conn.commit()
                    success = f"Account created successfully! You can now sign in."
                cur.close()
                conn.close()
            except Exception as e:
                error = f"Database error: {e}"

    return render_template("register.html", error=error, success=success)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if "username" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        try:
            _ensure_tables()
            conn = _get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                # Store verified username in session so reset page is accessible
                session["reset_user"] = username
                return redirect(url_for("reset_password"))
            else:
                error = "No account found with that username."
        except Exception as e:
            error = f"Database error: {e}"

    return render_template("forgot_password.html", error=error)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    username = session.get("reset_user")
    if not username:
        return redirect(url_for("forgot_password"))

    error = None
    success = None

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            try:
                _ensure_tables()
                conn = _get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE username = %s",
                    (generate_password_hash(password), username)
                )
                conn.commit()
                cur.close()
                conn.close()
                session.pop("reset_user", None)
                success = "Password reset successfully! You can now sign in."
            except Exception as e:
                error = f"Database error: {e}"

    return render_template("reset_password.html", username=username, error=error, success=success)


# ----------- Student Routes (Protected) -----------

@app.route("/")
@login_required
def index():
    students = []
    db_error = None
    try:
        _ensure_tables()
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id")
        students = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("DB error:", e)
        db_error = str(e)
    return render_template("index.html", students=students, db_error=db_error)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        course = request.form.get("course")
        try:
            _ensure_tables()
            conn = _get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO students (name, email, course) VALUES (%s, %s, %s)",
                (name, email, course)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("index"))
        except Exception as e:
            return f"Error adding student: {e}", 500
    return render_template("form.html", student=None)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    try:
        _ensure_tables()
        conn = _get_db()
        cur = conn.cursor()
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            course = request.form.get("course")
            cur.execute(
                "UPDATE students SET name=%s, email=%s, course=%s WHERE id=%s",
                (name, email, course, id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("index"))
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        cur.close()
        conn.close()
        if not student:
            return "Student not found", 404
        return render_template("form.html", student=student)
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_student(id):
    try:
        _ensure_tables()
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    username = session.get("username")
    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            try:
                _ensure_tables()
                conn = _get_db()
                cur = conn.cursor()
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()

                if not row or not check_password_hash(row[0], current_pw):
                    error = "Current password is incorrect."
                elif len(new_pw) < 6:
                    error = "New password must be at least 6 characters."
                elif new_pw != confirm_pw:
                    error = "New passwords do not match."
                else:
                    cur.execute(
                        "UPDATE users SET password_hash = %s WHERE username = %s",
                        (generate_password_hash(new_pw), username)
                    )
                    conn.commit()
                    success = "Password changed successfully!"

                cur.close()
                conn.close()
            except Exception as e:
                error = f"Database error: {e}"

        elif action == "change_username":
            new_username = request.form.get("new_username", "").strip()
            current_pw = request.form.get("current_password_u", "")

            if len(new_username) < 3:
                error = "Username must be at least 3 characters."
            else:
                try:
                    _ensure_tables()
                    conn = _get_db()
                    cur = conn.cursor()
                    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                    row = cur.fetchone()

                    if not row or not check_password_hash(row[0], current_pw):
                        error = "Current password is incorrect."
                    else:
                        cur.execute("SELECT id FROM users WHERE username = %s", (new_username,))
                        if cur.fetchone():
                            error = "That username is already taken."
                        else:
                            cur.execute(
                                "UPDATE users SET username = %s WHERE username = %s",
                                (new_username, username)
                            )
                            conn.commit()
                            session["username"] = new_username
                            username = new_username
                            success = "Username changed successfully!"

                    cur.close()
                    conn.close()
                except Exception as e:
                    error = f"Database error: {e}"

    # Fetch total student count for display
    total_students = 0
    try:
        _ensure_tables()
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception:
        total_users = 0

    return render_template(
        "settings.html",
        username=session.get("username"),
        error=error,
        success=success,
        total_students=total_students,
        total_users=total_users
    )


# ----------- Local dev entry -----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
