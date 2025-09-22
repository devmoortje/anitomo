import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from helper import get_user_client
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from werkzeug.exceptions import BadRequestKeyError


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
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else None


    @app.route("/")
    def root():
        return redirect("/pages/main")

    # ----- Public / Landing
    @app.route("/home")
    def home():
        return redirect(url_for("pages.main"))

    @app.route("/pages/main", methods=["GET"])
    def pages_main():
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))

        res = supabase.table("profiles").select("display_name") \
                .eq("id", session["user_id"]).single().execute()
        
        display_name = res.data["display_name"]

        return render_template("main.html", flash_msg=request.args.get("m"), display_name=display_name)


    # ----- Log in
    @app.route("/auth/login", methods=["GET", "POST"])
    def auth_login():
        error = None
        if request.method == "POST":
            email = request.form.get("email","").strip().lower()
            password = request.form.get("password","")
            
            # Fetch email. If not exist, let the user know
            user_exists = supabase.table("profiles").select("id").eq("email", email).execute()
            if not user_exists.data:
                return render_template("login.html", error="Invalid email"), 400

            # Log in with supabase
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            except AuthApiError:
                return render_template("login.html", error="Invalid password"), 400
            session["access_token"] = res.session.access_token
            session["refresh_token"] = res.session.refresh_token
            session["user_id"] = res.user.id

        
        
            return redirect(url_for("pages_main"))
        return render_template("login.html", error=error)

    @app.route("/auth/logout")
    def auth_logout():
        session.clear()
        return redirect(url_for("pages.main"))

    @app.route("/auth/register", methods=["GET", "POST"])
    def auth_register():
        error = None
        if request.method == "POST":
            display_name = request.form.get("display_name","").strip()
            email = request.form.get("email","").strip()
            password = request.form.get("password","")
            confirm = request.form.get("confirm","")
            top5 = request.form.get("top5", "")
            if not display_name or not email or not password:
                error = "Please fill in all required fields."
            elif password != confirm:
                error = "Passwords do not match."
            else:
                res = supabase.auth.sign_up({"email": email, "password": password})
                user = res.user
                # if admin and user, insert a new user
                if admin and user:
                    admin.table("profiles").insert({"id": user.id, "display_name": display_name, "email": user.email, "handle": f"user_{user.id[:8]}", "top5": top5}).execute()
                return redirect(url_for("pages_main"))
        return render_template("register.html", error=error)

    # ----- Account
    @app.route("/account/me", methods=["GET", "POST"])
    def account_me():
    # 1) Require login and get a user-scoped client (RLS-aware)
        user_client = get_user_client(supabase)
        if not user_client:
            return redirect(url_for("auth.login"))

        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.login"))

        # 2) Fetch current profile
        prof_res = user_client.table("profiles") \
            .select("id, display_name, email, bio, top5, avatar_url") \
            .eq("id", user_id) \
            .execute()
        
        if not prof_res:
            return "We are sorry. We weren't able to retrieve personal information.", 500

        profile = prof_res.data[0]
        display_name = profile["display_name"]

        saved = False

        if request.method == "POST":
            # 3) Collect fields from form (use existing values as defaults)
            #    Guard against missing keys so a partial form doesn't nuke fields.
            def _get(name, default):
                try:
                    v = request.form.get(name, default)
                except BadRequestKeyError:
                    v = default
                return v

            update_payload = {
                "display_name": _get("displayName", profile.get("display_name")),
                "email":       _get("email",       profile.get("email")),
                "bio":         _get("bio",         profile.get("bio")),
                "top5":        _get("top5",        profile.get("top5"))
            }

            # Remove keys that are still None (helps if columns don’t exist yet)
            update_payload = {k: v for k, v in update_payload.items() if v is not None}

            if prof_res.data:
                # 4a) Update existing row
                user_client.table("profiles") \
                    .update(update_payload) \
                    .eq("id", user_id) \
                    .execute()
            else:
                # 4b) Insert new row (ensure id is present)
                update_payload["id"] = user_id
                user_client.table("profiles").insert(update_payload).execute()

            # Re-fetch to render fresh values
            prof_res = user_client.table("profiles") \
                .select("id, display_name, email, bio, top5, avatar_url") \
                .eq("id", user_id) \
                .execute()
            profile = prof_res.data[0] if prof_res.data else profile
            saved = True

        # 5) Render
        return render_template("account.html", user=profile, saved=saved, display_name=display_name)

    @app.route("/test")
    def test():

        # Upload image to Supabase bucket
        # user_id = session.get("user_id")
        
        # storage_path = f"{user_id}/pic.jpg"
        
        file_path = "/Users/seongjinkim/Downloads/test.jpg"
        storage_path = "img_upload_test2/pic.jpg"
        
        with open(file_path, "rb") as f:
            res = supabase.storage.from_("avatars").upload(
                path=storage_path,
                file=f
            )                    
        
        # file_path = "/Users/seongjinkim/Documents/Python/anitomo/static/images/cover.jpg"
        # storage_path = "img_upload_test/pic.jpg"
        
        # response = supabase.storage.from_('avatars').upload(storage_path, file_path)

        return render_template(
            "test.html",
            SUPABASE_URL=SUPABASE_URL,
            SUPABASE_ANON_KEY=SUPABASE_ANON_KEY)

    # Jinja-friendly endpoint names
    app.add_url_rule("/main", endpoint="pages.main", view_func=pages_main)
    app.add_url_rule("/login", endpoint="auth.login", view_func=auth_login, methods=["GET","POST"])
    app.add_url_rule("/logout", endpoint="auth.logout", view_func=auth_logout)
    app.add_url_rule("/register", endpoint="auth.register", view_func=auth_register, methods=["GET","POST"])
    app.add_url_rule("/account", endpoint="account.me", view_func=account_me, methods=["GET","POST"])

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
