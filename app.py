from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import date
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_FOLDER = BASE_DIR
DATABASE = os.path.join(BASE_DIR, "habit_tracker.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            target INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 10,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
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
            description TEXT,
            earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/index.html")
def index_html():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/home.html")
def home_html():
    return send_from_directory(FRONTEND_FOLDER, "home.html")


@app.route("/habits.html")
def habits_html():
    return send_from_directory(FRONTEND_FOLDER, "habits.html")


@app.route("/dashboard.html")
def dashboard_html():
    return send_from_directory(FRONTEND_FOLDER, "dashboard.html")


@app.route("/achievements.html")
def achievements_html():
    return send_from_directory(FRONTEND_FOLDER, "achievements.html")


@app.route("/style.css")
def style_css():
    return send_from_directory(FRONTEND_FOLDER, "style.css")


@app.route("/script.js")
def script_js():
    return send_from_directory(FRONTEND_FOLDER, "script.js")


@app.route("/api/test", methods=["GET"])
def api_test():
    return jsonify({
        "message": "Gamified Health Habit Tracker Backend Running Successfully!",
        "status": "success"
    })


@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json(silent=True)

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

    if user is None:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(dict(user))


@app.route("/api/habits", methods=["POST"])
def add_habit():

    data = request.get_json(silent=True)

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

    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:
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


@app.route("/api/habits/<int:habit_id>/complete", methods=["POST"])
def complete_habit(habit_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM habits
        WHERE id = ?
    """, (habit_id,))

    habit = cursor.fetchone()

    if habit is None:
        conn.close()

        return jsonify({
            "error": "Habit not found"
        }), 404

    user_id = habit["user_id"]
    xp = habit["xp"]

    cursor.execute("""
        INSERT INTO habit_completions (habit_id)
        VALUES (?)
    """, (habit_id,))

    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    today = date.today().isoformat()

    if progress is None:

        total_xp = xp
        level = (total_xp // 100) + 1
        streak = 1

        cursor.execute("""
            INSERT INTO progress (
                user_id,
                total_xp,
                level,
                streak,
                last_active
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            total_xp,
            level,
            streak,
            today
        ))

    else:

        total_xp = progress["total_xp"] + xp
        level = (total_xp // 100) + 1
        streak = progress["streak"]
        last_active = progress["last_active"]

        if last_active != today:

            if last_active:

                try:
                    last_date = date.fromisoformat(last_active)
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

    cursor.execute("""
        SELECT COUNT(*)
        FROM habit_completions hc
        INNER JOIN habits h
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

        achievement = cursor.fetchone()

        if achievement is None:

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


@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:
        conn.close()

        return jsonify({
            "error": "User not found"
        }), 404

    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    if progress is None:

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

    cursor.execute("""
        SELECT COUNT(*)
        FROM habits
        WHERE user_id = ?
    """, (user_id,))

    total_habits = cursor.fetchone()[0]

    today = date.today().isoformat()

    cursor.execute("""
        SELECT COUNT(*)
        FROM habit_completions hc
        INNER JOIN habits h
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


@app.route("/api/achievements", methods=["POST"])
def add_achievement():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    user_id = data.get("user_id")
    title = data.get("title")
    description = data.get("description", "")

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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
