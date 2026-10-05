from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, date
import os

# ========================================
# FLASK APP
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
    BASE_DIR,
    "../frontend"
)


# ========================================
# DATABASE CONNECTION
# ========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ========================================
# CREATE DATABASE TABLES
# ========================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            target INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 10,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id),
            UNIQUE(habit_id, completed_date)
        )
    """)

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            earned_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ========================================
# FRONTEND PAGES
# ========================================

@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_FOLDER,
        "home.html"
    )


@app.route("/home.html")
def home_page():
    return send_from_directory(
        FRONTEND_FOLDER,
        "home.html"
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

@app.route("/api/test")
def test():

    return jsonify({
        "message": "API is working!",
        "status": "success"
    })


# ========================================
# CREATE USER
# ========================================

@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")

    if not name:

        return jsonify({
            "error": "Name is required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, created_at)
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            datetime.now().isoformat()
        ))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO progress
            (user_id, total_xp, level, streak, last_active)
            VALUES (?, 0, 1, 0, ?)
        """, (
            user_id,
            None
        ))

        conn.commit()

        return jsonify({
            "message": "User created successfully",
            "user_id": user_id,
            "name": name
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
        SELECT
            users.id,
            users.name,
            users.email,
            progress.total_xp,
            progress.level,
            progress.streak,
            progress.last_active
        FROM users
        LEFT JOIN progress
        ON users.id = progress.user_id
        WHERE users.id = ?
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

    data = request.get_json() or {}

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

    cursor.execute("""
        INSERT INTO habits
        (user_id, name, category, target, xp, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        category,
        target,
        xp,
        datetime.now().isoformat()
    ))

    habit_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Habit added successfully",
        "habit_id": habit_id
    }), 201


# ========================================
# GET HABITS
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

    result = []

    for habit in habits:

        habit_data = dict(habit)

        cursor.execute("""
            SELECT completed_date
            FROM habit_completions
            WHERE habit_id = ?
            ORDER BY completed_date DESC
        """, (habit["id"],))

        completions = cursor.fetchall()

        habit_data["completions"] = [
            row["completed_date"]
            for row in completions
        ]

        result.append(habit_data)

    conn.close()

    return jsonify(result)


# ========================================
# COMPLETE HABIT
# ========================================

@app.route("/api/habits/<int:habit_id>/complete", methods=["POST"])
def complete_habit(habit_id):

    conn = get_db()
    cursor = conn.cursor()

    try:

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

        completed_date = date.today().isoformat()

        # Check if already completed today
        cursor.execute("""
            SELECT *
            FROM habit_completions
            WHERE habit_id = ?
            AND completed_date = ?
        """, (
            habit_id,
            completed_date
        ))

        already_completed = cursor.fetchone()

        if already_completed:

            conn.close()

            return jsonify({
                "message": "Habit already completed today"
            }), 400

        # Save completion
        cursor.execute("""
            INSERT INTO habit_completions
            (habit_id, completed_date)
            VALUES (?, ?)
        """, (
            habit_id,
            completed_date
        ))

        # Add XP
        cursor.execute("""
            UPDATE progress
            SET total_xp = total_xp + ?,
                last_active = ?
            WHERE user_id = ?
        """, (
            habit["xp"],
            completed_date,
            habit["user_id"]
        ))

        # Get updated XP
        cursor.execute("""
            SELECT total_xp
            FROM progress
            WHERE user_id = ?
        """, (habit["user_id"],))

        progress = cursor.fetchone()

        if not progress:

            conn.rollback()
            conn.close()

            return jsonify({
                "error": "User progress not found"
            }), 404

        total_xp = progress["total_xp"]

        # Calculate level
        level = (total_xp // 100) + 1

        # Update level
        cursor.execute("""
            UPDATE progress
            SET level = ?
            WHERE user_id = ?
        """, (
            level,
            habit["user_id"]
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "message": "Habit completed!",
            "xp_earned": habit["xp"],
            "total_xp": total_xp,
            "level": level
        }), 200

    except sqlite3.IntegrityError:

        conn.rollback()
        conn.close()

        return jsonify({
            "error": "Habit already completed today"
        }), 400

    except Exception as e:

        conn.rollback()
        conn.close()

        return jsonify({
            "error": str(e)
        }), 500


# ========================================
# DASHBOARD
# ========================================

@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            total_xp,
            level,
            streak,
            last_active
        FROM progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    if not progress:

        conn.close()

        return jsonify({
            "error": "User not found"
        }), 404

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM habits
        WHERE user_id = ?
    """, (user_id,))

    total_habits = cursor.fetchone()["total"]

    today = date.today().isoformat()

    cursor.execute("""
        SELECT COUNT(*) AS completed
        FROM habit_completions hc
        JOIN habits h
        ON hc.habit_id = h.id
        WHERE h.user_id = ?
        AND hc.completed_date = ?
    """, (
        user_id,
        today
    ))

    completed_today = cursor.fetchone()["completed"]

    conn.close()

    return jsonify({
        "total_xp": progress["total_xp"],
        "level": progress["level"],
        "streak": progress["streak"],
        "last_active": progress["last_active"],
        "total_habits": total_habits,
        "completed_today": completed_today
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

    data = request.get_json() or {}

    user_id = data.get("user_id")
    title = data.get("title")
    description = data.get("description")

    if not user_id or not title or not description:

        return jsonify({
            "error": "user_id, title and description are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievements
        (user_id, title, description, earned_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        title,
        description,
        datetime.now().isoformat()
    ))

    achievement_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Achievement unlocked!",
        "achievement_id": achievement_id
    }), 201


# ========================================
# RUN SERVER
# ========================================

if __name__ == "__main__":

    init_db()

    print("\n========================================")
    print(" Gamified Health Habit Tracker Backend")
    print("========================================")
    print(" Server: http://127.0.0.1:5000")
    print(" Database: habit_tracker.db")
    print("========================================\n")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
