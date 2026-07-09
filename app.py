from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from config import Config
from models.user import User
from models.ngo import NGO
from models.review import Review
from models.admin import Admin
from models.ai_recommender import AIRecommender

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# Vercel (like most serverless/CDN hosts) terminates TLS at its edge and
# forwards plain HTTP to the function, adding X-Forwarded-* headers to say
# what the original request looked like. Without ProxyFix, Flask thinks
# every request is unencrypted HTTP, which breaks anything that checks
# request.is_secure - notably the SESSION_COOKIE_SECURE setting below.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Session cookie hardening for production. SECURE means the browser will
# only ever send the cookie over HTTPS (Vercel is HTTPS-only, so this is
# free); HTTPONLY blocks JS from reading it (defense against XSS stealing
# a session); SAMESITE=Lax is the standard balance of CSRF protection
# without breaking normal top-level navigation/login flows.
app.config["SESSION_COOKIE_SECURE"] = Config.IS_PRODUCTION
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ---------- RBAC decorators ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


def _current_user():
    if "user_id" not in session:
        return None
    return {"user_id": session["user_id"], "name": session.get("name"), "role": session.get("role")}


# ---------- Sanity check ----------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "ImpactConnect backend is running"})


# ---------- Page routes (server-rendered, RBAC-gated) ----------
@app.route("/")
def home_page():
    return render_template("index.html", user=_current_user())


@app.route("/directory")
def directory_page():
    return render_template("directory.html", user=_current_user())


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/rahnuma")
def rahnuma_page():
    return render_template("rahnuma.html", user=_current_user())


@app.route("/ngo/<int:ngo_id>")
def ngo_detail_page(ngo_id):
    return render_template("ngo_detail.html", ngo_id=ngo_id, user=_current_user())


@app.route("/admin")
def admin_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin.html", user=_current_user())


@app.route("/dashboard")
def dashboard_page():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_page"))
    return render_template("dashboard.html", user=_current_user())


