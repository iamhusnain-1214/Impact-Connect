"""
Seeds (or resets) the single default admin account.
Run once after schema.sql: python -m db.seed_admin

This is the ONLY place an admin account gets created. The public
/api/register endpoint always forces role="donor" on purpose (see
the comment in app.py) so nobody can grant themselves admin access
by tampering with a signup request. Admin accounts are only ever
made here, directly against the database, by whoever controls the
server/DB.

Safe to re-run: if the admin email already exists, it just resets
its password and makes sure role='admin' instead of creating a
duplicate row.
"""

import bcrypt
from db.connection import get_connection

# --- Change these before running if you want a different login ---
ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@impactconnect.com"
ADMIN_PASSWORD = "Admin@123"
# --------------------------------------------------------------------


def seed_admin():
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt())

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (ADMIN_EMAIL,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "UPDATE users SET password_hash = %s, role = 'admin', name = %s WHERE email = %s",
                (password_hash.decode("utf-8"), ADMIN_NAME, ADMIN_EMAIL),
            )
            action = "Updated existing"
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
                (ADMIN_NAME, ADMIN_EMAIL, password_hash.decode("utf-8")),
            )
            action = "Created new"

        conn.commit()
        print(f"{action} admin account:")
        print(f"  Email:    {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print("Log in at /login with these — you'll land on /admin.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_admin()
