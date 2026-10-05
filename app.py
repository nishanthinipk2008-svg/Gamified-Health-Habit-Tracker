from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, date
import os

# ========================================
# FLASK APP
# ========================================

app = Flask(__name__)
CORS(app)


# ========================================
# PATH CONFIGURATION
# ========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)

DATABASE = os.path.join(
    DATABASE_DIR,
    "habit_tracker.db"
)

FRONTEND_FOLDER = os.path.join(
    BASE_DIR,
    "frontend"
)


# ========================================
# DATABASE CONNECTION
# ========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ========================================
# DATABASE INITIALIZATION
# ========================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Habits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            target INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 10,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Habit completions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
    """)

    # Progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            total_xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak INTEGER DEFAULT 0,
            last_active TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Achievements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize database when Flask starts
init_db()


# ========================================
# FRONTEND ROUTES
# ========================================

@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


@app.route("/index.html")
def index_page():
    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


@app.route("/habits.html")
def habits_page():
    return send_from_directory(
        FRONTEND_FOLDER,
        "habits.html"
    )


@app.route("/dashboard.html")
def dashboard_page():
    return send_from_directory(
        FRONTEND_FOLDER,
        "dashboard.html"
    )


@app.route("/achievements.html")
def achievements_page():
    return send_from_directory(
        FRONTEND_FOLDER,
        "achievements.html"
    )


# ========================================
# API TEST
# ========================================

@app.route("/api/test", methods=["GET"])
def test():

    return jsonify({
        "message": "Gamified Health Habit Tracker Backend Running Successfully!",
        "status": "success"
    })


# ========================================
# CREATE USER
# ========================================

@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({
            "error": "Name and email are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (name, email)
            VALUES (?, ?)
        """, (name, email))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO progress (
                user_id,
                total_xp,
                level,
                streak
            )
            VALUES (?, 0, 1, 0)
        """, (user_id,))

        conn.commit()

        return jsonify({
            "message": "User created successfully",
            "user_id": user_id,
            "name": name,
            "email": email
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Email already exists"
        }), 400

    finally:

        conn.close()


# ========================================
# GET USER
# ========================================

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    if not user:

        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(dict(user))


# ========================================
# ADD HABIT
# ========================================

@app.route("/api/habits", methods=["POST"])
def add_habit():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    user_id = data.get("user_id")
    name = data.get("name")
    category = data.get("category", "General")
    target = data.get("target", 1)
    xp = data.get("xp", 10)

    if not user_id or not name:

        return jsonify({
            "error": "user_id and name are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check user
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if not user:

        conn.close()

        return jsonify({
            "error": "User not found"
        }), 404

    cursor.execute("""
        INSERT INTO habits (
            user_id,
            name,
            category,
            target,
            xp
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        category,
        target,
        xp
    ))

    habit_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Habit added successfully",
        "habit_id": habit_id
    }), 201


# ========================================
# GET USER HABITS
# ========================================

@app.route("/api/habits/<int:user_id>", methods=["GET"])
def get_habits(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM habits
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    habits = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(habit)
        for habit in habits
    ])


# ========================================
# COMPLETE HABIT
# ========================================

