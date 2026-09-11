import os
from flask import Flask, render_template, request, redirect, url_for, jsonify

try:
    from app.db import get_db_connection, init_db, ensure_db_initialized
except (ImportError, ModuleNotFoundError):
    from db import get_db_connection, init_db, ensure_db_initialized

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


@app.route("/")
def index():
    students = []
    db_error = None

    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id")
        students = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("Database connection error:", e)
        db_error = str(e)

    return render_template("index.html", students=students, db_error=db_error)


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        course = request.form.get("course")

        try:
            ensure_db_initialized()
            conn = get_db_connection()
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
def edit_student(id):
    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cur = conn.cursor()

        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            course = request.form.get("course")

            cur.execute(
                """
                UPDATE students
                SET name = %s, email = %s, course = %s
                WHERE id = %s
                """,
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
        return f"Error updating student: {e}", 500


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_student(id):
    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM students WHERE id = %s", (id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    try:
        init_db()
    except Exception as err:
        print("Warning: Could not initialize database on startup:", err)
    app.run(host="0.0.0.0", port=5000, debug=True)