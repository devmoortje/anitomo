from flask import Flask, render_template, request, redirect, url_for, session

def create_app():
    app = Flask(__name__)
    app.secret_key = "CHANGE_ME"  # set from env in real apps

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
        if not session.get("user"):
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
            username = request.form.get("username","").strip()
            password = request.form.get("password","")
            user = USERS.get(username)
            if not user or user["password"] != password:
                error = "Invalid username or password."
            else:
                session["user"] = {"username": username, "display": user.get("display", username), "email": user.get("email")}
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
            elif username in USERS:
                error = "Username already taken."
            else:
                USERS[username] = {"username": username, "email": email, "password": password, "display": username}
                session["user"] = {"username": username, "display": username, "email": email}
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