# ---------- Auth (JSON API, sets session cookie on success) ----------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    try:
        # Role is ALWAYS "donor" here, regardless of what the client sends.
        # Admin accounts are never self-registered - they're promoted manually
        # in the database. This prevents anyone from POSTing role: "admin"
        # to this endpoint and granting themselves admin access.
        user_id = User.register(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            role="donor"
        )
        session["user_id"] = user_id
        session["name"] = data["name"]
        session["role"] = "donor"
        return jsonify({"message": "Registered successfully", "user": _current_user()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    requested_role = data.get("login_as")  # "admin" or "user", chosen on the login screen

    user = User.login(data["email"], data["password"])
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # The account's real role always comes from the DB (never trust the
    # client for authorization) - but we DO use the selected tab to give a
    # clear, specific error instead of silently landing on the wrong
    # dashboard. "user" here covers both donor and ngo_admin accounts.
    actual_is_admin = user.role == "admin"
    requested_is_admin = requested_role == "admin"

    if requested_role and actual_is_admin != requested_is_admin:
        if requested_is_admin:
            return jsonify({"error": "This account isn't an admin account. Try logging in as User instead."}), 403
        return jsonify({"error": "This is an admin account. Try logging in as Admin instead."}), 403

    session["user_id"] = user.user_id
    session["name"] = user.name
    session["role"] = user.role
    return jsonify({"message": "Login successful", "user": user.to_dict()})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/me", methods=["GET"])
def me():
    return jsonify(_current_user())


# ---------- Public stats (for the landing page strip - no login needed) ----------
@app.route("/api/public-stats", methods=["GET"])
def public_stats():
    from db.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM ngos")
        total_ngos = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS verified FROM ngos WHERE verified = TRUE")
        verified_ngos = cursor.fetchone()["verified"]
        cursor.execute("SELECT COUNT(*) AS total_categories FROM categories")
        total_categories = cursor.fetchone()["total_categories"]
        return jsonify({
            "total_ngos": total_ngos,
            "verified_ngos": verified_ngos,
            "total_categories": total_categories
        })
    finally:
        cursor.close()
        conn.close()


# ---------- NGOs ----------
@app.route("/api/ngos", methods=["GET"])
def list_ngos():
    keyword = request.args.get("q")
    category = request.args.get("category")
    city = request.args.get("city")
    verified_only = request.args.get("verified") == "true"
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", default=0, type=int)
    results = NGO.search(keyword=keyword, category=category, city=city,
                         verified_only=verified_only, limit=limit, offset=offset)
    return jsonify(results)


@app.route("/api/ngos/<int:ngo_id>", methods=["GET"])
def get_ngo(ngo_id):
    ngo = NGO.get_by_id(ngo_id)
    if not ngo:
        return jsonify({"error": "NGO not found"}), 404
    ngo["average_rating"] = Review.get_average_rating(ngo_id)
    return jsonify(ngo)


# ---------- NGO management (admin only - real authority, not just a form) ----------
@app.route("/api/ngos", methods=["POST"])
@admin_required
def create_ngo():
    data = request.get_json()
    try:
        ngo_id = NGO.create(
            name=data["name"],
            description=data.get("description", ""),
            mission=data.get("mission", ""),
            city=data.get("city", ""),
            province=data.get("province", ""),
            contact=data.get("contact", ""),
            website=data.get("website", ""),
            category_ids=data.get("category_ids", []),
            created_by=session["user_id"],
            verified=data.get("verified", True)
        )
        return jsonify({"message": "NGO added", "ngo_id": ngo_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/ngos/<int:ngo_id>", methods=["PUT"])
@admin_required
def update_ngo(ngo_id):
    data = request.get_json()
    category_ids = data.pop("category_ids", None)
    allowed_fields = {"name", "description", "mission", "city", "province", "contact", "website", "verified"}
    fields = {k: v for k, v in data.items() if k in allowed_fields}
    try:
        NGO.update(ngo_id, category_ids=category_ids, **fields)
        return jsonify({"message": "NGO updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/ngos/<int:ngo_id>", methods=["DELETE"])
@admin_required
def delete_ngo(ngo_id):
    try:
        NGO.delete(ngo_id)
        return jsonify({"message": "NGO deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------- Categories ----------
@app.route("/api/categories", methods=["GET"])
def list_categories():
    from db.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()


# ---------- Reviews ----------
@app.route("/api/ngos/<int:ngo_id>/reviews", methods=["GET"])
def get_reviews(ngo_id):
    return jsonify(Review.get_for_ngo(ngo_id))


@app.route("/api/ngos/<int:ngo_id>/reviews", methods=["POST"])
@login_required
def add_review(ngo_id):
    data = request.get_json()
    try:
        review_id = Review.add_review(
            user_id=session["user_id"],
            ngo_id=ngo_id,
            rating=data["rating"],
            comment=data.get("comment", "")
        )
        return jsonify({"message": "Review added", "review_id": review_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/my-reviews", methods=["GET"])
@login_required
def my_reviews():
    from db.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT r.review_id, r.rating, r.comment, r.created_at, n.ngo_id, n.name AS ngo_name
               FROM reviews r JOIN ngos n ON r.ngo_id = n.ngo_id
               WHERE r.user_id = %s ORDER BY r.created_at DESC""",
            (session["user_id"],)
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()


# ---------- Admin (RBAC-protected: session role must be 'admin') ----------
@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    return jsonify(Admin.get_dashboard_stats())


@app.route("/api/admin/all-ngos", methods=["GET"])
@admin_required
def admin_all_ngos():
    keyword = request.args.get("q")
    return jsonify(NGO.search(keyword=keyword, verified_only=False))


# ---------- AI Recommendation ----------
@app.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query text is required"}), 400
    recommendations = AIRecommender.recommend(query)
    return jsonify({"query": query, "recommendations": recommendations})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
