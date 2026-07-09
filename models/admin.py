from models.user import User
from db.connection import get_connection


class Admin(User):
    """
    Admin IS-A User with extra powers: full authority to add, edit, and delete
    NGOs directly (see NGO.create/update/delete), plus dashboard stats.
    Inherits __init__ and to_dict from User - demonstrates inheritance directly.

    There's no separate NGO self-registration or approval-queue workflow -
    the admin IS the verification authority. An NGO an admin adds is trusted
    (verified) immediately, since it was entered by someone with that authority.
    """

    def __init__(self, user_id=None, name=None, email=None):
        super().__init__(user_id=user_id, name=name, email=email, role="admin")

    @staticmethod
    def get_dashboard_stats():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM ngos")
            total_ngos = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS verified FROM ngos WHERE verified = TRUE")
            verified_ngos = cursor.fetchone()["verified"]

            cursor.execute("SELECT COUNT(*) AS total_categories FROM categories")
            total_categories = cursor.fetchone()["total_categories"]

            cursor.execute("SELECT COUNT(*) AS total_donors FROM users WHERE role = 'donor'")
            total_donors = cursor.fetchone()["total_donors"]

            cursor.execute("SELECT COUNT(*) AS total_reviews FROM reviews")
            total_reviews = cursor.fetchone()["total_reviews"]

            return {
                "total_ngos": total_ngos,
                "verified_ngos": verified_ngos,
                "total_categories": total_categories,
                "total_donors": total_donors,
                "total_reviews": total_reviews,
            }
        finally:
            cursor.close()
            conn.close()
