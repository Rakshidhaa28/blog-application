from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
from urllib.parse import urlparse, parse_qs

from database import get_db, init_db, hash_password


# ==========================================
# SERVER SETTINGS
# ==========================================

HOST = "0.0.0.0"
PORT = 8000

# Stores login sessions
sessions = {}


# ==========================================
# BLOG SERVER
# ==========================================

class BlogServer(BaseHTTPRequestHandler):

    # --------------------------------------
    # Send JSON Response
    # --------------------------------------

    def send_json(self, data, status=200):

        response = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()

        self.wfile.write(response)


    # --------------------------------------
    # Read JSON Request
    # --------------------------------------

    def read_json(self):

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(length)

            return json.loads(
                body.decode("utf-8")
            )

        except Exception:

            return {}


    # --------------------------------------
    # Get Logged-in User
    # --------------------------------------

    def get_user(self):

        auth = self.headers.get(
            "Authorization",
            ""
        )

        if not auth.startswith("Bearer "):

            return None

        token = auth.replace(
            "Bearer ",
            "",
            1
        ).strip()

        return sessions.get(token)


    # --------------------------------------
    # Serve HTML / CSS / JS
    # --------------------------------------

    def serve_file(self, filepath, content_type):

        if not os.path.exists(filepath):

            self.send_error(
                404,
                "File not found"
            )

            return

        try:

            with open(
                filepath,
                "rb"
            ) as file:

                content = file.read()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                content_type
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()

            self.wfile.write(content)

        except Exception as e:

            self.send_error(
                500,
                str(e)
            )


    # ======================================
    # GET REQUESTS
    # ======================================

    def do_GET(self):

        parsed = urlparse(self.path)

        path = parsed.path

        # ----------------------------------
        # HTML Pages
        # ----------------------------------

        pages = {

            "/":
                "templates/index.html",

            "/index.html":
                "templates/index.html",

            "/login.html":
                "templates/login.html",

            "/register.html":
                "templates/register.html",

            "/create.html":
                "templates/create.html",

            "/post.html":
                "templates/post.html",

            "/edit.html":
                "templates/edit.html"
        }

        if path in pages:

            self.serve_file(
                pages[path],
                "text/html; charset=utf-8"
            )

            return


        # ----------------------------------
        # Static Files
        # ----------------------------------

        if path.startswith("/static/"):

            filepath = path.lstrip("/")

            if filepath.endswith(".css"):

                content_type = "text/css"

            elif filepath.endswith(".js"):

                content_type = "application/javascript"

            elif filepath.endswith(".png"):

                content_type = "image/png"

            elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):

                content_type = "image/jpeg"

            else:

                content_type = "application/octet-stream"

            self.serve_file(
                filepath,
                content_type
            )

            return


        # ==================================
        # API - GET POSTS
        # ==================================

        if path == "/api/posts":

            conn = get_db()

            posts = conn.execute(
                """
                SELECT
                    posts.id,
                    posts.title,
                    posts.content,
                    posts.created_at,
                    users.username
                FROM posts
                JOIN users
                ON posts.user_id = users.id
                ORDER BY posts.id DESC
                """
            ).fetchall()

            conn.close()

            result = []

            for post in posts:

                result.append({
                    "id": post["id"],
                    "title": post["title"],
                    "content": post["content"],
                    "created_at": post["created_at"],
                    "username": post["username"]
                })

            self.send_json(result)

            return


        # ==================================
        # API - SINGLE POST
        # ==================================

        if path.startswith("/api/posts/"):

            try:

                post_id = int(
                    path.split("/")[-1]
                )

            except ValueError:

                self.send_json(
                    {"error": "Invalid post ID"},
                    400
                )

                return


            conn = get_db()

            post = conn.execute(
                """
                SELECT
                    posts.id,
                    posts.title,
                    posts.content,
                    posts.created_at,
                    posts.user_id,
                    users.username
                FROM posts
                JOIN users
                ON posts.user_id = users.id
                WHERE posts.id = ?
                """,
                (post_id,)
            ).fetchone()


            if not post:

                conn.close()

                self.send_json(
                    {"error": "Post not found"},
                    404
                )

                return


            comments = conn.execute(
                """
                SELECT
                    comments.id,
                    comments.content,
                    comments.created_at,
                    users.username
                FROM comments
                JOIN users
                ON comments.user_id = users.id
                WHERE comments.post_id = ?
                ORDER BY comments.id ASC
                """,
                (post_id,)
            ).fetchall()


            conn.close()


            comment_list = []

            for comment in comments:

                comment_list.append({

                    "id": comment["id"],

                    "content":
                        comment["content"],

                    "created_at":
                        comment["created_at"],

                    "username":
                        comment["username"]
                })


            result = {

                "id":
                    post["id"],

                "title":
                    post["title"],

                "content":
                    post["content"],

                "created_at":
                    post["created_at"],

                "user_id":
                    post["user_id"],

                "username":
                    post["username"],

                "comments":
                    comment_list
            }


            self.send_json(result)

            return


        # ==================================
        # API - CURRENT USER
        # ==================================

        if path == "/api/me":

            user_id = self.get_user()

            if not user_id:

                self.send_json({
                    "logged_in": False
                })

                return


            conn = get_db()

            user = conn.execute(
                """
                SELECT id, username
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            ).fetchone()

            conn.close()


            if not user:

                self.send_json({
                    "logged_in": False
                })

                return


            self.send_json({

                "logged_in": True,

                "id":
                    user["id"],

                "username":
                    user["username"]
            })

            return


        # ----------------------------------
        # Unknown GET
        # ----------------------------------

        self.send_error(
            404,
            "Page not found"
        )


    # ======================================
    # POST REQUESTS
    # ======================================

    def do_POST(self):

        parsed = urlparse(self.path)

        path = parsed.path

        data = self.read_json()


        # ==================================
        # REGISTER
        # ==================================

        if path == "/api/register":

            username = str(
                data.get("username", "")
            ).strip()

            password = str(
                data.get("password", "")
            )


            if not username or not password:

                self.send_json({

                    "error":
                        "Username and password are required"

                }, 400)

                return


            if len(username) < 3:

                self.send_json({

                    "error":
                        "Username must contain at least 3 characters"

                }, 400)

                return


            if len(password) < 4:

                self.send_json({

                    "error":
                        "Password must contain at least 4 characters"

                }, 400)

                return


            conn = get_db()


            existing = conn.execute(
                """
                SELECT id
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()


            if existing:

                conn.close()

                self.send_json({

                    "error":
                        "Username already exists"

                }, 409)

                return


            password_hash = hash_password(
                password
            )


            cursor = conn.execute(
                """
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
                """,
                (
                    username,
                    password_hash
                )
            )


            user_id = cursor.lastrowid

            conn.commit()

            conn.close()


            self.send_json({

                "message":
                    "Registration successful",

                "user_id":
                    user_id

            }, 201)

            return


        # ==================================
        # LOGIN
        # ==================================

        if path == "/api/login":

            username = str(
                data.get("username", "")
            ).strip()

            password = str(
                data.get("password", "")
            )


            if not username or not password:

                self.send_json({

                    "error":
                        "Username and password are required"

                }, 400)

                return


            conn = get_db()


            user = conn.execute(
                """
                SELECT id, username, password
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()


            conn.close()


            if not user:

                self.send_json({

                    "error":
                        "Invalid username or password"

                }, 401)

                return


            password_hash = hash_password(
                password
            )


            if password_hash != user["password"]:

                self.send_json({

                    "error":
                        "Invalid username or password"

                }, 401)

                return


            token = secrets.token_hex(32)


            sessions[token] = user["id"]


            self.send_json({

                "message":
                    "Login successful",

                "token":
                    token,

                "user": {

                    "id":
                        user["id"],

                    "username":
                        user["username"]

                }

            })

            return


        # ==================================
        # LOGOUT
        # ==================================

        if path == "/api/logout":

            auth = self.headers.get(
                "Authorization",
                ""
            )


            if auth.startswith("Bearer "):

                token = auth.replace(
                    "Bearer ",
                    "",
                    1
                ).strip()

                sessions.pop(
                    token,
                    None
                )


            self.send_json({

                "message":
                    "Logout successful"

            })

            return


        # ==================================
        # CREATE POST
        # ==================================

        if path == "/api/posts":

            user_id = self.get_user()


            if not user_id:

                self.send_json({

                    "error":
                        "Please login first"

                }, 401)

                return


            title = str(
                data.get("title", "")
            ).strip()

            content = str(
                data.get("content", "")
            ).strip()


            if not title or not content:

                self.send_json({

                    "error":
                        "Title and content are required"

                }, 400)

                return


            conn = get_db()


            cursor = conn.execute(
                """
                INSERT INTO posts
                (user_id, title, content)
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    title,
                    content
                )
            )


            post_id = cursor.lastrowid


            conn.commit()

            conn.close()


            self.send_json({

                "message":
                    "Post created successfully",

                "post_id":
                    post_id

            }, 201)

            return


        # ==================================
        # ADD COMMENT
        # ==================================

        if path.startswith("/api/posts/") and path.endswith("/comments"):

            try:

                parts = path.split("/")

                post_id = int(parts[3])

            except Exception:

                self.send_json({

                    "error":
                        "Invalid post ID"

                }, 400)

                return


            user_id = self.get_user()


            if not user_id:

                self.send_json({

                    "error":
                        "Please login first"

                }, 401)

                return


            content = str(
                data.get("content", "")
            ).strip()


            if not content:

                self.send_json({

                    "error":
                        "Comment cannot be empty"

                }, 400)

                return


            conn = get_db()


            post = conn.execute(
                """
                SELECT id
                FROM posts
                WHERE id = ?
                """,
                (post_id,)
            ).fetchone()


            if not post:

                conn.close()

                self.send_json({

                    "error":
                        "Post not found"

                }, 404)

                return


            conn.execute(
                """
                INSERT INTO comments
                (post_id, user_id, content)
                VALUES (?, ?, ?)
                """,
                (
                    post_id,
                    user_id,
                    content
                )
            )


            conn.commit()

            conn.close()


            self.send_json({

                "message":
                    "Comment added successfully"

            }, 201)

            return


        # ----------------------------------
        # Unknown POST
        # ----------------------------------

        self.send_error(
            404,
            "API not found"
        )


    # ======================================
    # PUT REQUEST
    # ======================================

    def do_PUT(self):

        parsed = urlparse(self.path)

        path = parsed.path


        if not path.startswith("/api/posts/"):

            self.send_error(
                404,
                "API not found"
            )

            return


        try:

            post_id = int(
                path.split("/")[-1]
            )

        except ValueError:

            self.send_json({

                "error":
                    "Invalid post ID"

            }, 400)

            return


        user_id = self.get_user()


        if not user_id:

            self.send_json({

                "error":
                    "Please login first"

            }, 401)

            return


        data = self.read_json()


        title = str(
            data.get("title", "")
        ).strip()

        content = str(
            data.get("content", "")
        ).strip()


        if not title or not content:

            self.send_json({

                "error":
                    "Title and content are required"

            }, 400)

            return


        conn = get_db()


        post = conn.execute(
            """
            SELECT id
            FROM posts
            WHERE id = ?
            AND user_id = ?
            """,
            (
                post_id,
                user_id
            )
        ).fetchone()


        if not post:

            conn.close()

            self.send_json({

                "error":
                    "Post not found or you are not the owner"

            }, 404)

            return


        conn.execute(
            """
            UPDATE posts
            SET title = ?, content = ?
            WHERE id = ?
            """,
            (
                title,
                content,
                post_id
            )
        )


        conn.commit()

        conn.close()


        self.send_json({

            "message":
                "Post updated successfully"

        })
