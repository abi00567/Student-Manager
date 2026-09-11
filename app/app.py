from flask import Flask, render_template, request, redirect, url_for, jsonify
from app.db import get_db_connection, init_db

app = Flask(__name__)


@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY id")
    students = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", students=students)


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]

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

    return render_template("form.html", student=None)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]

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

    return render_template("form.html", student=student)


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM students WHERE id = %s", (id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)