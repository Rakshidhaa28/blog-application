import sqlite3
import hashlib

DB_NAME = "blog.db"


# -----------------------------
# Database Connection
# -----------------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# -----------------------------
# Initialize Database
# -----------------------------
def init_db():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Posts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Comments table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # --------------------------------
    # Create default admin account
    # --------------------------------
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:

        cursor = conn.execute(
            """
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """,
            (
                "admin",
                hash_password("admin123")
            )
        )

        admin_id = cursor.lastrowid

        # Sample Post 1
        conn.execute(
            """
            INSERT INTO posts
            (user_id, title, content)
            VALUES (?, ?, ?)
            """,
            (
                admin_id,
                "Welcome to BlogSpace",
                "Welcome to our Blog Platform! "
                "This is your first sample post."
            )
        )

        # Sample Post 2
        conn.execute(
            """
            INSERT INTO posts
            (user_id, title, content)
            VALUES (?, ?, ?)
            """,
            (
                admin_id,
                "Learning Python",
                "Python is beginner friendly and useful "
                "for web development, AI and automation."
            )
        )

        # Sample Post 3
        conn.execute(
            """
            INSERT INTO posts
            (user_id, title, content)
            VALUES (?, ?, ?)
            """,
            (
                admin_id,
                "My Web Development Journey",
                "Start small, practice every day and "
                "build projects to improve your skills."
            )
        )

    conn.commit()
    conn.close()