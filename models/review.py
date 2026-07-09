from db.connection import get_connection


class Review:
    def __init__(self, review_id=None, user_id=None, ngo_id=None, rating=None, comment=None):
        self.review_id = review_id
        self.user_id = user_id
        self.ngo_id = ngo_id
        self.rating = rating
        self.comment = comment

    @staticmethod
    def add_review(user_id, ngo_id, rating, comment):
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO reviews (user_id, ngo_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (user_id, ngo_id, rating, comment)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_for_ngo(ngo_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT r.*, u.name AS reviewer_name
                   FROM reviews r JOIN users u ON r.user_id = u.user_id
                   WHERE r.ngo_id = %s ORDER BY r.created_at DESC""",
                (ngo_id,)
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_average_rating(ngo_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT AVG(rating) FROM reviews WHERE ngo_id = %s", (ngo_id,))
            avg = cursor.fetchone()[0]
            return round(float(avg), 1) if avg else None
        finally:
            cursor.close()
            conn.close()
