#!venv/bin/python

from flask import Flask, request, render_template, send_from_directory, jsonify, Response
import psycopg2
import psycopg2.extras
import os
import re
import dotenv
import lib_util
import json
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

app = Flask(__name__)

def get_items(author=None, title=None, year=None, tag=None, itemid=None):

    query = "SELECT * FROM files"
    conditions = []
    if author:
        conditions.append(f" author ILIKE '%{author}%'")
    if title:
        conditions.append(f" title ILIKE '%{title}%'")
    if year:
        conditions.append(f" year = {year}")
    if tag is not None:
        conditions.append(f" EXISTS ( SELECT 1 FROM json_array_elements_text(files.tags) AS elem WHERE elem = '{tag}');")
    if itemid:
        conditions.append(f" id = {itemid}")
    if len(conditions) > 0:
        query += " WHERE " + " AND".join(conditions)

    conn = psycopg2.connect(os.environ["LIB_DB_URI"])
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query)
    items = cursor.fetchall()
    conn.close()

    return [dict(ix) for ix in items]
    

@app.route('/')
def index():
    items = get_items()
    tags = sorted(set(sum([item["tags"] for item in items], [])))
    return render_template('index.html', tags=tags)


@app.route('/retrieve')
def retrieve():
    fileid = request.args.get("file")

    if not re.match(r"^\d+$", fileid):
        return "Invalid file id!", 400

    files = get_items(itemid = fileid)
    if len(files) == 0:
        return "File not found in library!", 400

    title = files[0]["title"]
    filename = files[0]["filename"]
    title = lib_util.format_filename(title) + os.path.splitext(filename)[1]
    
    region = os.environ["AWS_REGION"]
    lib_bucket_name = os.environ["LIB_BUCKET_NAME"]
    lib_bucket_path = os.environ["LIB_BUCKET_PATH"]
    file = os.path.join(lib_bucket_path, filename)
    s3_client = boto3.client('s3', region_name=region)
    try:
        file_obj = s3_client.get_object(Bucket=lib_bucket_name, Key=file)
        return Response(
            file_obj["Body"].read(),
            mimetype = "application/octet-stream",
            headers = {"Content-Disposition": f"attachment;filename={title}"}
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        return str(e)

    


@app.route('/data', methods=['POST'])
def data():
    tag = request.json['tag']
    title = request.json["title"]
    author = request.json["author"]
    if tag == "none":
        tag = None
    if title == "":
        title = None
    if author == "":
        author = None
    items = get_items(tag=tag, title=title, author=author)
    items = sorted(items, key = lambda x: x["title"])
    return jsonify(items)


if __name__ == '__main__':
    dotenv.load_dotenv()
    app.run(debug=True)
