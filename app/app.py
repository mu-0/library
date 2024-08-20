import os
import flask
import flask_login
import flask_sqlalchemy
import werkzeug.security as ws

app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "flask_default_secret_key")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# defaults to ./instance/db.sqlite ?
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"

db = flask_sqlalchemy.SQLAlchemy(app)

class UserTable(flask_login.UserMixin, db.Model):
    # user.id is what gets stored in the cookie, and is used for retrieving the user (see load_user())
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)

@login_manager.user_loader
def load_user(user_id):
    return UserTable.query.filter_by(id = user_id).first()

@app.route("/login")
def login():
    return flask.render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    next_page = flask.request.args.get("next")
    user = UserTable.query.filter_by(username = username).first()
    if not user or not ws.check_password_hash(user.password, password):
        return flask.redirect(flask.url_for("login"))
    flask_login.login_user(user)
    return flask.redirect(next_page or flask.url_for("index"))

@app.route("/")
@flask_login.login_required
def index():
    return "index"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
