from db.connection import get_connection


class NGO:
    """
    Represents an NGO profile. Handles create/update/delete, category tagging,
    and the search/filter logic used by both the directory page and the AI
    recommender (which needs a filtered list of NGOs to hand to Gemini).

    Admin-triggered writes (create/update/delete) are wrapped in explicit
    commit/rollback blocks - same ACID "atomicity" idea from the DB
    coursework, applied for real here.

    PERFORMANCE NOTE (fix for "NGOs take too long to load"):
    The old version fetched the NGO rows, then looped over every single row
    and ran a SEPARATE query (_get_categories_for) to fetch its categories.
    For 100 NGOs that's 1 query + 100 queries = 101 round-trips. Now
    categories are pulled in the SAME query using GROUP_CONCAT, so listing
    100+ NGOs is exactly ONE query, full stop.
    """

    def __init__(self, ngo_id=None, name=None, description=None, mission=None,
                 city=None, province=None, contact=None, website=None, verified=False):
        self.ngo_id = ngo_id
        self.name = name
        self.description = description
        self.mission = mission
        self.city = city
        self.province = province
        self.contact = contact
        self.website = website
        self.verified = verified

    # ---------- Create (admin only - see app.py) ----------

    @staticmethod
    def create(name, description, mission, city, province, contact, website,
               category_ids, created_by, verified=True):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO ngos (name, description, mission, city, province, contact, website, created_by, verified)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, description, mission, city, province, contact, website, created_by, verified)
            )
            ngo_id = cursor.lastrowid

            for cat_id in category_ids:
                cursor.execute(
                    "INSERT INTO ngo_categories (ngo_id, category_id) VALUES (%s, %s)",
                    (ngo_id, cat_id)
                )

            conn.commit()
            return ngo_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    # ---------- Read ----------

    @staticmethod
    def get_by_id(ngo_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT n.*,
                          GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR '||') AS category_names
                   FROM ngos n
                   LEFT JOIN ngo_categories nc ON n.ngo_id = nc.ngo_id
                   LEFT JOIN categories c ON nc.category_id = c.category_id
                   WHERE n.ngo_id = %s
                   GROUP BY n.ngo_id""",
                (ngo_id,)
            )
            ngo = cursor.fetchone()
            if ngo:
                names = ngo.pop("category_names")
                ngo["categories"] = names.split("||") if names else []
            return ngo
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def search(keyword=None, category=None, city=None, verified_only=False, limit=None, offset=0):
        """
        Flexible search used by the directory page AND the AI recommender.
        Categories are aggregated with GROUP_CONCAT in the SAME query - no
        more per-row follow-up queries. `limit`/`offset` support pagination.

        Filtering by `category` still needs the join to narrow WHERE, but the
        GROUP_CONCAT subquery below re-fetches ALL categories per NGO (not
        just the matching one), so a filtered result still shows every tag.
        """
        params = []

        category_filter_join = ""
        category_filter_where = ""
        if category:
            category_filter_join = """
                JOIN ngo_categories fnc ON n.ngo_id = fnc.ngo_id
                JOIN categories fc ON fnc.category_id = fc.category_id
            """
            category_filter_where = " AND fc.name = %s"

        query = f"""
            SELECT n.ngo_id, n.name, n.description, n.mission, n.city, n.province,
                   n.contact, n.website, n.verified,
                   GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR '||') AS category_names
            FROM ngos n
            LEFT JOIN ngo_categories nc ON n.ngo_id = nc.ngo_id
            LEFT JOIN categories c ON nc.category_id = c.category_id
            {category_filter_join}
            WHERE 1=1
        """

        if keyword:
            query += " AND (n.name LIKE %s OR n.description LIKE %s OR n.mission LIKE %s)"
            like = f"%{keyword}%"
            params += [like, like, like]

        if category:
            query += category_filter_where
            params.append(category)

        if city:
            query += " AND n.city = %s"
            params.append(city)

        if verified_only:
            query += " AND n.verified = TRUE"

        query += " GROUP BY n.ngo_id ORDER BY n.verified DESC, n.name ASC"

        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            params += [limit, offset]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        for ngo in results:
            names = ngo.pop("category_names")
            ngo["categories"] = names.split("||") if names else []
        return results

    @staticmethod
    def get_all(verified_only=False, limit=None, offset=0):
        return NGO.search(verified_only=verified_only, limit=limit, offset=offset)

    # ---------- Update / Delete (admin only - see app.py) ----------

    @staticmethod
    def update(ngo_id, category_ids=None, **fields):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if fields:
                set_clause = ", ".join(f"{k} = %s" for k in fields)
                values = list(fields.values()) + [ngo_id]
                cursor.execute(f"UPDATE ngos SET {set_clause} WHERE ngo_id = %s", values)

            if category_ids is not None:
                cursor.execute("DELETE FROM ngo_categories WHERE ngo_id = %s", (ngo_id,))
                for cat_id in category_ids:
                    cursor.execute(
                        "INSERT INTO ngo_categories (ngo_id, category_id) VALUES (%s, %s)",
                        (ngo_id, cat_id)
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(ngo_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ngos WHERE ngo_id = %s", (ngo_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