@app.route("/api/habits/<int:habit_id>/complete", methods=["POST"])
def complete_habit(habit_id):

    conn = get_db()
    cursor = conn.cursor()

    # Get habit
    cursor.execute("""
        SELECT *
        FROM habits
        WHERE id = ?
    """, (habit_id,))

    habit = cursor.fetchone()

    if not habit:

        conn.close()

        return jsonify({
            "error": "Habit not found"
        }), 404

    user_id = habit["user_id"]
    xp = habit["xp"]

    # Add completion
    cursor.execute("""
        INSERT INTO habit_completions (
            habit_id
        )
        VALUES (?)
    """, (habit_id,))

    # Get current progress
    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    if not progress:

        cursor.execute("""
            INSERT INTO progress (
                user_id,
                total_xp,
                level,
                streak,
                last_active
            )
            VALUES (?, ?, 1, 0, ?)
        """, (
            user_id,
            xp,
            date.today().isoformat()
        ))

        total_xp = xp
        level = 1
        streak = 0

    else:

        total_xp = progress["total_xp"] + xp

        # Level calculation
        level = (total_xp // 100) + 1

        streak = progress["streak"]

        last_active = progress["last_active"]

        today = date.today().isoformat()

        if last_active != today:

            if last_active:

                try:

                    last_date = date.fromisoformat(
                        last_active
                    )

                    difference = (
                        date.today() - last_date
                    ).days

                    if difference == 1:
                        streak += 1

                    elif difference > 1:
                        streak = 1

                except ValueError:

                    streak = 1

            else:

                streak = 1

        cursor.execute("""
            UPDATE progress
            SET
                total_xp = ?,
                level = ?,
                streak = ?,
                last_active = ?
            WHERE user_id = ?
        """, (
            total_xp,
            level,
            streak,
            today,
            user_id
        ))

    conn.commit()

    # ========================================
    # FIRST STEP ACHIEVEMENT
    # ========================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM habit_completions hc
        JOIN habits h
        ON hc.habit_id = h.id
        WHERE h.user_id = ?
    """, (user_id,))

    completion_count = cursor.fetchone()[0]

    if completion_count == 1:

        cursor.execute("""
            SELECT id
            FROM achievements
            WHERE user_id = ?
            AND title = ?
        """, (
            user_id,
            "First Step"
        ))

        existing = cursor.fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO achievements (
                    user_id,
                    title,
                    description
                )
                VALUES (?, ?, ?)
            """, (
                user_id,
                "First Step",
                "Completed your first habit!"
            ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Habit completed successfully",
        "habit_id": habit_id,
        "xp_earned": xp,
        "total_xp": total_xp,
        "level": level,
        "streak": streak
    })


# ========================================
# DASHBOARD
# ========================================

@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):

    conn = get_db()
    cursor = conn.cursor()

    # Check user
    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if not user:

        conn.close()

        return jsonify({
            "error": "User not found"
        }), 404

    # Progress
    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    if not progress:

        cursor.execute("""
            INSERT INTO progress (
                user_id,
                total_xp,
                level,
                streak
            )
            VALUES (?, 0, 1, 0)
        """, (user_id,))

        conn.commit()

        cursor.execute("""
            SELECT *
            FROM progress
            WHERE user_id = ?
        """, (user_id,))

        progress = cursor.fetchone()

    # Total habits
    cursor.execute("""
        SELECT COUNT(*)
        FROM habits
        WHERE user_id = ?
    """, (user_id,))

    total_habits = cursor.fetchone()[0]

    # Completed today
    today = date.today().isoformat()

    cursor.execute("""
        SELECT COUNT(*)
        FROM habit_completions hc
        JOIN habits h
        ON hc.habit_id = h.id
        WHERE h.user_id = ?
        AND DATE(hc.completed_at) = ?
    """, (
        user_id,
        today
    ))

    completed_today = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "user_id": user_id,
        "name": user["name"],
        "total_habits": total_habits,
        "completed_today": completed_today,
        "total_xp": progress["total_xp"],
        "level": progress["level"],
        "streak": progress["streak"],
        "last_active": progress["last_active"]
    })


# ========================================
# GET ACHIEVEMENTS
# ========================================

@app.route("/api/achievements/<int:user_id>", methods=["GET"])
def get_achievements(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM achievements
        WHERE user_id = ?
        ORDER BY earned_at DESC
    """, (user_id,))

    achievements = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(achievement)
        for achievement in achievements
    ])


# ========================================
# ADD ACHIEVEMENT
# ========================================

@app.route("/api/achievements", methods=["POST"])
def add_achievement():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "No data provided"
        }), 400

    user_id = data.get("user_id")
    title = data.get("title")
    description = data.get(
        "description",
        ""
    )

    if not user_id or not title:

        return jsonify({
            "error": "user_id and title are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievements (
            user_id,
            title,
            description
        )
        VALUES (?, ?, ?)
    """, (
        user_id,
        title,
        description
    ))

    achievement_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Achievement added successfully",
        "achievement_id": achievement_id
    }), 201


# ========================================
# RUN APP
# ========================================

if __name__ == "__main__":

    print(
        "Gamified Health Habit Tracker Backend Running Successfully!"
    )

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
