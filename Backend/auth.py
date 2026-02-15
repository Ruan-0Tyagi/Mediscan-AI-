from flask import Blueprint, request, jsonify, session
import sqlite3
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

auth_blueprint = Blueprint("auth", __name__)

# Admin email config
ADMIN_EMAIL = "deaftyagi23@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "deaftyagi23@gmail.com"
SMTP_PASS = "yfyw hcxl cmwy jbth"

# Database setup
def get_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            approved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

# Send email
def send_mail(subject, body):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# Signup API
@auth_blueprint.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data["email"]
    password = generate_password_hash(data["password"])

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already registered"})

    approval_link = f"http://127.0.0.1:5000/approve/{email}"

    send_mail(
        "New MediScan AI Signup Request",
        f"User {email} has requested access.\n\nApprove account: {approval_link}"
    )

    conn.close()
    return jsonify({"message": "Signup successful. Await admin approval."})

# Admin approval API
@auth_blueprint.route("/approve/<email>", methods=["GET"])
def approve_user(email):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved=1 WHERE email=?", (email,))
    conn.commit()
    conn.close()
    return "User approved successfully. They can now login."

# Login API
@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password, approved FROM users WHERE email=?", (email,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "User not found"})

    if not check_password_hash(row[0], password):
        conn.close()
        return jsonify({"error": "Invalid password"})

    if row[1] == 0:
        conn.close()
        return jsonify({"error": "Admin approval pending"})

    send_mail(
        "MediScan AI Login Alert",
        f"User {email} has logged into MediScan AI."
    )

    conn.close()
    session["user"] = email

    return jsonify({"message": "Login successful"})

# Set session
@auth_blueprint.route("/set_session", methods=["POST"])
def set_session():
    data = request.json
    session["user_email"] = data["email"]
    return jsonify({"status": "session set"})

# Check session
@auth_blueprint.route("/check_session", methods=["GET"])
def check_session():
    if "user_email" in session:
        return jsonify({"logged_in": True, "email": session["user_email"]})
    return jsonify({"logged_in": False})

# Logout
@auth_blueprint.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return jsonify({"status": "logged out"})

# Profile API
@auth_blueprint.route("/profile", methods=["GET"])
def profile():
    if "user_email" not in session:
        return jsonify({"error": "Not logged in"}), 401

    return jsonify({
        "email": session["user_email"],
        "total_reports": 0
    })