def do_DELETE(self):

        parsed = urlparse(self.path)

        path = parsed.path


        if not path.startswith("/api/posts/"):

            self.send_error(
                404,
                "API not found"
            )

            return


        try:

            post_id = int(
                path.split("/")[-1]
            )

        except ValueError:

            self.send_json({

                "error":
                    "Invalid post ID"

            }, 400)

            return


        user_id = self.get_user()


        if not user_id:

            self.send_json({

                "error":
                    "Please login first"

            }, 401)

            return


        conn = get_db()


        post = conn.execute(
            """
            SELECT id
            FROM posts
            WHERE id = ?
            AND user_id = ?
            """,
            (
                post_id,
                user_id
            )
        ).fetchone()


        if not post:

            conn.close()

            self.send_json({

                "error":
                    "Post not found or you are not the owner"

            }, 404)

            return


        # Delete comments first
        conn.execute(
            """
            DELETE FROM comments
            WHERE post_id = ?
            """,
            (post_id,)
        )


        # Delete post
        conn.execute(
            """
            DELETE FROM posts
            WHERE id = ?
            """,
            (post_id,)
        )


        conn.commit()

        conn.close()


        self.send_json({

            "message":
                "Post deleted successfully"

        })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    # Create database
    init_db()


    print()
    print("======================================")
    print("       BLOG PLATFORM STARTED")
    print("======================================")
    print("Server running at:")
    print("http://localhost:8000")
    print()
    print("Default Admin Login:")
    print("Username : admin")
    print("Password : admin123")
    print("======================================")
    print()


    server = HTTPServer(
        (HOST, PORT),
        BlogServer
    )


    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print()
        print("Server stopped.")

        server.server_close()