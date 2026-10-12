import os
import re
import pymysql
import bcrypt
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash

load_dotenv()

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Copy .env.example to .env")


def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
    )


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_PASSWORD_BYTES = 72  # bcrypt rejects anything longer


def validate_title(title):
    if not title.strip():
        return "Title is required"
    if len(title) > 200:
        return "Title is too long (200 characters at most)"
    return None


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("todos"))
    return redirect(url_for("login"))


# ----------------- REGISTER -----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Name is required")
        elif len(name) > 100:
            errors.append("Name is too long (100 characters at most)")
        if not email:
            errors.append("Email is required")
        elif len(email) > 255:
            errors.append("Email is too long (255 characters at most)")
        elif not EMAIL_RE.match(email):
            errors.append("Email format is invalid")
        if not password:
            errors.append("Password is required")
        elif len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            errors.append("Password is too long (72 bytes at most)")
        if not confirm_password:
            errors.append("Confirm password is required")
        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("register.html", name=name, email=email)

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s);"
                cursor.execute(sql, (email, name, password_hash))
                new_id = cursor.lastrowid
            conn.commit()

            session["user_id"] = new_id
            session["name"] = name
            return redirect(url_for("todos"))
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                flash("Email Already Exists", "error")
            else:
                flash("Database error occurred", "error")
            return render_template("register.html", name=name, email=email)
        finally:
            conn.close()

    return render_template("register.html")


# ----------------- LOGIN -----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("login.html", email=email)

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT user_id, name, password_hash FROM users WHERE email = %s;"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

            if (
                user
                and len(password.encode("utf-8")) <= MAX_PASSWORD_BYTES
                and bcrypt.checkpw(
                    password.encode("utf-8"), user["password_hash"].encode("utf-8")
                )
            ):
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("todos"))
            else:
                flash("Invalid email or password", "error")
                return render_template("login.html", email=email)
        finally:
            conn.close()

    return render_template("login.html")


# ----------------- LOGOUT -----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------- TODOS LIST -----------------
@app.route("/todos", methods=["GET"])
def todos():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC;"
            cursor.execute(sql, (user_id,))
            todo_list = cursor.fetchall()
        return render_template("todos.html", todos=todo_list, name=session.get("name"))
    finally:
        conn.close()


# ----------------- ADD TODO -----------------
@app.route("/todos/add", methods=["POST"])
def add_todo():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    error = validate_title(title)
    if error:
        flash(error, "error")
        return redirect(url_for("todos"))

    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO todos (user_id, title) VALUES (%s, %s);"
            cursor.execute(sql, (user_id, title))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("todos"))


# ----------------- EDIT TODO -----------------
@app.route("/todos/edit/<int:todo_id>", methods=["POST"])
def edit_todo(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    error = validate_title(title)
    if error:
        flash(error, "error")
        return redirect(url_for("todos"))

    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s;"
            cursor.execute(sql, (title, todo_id, user_id))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("todos"))


# ----------------- TOGGLE DONE -----------------
@app.route("/todos/toggle/<int:todo_id>", methods=["POST"])
def toggle_todo(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    is_done = 1 if request.form.get("is_done") == "1" else 0
    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s;"
            cursor.execute(sql, (is_done, todo_id, user_id))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("todos"))


# ----------------- DELETE TODO -----------------
@app.route("/todos/delete/<int:todo_id>", methods=["POST"])
def delete_todo(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM todos WHERE todo_id = %s AND user_id = %s;"
            cursor.execute(sql, (todo_id, user_id))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("todos"))


# ----------------- ERRORS -----------------
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    return render_template("error.html"), getattr(e, "code", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
