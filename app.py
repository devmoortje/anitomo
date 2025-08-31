import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError


def create_app():

    # Load env var into os.environ
    load_dotenv()

    app = Flask(__name__)

    # Set Flask secret key from env var
    app.secret_key = os.environ.get("SECRET_KEY")
    if not app.secret_key:
        raise RuntimeError("SECRET_KEY is not set")

    # Set Supabase url, anon key, service role key from env var
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY is not set")

    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    # Create Client objects supabase and admin
    # supabase can do CRUD
    #  while admin has full access to 
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else None


    # Fake in-memory "users"
    USERS = {}

    @app.route("/")
    def root():
        return redirect("/pages/index")

    # ----- Public / Landing
    @app.route("/home")
    def home():
        return redirect(url_for("pages.index"))

    @app.route("/index")
    def index_redirect():
        return redirect(url_for("pages.index"))

    # Blueprint-like grouping via endpoints
    @app.route("/pages/index")
    def pages_index():
        return render_template("index.html")

    @app.route("/pages/main", methods=["GET"])
    def pages_main():
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return render_template("main.html", flash_msg=request.args.get("m"))

    @app.route("/pages/create-room", methods=["POST"])
    def pages_create_room():
        if not session.get("user"):
            return redirect(url_for("auth.login"))
        # pretend a room was created
        return redirect(url_for("pages_main", m="🎬 Room created (demo)."))

    @app.route("/pages/quick-match", methods=["POST"])
    def pages_quick_match():
        if not session.get("user"):
            return redirect(url_for("auth.login"))
        return redirect(url_for("pages_main", m="🎯 We'd match you with 3 people (demo)."))

    # ----- Auth
    @app.route("/auth/login", methods=["GET", "POST"])
    def auth_login():
        error = None
        if request.method == "POST":
            email = request.form.get("email","").strip()
            password = request.form.get("password","")
            print("------------BEFORE RES-----------")
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            except AuthApiError as e:
        # Typical message: "Invalid login credentials"
        # str(e) is safe and human-readable; status code if you need it:
                status = getattr(e, "status_code", 400)
                return render_template("login.html", error=str(e)), status

            
            
            # res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            print("------------AFTER RES-----------")
            if res.user is None:  
            # Login failed
                if res.error:
                    error_message = res.error.message   # e.g. "Invalid login credentials"
                else:
                    error_message = "Login failed for unknown reason."
                return render_template("login.html", error=error_message)

            session["access_token"] = res.session.access_token
            session["user_id"] = res.user.id
            print(f"session user id is: {session.get('user_id')}")

            return redirect(url_for("pages_main"))
        return render_template("login.html", error=error)

    @app.route("/auth/logout")
    def auth_logout():
        session.clear()
        return redirect(url_for("pages.index"))

    @app.route("/auth/register", methods=["GET", "POST"])
    def auth_register():
        error = None
        if request.method == "POST":
            username = request.form.get("username","").strip()
            email = request.form.get("email","").strip()
            password = request.form.get("password","")
            confirm = request.form.get("confirm","")
            if not username or not email or not password:
                error = "Please fill in all required fields."
            elif password != confirm:
                error = "Passwords do not match."
            else:
                res = supabase.auth.sign_up({"email": email, "password": password})
                user = res.user
                # if admin and user, insert a new user
                if admin and user:
                    admin.table("profiles").insert({"id": user.id, "display_name": "", "email": user.email, "handle": f"user_{user.id[:8]}"}).execute()
                return redirect(url_for("pages_main"))
        return render_template("register.html", error=error)

    # ----- Account
    @app.route("/account/me", methods=["GET", "POST"])
    def account_me():
        if not session.get("user"):
            return redirect(url_for("auth.login"))
        username = session["user"]["username"]
        user = USERS.get(username, {})
        saved = False
        if request.method == "POST":
            user["display"] = request.form.get("displayName", user.get("display"))
            user["email"] = request.form.get("email", user.get("email"))
            user["bio"] = request.form.get("bio", user.get("bio",""))
            user["top5"] = request.form.get("top5", user.get("top5",""))
            user["tags"] = request.form.get("tags", user.get("tags",""))
            USERS[username] = user
            session["user"]["display"] = user.get("display", username)
            saved = True
        return render_template("account.html", user=user, saved=saved)

    # Jinja-friendly endpoint names
    app.add_url_rule("/pages/index", endpoint="pages.index", view_func=pages_index)
    app.add_url_rule("/main", endpoint="pages.main", view_func=pages_main)
    app.add_url_rule("/create-room", endpoint="pages.create_room", view_func=pages_create_room, methods=["POST"])
    app.add_url_rule("/quick-match", endpoint="pages.quick_match", view_func=pages_quick_match, methods=["POST"])
    app.add_url_rule("/login", endpoint="auth.login", view_func=auth_login, methods=["GET","POST"])
    app.add_url_rule("/logout", endpoint="auth.logout", view_func=auth_logout)
    app.add_url_rule("/register", endpoint="auth.register", view_func=auth_register, methods=["GET","POST"])
    app.add_url_rule("/account", endpoint="account.me", view_func=account_me, methods=["GET","POST"])

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
