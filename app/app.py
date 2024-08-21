import os
import re
import flask
import flask_login
import flask_sqlalchemy
import boto3
import werkzeug.security as ws
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "flask_default_secret_key")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SQLALCHEMY_BINDS"] = {
    # defaults to ./instance/db.sqlite ?
    "users_db": "sqlite:///db.sqlite",
    "files_db": os.getenv("FILES_DB")
}

db = flask_sqlalchemy.SQLAlchemy(app)

class UserTable(flask_login.UserMixin, db.Model):
    __bind_key__ = "users_db"
    # user.id is what gets stored in the cookie, and is used for retrieving the user (see load_user())
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)

class Files(db.Model):
    __bind_key__ = "files_db"
    id = db.Column(db.Integer, primary_key = True)
    filename = db.Column(db.String, nullable = False)
    title = db.Column(db.String, nullable = False)
    author = db.Column(db.String)
    year = db.Column(db.String)
    edition = db.Column(db.String)
    tags = db.Column(db.JSON)

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

# this sucks so much, top of 'do better' priorities
@app.route('/data', methods=['POST'])
@flask_login.login_required
def data():
    tag = flask.request.json['tag']
    title = flask.request.json["title"]
    author = flask.request.json["author"]

    if tag == "none":
        tag = None

    items = Files.query.filter(Files.title.ilike(f"%{title}%")).filter(Files.author.ilike(f"%{author}%")).all()

    # couldn't work out a sqlalchemy filter for tags, think i need to redo the schema
    if tag is not None:
        items_filtered = []
        for item in items:
            if tag in item.tags:
                items_filtered.append(item)
        items = items_filtered

    def to_dict(item):
        return {column.name: getattr(item, column.name) for column in item.__table__.columns}

    return flask.jsonify([to_dict(item) for item in items])

@app.route('/retrieve')
def retrieve():

    def format_filename(s):
        s = s.lower()
        s = s.replace(" ", "_")
        s = re.sub(r'[^a-z0-9_-]', '', s)
        s = s.strip("_-")
        s = s[:255]
        return s

    filename = flask.request.args.get("file")

    file = Files.query.filter_by(filename = filename).first()

    title = file.title
    title = format_filename(title) + os.path.splitext(filename)[1]
    
    region = os.environ["AWS_REGION"]
    lib_bucket_name = os.environ["LIB_BUCKET_NAME"]
    lib_bucket_path = os.environ["LIB_BUCKET_PATH"]
    filepath = os.path.join(lib_bucket_path, filename)
    s3_client = boto3.client('s3', region_name=region)
    try:
        file_obj = s3_client.get_object(Bucket=lib_bucket_name, Key=filepath)
        return flask.Response(
            file_obj["Body"].read(),
            mimetype = "application/octet-stream",
            headers = {"Content-Disposition": f"attachment;filename={title}"}
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        return str(e)


@app.route("/")
@flask_login.login_required
def index():
    # items used to generate tag list. please do better
    items = Files.query.all()
    tags = sorted(set(sum([item.tags for item in items], [])))
    return flask.render_template('index.html', tags=tags)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
