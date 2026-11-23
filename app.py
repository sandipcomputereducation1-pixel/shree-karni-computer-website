
import os
import sqlite3
from functools import wraps
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DB = "shree_karni.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )""")
        db.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            details TEXT
        )""")
        db.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            details TEXT
        )""")
        db.execute("""
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL
        )""")

                username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            raise RuntimeError("Admin credentials are missing")

        existing = db.execute(
            "SELECT id FROM admins ORDER BY id LIMIT 1"
        ).fetchone()

        if existing:
            db.execute(
                "UPDATE admins SET username=?, password=? WHERE id=?",
                (username, generate_password_hash(password), existing["id"])
            )
        else:
            db.execute(
                "INSERT INTO admins (username,password) VALUES (?,?)",
                (username, generate_password_hash(password))
            )
            )

init_db()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

LOGIN_HTML = """
<h2>Shree Karni Computer - Admin Login</h2>
<form method="post">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button>Login</button>
</form>
"""

ADMIN_HTML = """
<h1>Shree Karni Computer Admin Panel</h1>
<p>Welcome, {{ session.admin }} |
<a href="/logout">Logout</a></p>

<h2>Add Course</h2>
<form method="post" action="/add-course">
<input name="name" placeholder="Course Name" required>
<input name="details" placeholder="Course Details">
<button>Add Course</button>
</form>

<h2>Courses</h2>
{% for c in courses %}
<p>{{ c.name }} - {{ c.details }}
<a href="/delete-course/{{ c.id }}">Delete</a></p>
{% endfor %}

<hr>
<h2>Add Notice</h2>
<form method="post" action="/add-notice">
<input name="title" placeholder="Notice Title" required>
<input name="details" placeholder="Notice Details">
<button>Add Notice</button>
</form>

<h2>Notices</h2>
{% for n in notices %}
<p>{{ n.title }} - {{ n.details }}
<a href="/delete-notice/{{ n.id }}">Delete</a></p>
{% endfor %}

<hr>
<h2>Gallery Image URL</h2>
<form method="post" action="/add-image">
<input name="image_url" placeholder="Image URL" required>
<button>Add Image</button>
</form>

{% for g in gallery %}
<p><img src="{{ g.image_url }}" width="100">
<a href="/delete-image/{{ g.id }}">Delete</a></p>
{% endfor %}
"""

@app.route("/")
def home():
    return redirect("/admin")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with get_db() as db:
            user = db.execute(
                "SELECT * FROM admins WHERE username=?",
                (request.form["username"],)
            ).fetchone()

        if user and check_password_hash(user["password"], request.form["password"]):
            session["admin"] = user["username"]
            return redirect("/admin")
        return "Invalid username or password"
    return render_template_string(LOGIN_HTML)

@app.route("/admin")
@login_required
def admin():
    with get_db() as db:
        courses = db.execute("SELECT * FROM courses").fetchall()
        notices = db.execute("SELECT * FROM notices").fetchall()
        gallery = db.execute("SELECT * FROM gallery").fetchall()
    return render_template_string(
        ADMIN_HTML, courses=courses, notices=notices, gallery=gallery
    )

@app.route("/add-course", methods=["POST"])
@login_required
def add_course():
    with get_db() as db:
        db.execute("INSERT INTO courses(name,details) VALUES (?,?)",
                   (request.form["name"], request.form["details"]))
    return redirect("/admin")

@app.route("/delete-course/<int:id>")
@login_required
def delete_course(id):
    with get_db() as db:
        db.execute("DELETE FROM courses WHERE id=?", (id,))
    return redirect("/admin")

@app.route("/add-notice", methods=["POST"])
@login_required
def add_notice():
    with get_db() as db:
        db.execute("INSERT INTO notices(title,details) VALUES (?,?)",
                   (request.form["title"], request.form["details"]))
    return redirect("/admin")

@app.route("/delete-notice/<int:id>")
@login_required
def delete_notice(id):
    with get_db() as db:
        db.execute("DELETE FROM notices WHERE id=?", (id,))
    return redirect("/admin")

@app.route("/add-image", methods=["POST"])
@login_required
def add_image():
    with get_db() as db:
        db.execute("INSERT INTO gallery(image_url) VALUES (?)",
                   (request.form["image_url"],))
    return redirect("/admin")

@app.route("/delete-image/<int:id>")
@login_required
def delete_image(id):
    with get_db() as db:
        db.execute("DELETE FROM gallery WHERE id=?", (id,))
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
