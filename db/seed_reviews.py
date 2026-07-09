"""
Seeds realistic reviews for NGOs so the directory/detail pages don't look
empty. Safe to re-run: it creates a small pool of demo donor accounts (or
reuses them if they already exist) and only adds a review from a given
donor for a given NGO if one doesn't already exist.

Run after seeding NGOs: python -m db.seed_reviews
"""

import random
import bcrypt
from db.connection import get_connection

DEMO_DONORS = [
    ("Ayesha Raza", "ayesha.raza@example.com"),
    ("Bilal Ahmed", "bilal.ahmed@example.com"),
    ("Sana Tariq", "sana.tariq@example.com"),
    ("Hamza Khan", "hamza.khan@example.com"),
    ("Fatima Noor", "fatima.noor@example.com"),
    ("Usman Malik", "usman.malik@example.com"),
    ("Zainab Sheikh", "zainab.sheikh@example.com"),
    ("Ali Hassan", "ali.hassan@example.com"),
]
DEMO_PASSWORD = "Donor@123"

POSITIVE_COMMENTS = [
    "Volunteered here last month — the team is genuinely organized and transparent about where funds go.",
    "Donated for the first time and got a clear update on how it was used. Will donate again.",
    "Their field team reached our village within days of the flood. Real impact, not just talk.",
    "Been following their work for two years now. Consistent, credible, and community-first.",
    "Clean process, responsive staff, and you can actually see the outcomes on the ground.",
    "One of the few NGOs here that publishes real numbers instead of vague promises.",
    "My cousin works with them as a volunteer — says the leadership is hands-on and honest.",
    "Reached out with a question and got a same-day reply. Rare for an NGO this size.",
    "Supported their winter drive — photos and updates made it easy to trust where the money went.",
    "Small team but they punch way above their weight. Impressed by the reach in rural areas.",
]
MIXED_COMMENTS = [
    "Good intentions and solid ground work, though communication could be a bit faster.",
    "Doing important work — wish they had a simpler way to track donation usage online.",
    "Decent experience overall. The website could use more regular updates on ongoing projects.",
]

RATING_POOL = [5, 5, 5, 4, 4, 4, 3]  # skewed positive but not all 5s


def _get_or_create_donors(cursor, conn):
    donor_ids = []
    for name, email in DEMO_DONORS:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        if row:
            donor_ids.append(row[0])
            continue
        password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'donor')",
            (name, email, password_hash.decode("utf-8")),
        )
        donor_ids.append(cursor.lastrowid)
    conn.commit()
    return donor_ids


def seed_reviews(min_reviews=2, max_reviews=5):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        donor_ids = _get_or_create_donors(cursor, conn)

        cursor.execute("SELECT ngo_id FROM ngos")
        ngo_ids = [row[0] for row in cursor.fetchall()]

        added = 0
        for ngo_id in ngo_ids:
            n_reviews = random.randint(min_reviews, max_reviews)
            reviewers = random.sample(donor_ids, min(n_reviews, len(donor_ids)))

            for donor_id in reviewers:
                cursor.execute(
                    "SELECT review_id FROM reviews WHERE user_id = %s AND ngo_id = %s",
                    (donor_id, ngo_id),
                )
                if cursor.fetchone():
                    continue  # already reviewed, don't duplicate on re-run

                rating = random.choice(RATING_POOL)
                comment = random.choice(POSITIVE_COMMENTS if rating >= 4 else MIXED_COMMENTS)
                cursor.execute(
                    "INSERT INTO reviews (user_id, ngo_id, rating, comment) VALUES (%s, %s, %s, %s)",
                    (donor_id, ngo_id, rating, comment),
                )
                added += 1

        conn.commit()
        print(f"Seeded {added} reviews across {len(ngo_ids)} NGOs using {len(donor_ids)} demo donors.")
        print(f"Demo donor login password (any of the emails above): {DEMO_PASSWORD}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_reviews()
