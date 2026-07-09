import bcrypt
from db.connection import get_connection


class User:
    """
    Represents a platform user (donor, ngo_admin, or admin).
    Encapsulates all DB operations related to users behind simple methods,
    so routes/ files never write raw SQL directly.
    """

    def __init__(self, user_id=None, name=None, email=None, role="donor"):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role

    # ---------- Static "repository-style" methods ----------

    @staticmethod
    def register(name, email, password, role="donor"):
        """Creates a new user with a bcrypt-hashed password. Returns new user_id."""
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (name, email, password_hash.decode("utf-8"), role)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def login(email, password):
        """
        Verifies email + password against the DB.
        Returns a User object on success, or None on failure.
        """
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if row is None:
            return None

        stored_hash = row["password_hash"].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return User(user_id=row["user_id"], name=row["name"], email=row["email"], role=row["role"])
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if row is None:
            return None
        return User(user_id=row["user_id"], name=row["name"], email=row["email"], role=row["role"])

    def to_dict(self):
        return {"user_id": self.user_id, "name": self.name, "email": self.email, "role": self.role}
