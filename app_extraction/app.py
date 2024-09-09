import flask
import werkzeug
app = flask.Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():

    # validate post contents
    if "file" not in flask.request.files:
        return "no file uploaded", 400

    file = flask.request.files["file"]

    # validate file exists
    if not file:
        return "invalid file", 400

    filename = werkzeug.utils.secure_filename(file.filename)

    return filename


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
