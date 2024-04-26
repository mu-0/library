#!venv/bin/python

import os
import hashlib
import json
import psycopg2
import boto3
from botocore.exceptions import ClientError
import dotenv
from openai import OpenAI

# Returns list of files in intake_dir
def intake(intake_dir):
    full_paths = [os.path.join(intake_dir, f) for f in os.listdir(intake_dir) if os.path.isfile(os.path.join(intake_dir, f))]
    return full_paths

# Calculate MD5 hash of a file
def calculate_file_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

# Get file metadata from GPT. Returns dictionary
def get_file_metadata(file):
    basename = os.path.basename(file)

    client = OpenAI(api_key = os.environ['OPENAI_KEY'])
    
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[{"role": "user", "content": f"I am giving you the filename of a book. You are to do your best to figure out the title, author, and year published. This information may or may not be in the filename, so you may need to use context from your training data. Please output in JSON containing fields of title, author, and year.\n{basename}"}
      ]
    )

    try:
        filedata = json.loads(completion.choices[0].message.content)
    except json.decoder.JSONDecodeError:
        filedata = {"title": "", "author": "", "year": ""}

    filedata["edition"] = ""
    filedata["tags"] = []

    return filedata


def handle_file(file, force=False):
    print(f"Parsing {file}...")

    file_md5 = calculate_file_md5(file)
    new_filename = file_md5 + os.path.splitext(file)[-1]

    # Set up S3 client
    region = os.environ["AWS_REGION"]
    lib_bucket_name = os.environ["LIB_BUCKET_NAME"]
    lib_file = os.path.join(os.environ["LIB_BUCKET_PATH"], new_filename)
    s3_client = boto3.client("s3", region_name=region)
    
    # Make sure file doesn't already exist
    if not force:
        try:
            s3_client.head_object(Bucket=lib_bucket_name, Key=lib_file)
            print("File already exists on server!")
            return
        except ClientError as e:
            if int(e.response["Error"]["Code"]) != 404:
                print("Other client error:", e)
                return

    # Attempt to get file metadata
    filedata = get_file_metadata(file)

    # Let user review metadata
    with open("tmp.json", 'w') as f:
        json.dump(filedata, f, indent=4)
    with open("tmp.json", 'r') as f:
        print(f.read())
    if input("Press Enter when reviewed. Enter 0 to skip.\n") == "0":
        print("Skipping")
        os.remove("tmp.json")
        return False
    with open("tmp.json", 'r') as f:
        filedata = json.load(f)
    os.remove("tmp.json")

    response = s3_client.upload_file(file, lib_bucket_name, lib_file)

    # Add file to library database
    conn = psycopg2.connect(os.environ["LIB_DB_URI"])
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO files (filename, title, author, year, edition, tags) VALUES ('{new_filename}', '{filedata['title']}', '{filedata['author']}', '{filedata['year']}', '{filedata['edition']}', '{json.dumps(filedata['tags'])}')")
    conn.commit()
    conn.close()

    os.remove(file)


def main():

    intake_dir = os.environ['INTAKE_DIR']
    # Check that intake directory is valid
    if not os.path.isdir(intake_dir):
        print("Could not find intake directory!")
        return

    files = intake(intake_dir)
    for file in files:
        handle_file(file)


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()
