#!venv/bin/python

import os
import hashlib
import json
import sqlite3
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

# Check if a file already exists in lib
def check_uniqueness(md5, lib_dir):
    file_hashes = [f.split('.')[0] for f in os.listdir(lib_dir)]
    if md5 in file_hashes:
        return False
    return True

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


def handle_file(file, lib_dir, lib_db):
    print(f"Parsing {file}...")

    # Check if file is already in lib
    file_md5 = calculate_file_md5(file)
    if not check_uniqueness(file_md5, lib_dir):
        print(f"File {file} already exists in lib! (md5={file_md5})")
        return False
    new_filename = file_md5 + os.path.splitext(file)[-1]

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

    # Add file to library database
    conn = sqlite3.connect(lib_db)
    c = conn.cursor()
    c.execute("INSERT INTO files (filename, title, author, year, edition, tags) VALUES (?, ?, ?, ?, ?, ?)", (new_filename, filedata["title"], filedata["author"], filedata["year"], filedata["edition"], json.dumps(filedata["tags"])))
    conn.commit()
    conn.close()

    # Move file to library
    os.rename(file, os.path.join(lib_dir, new_filename))


def main():

    intake_dir = os.environ['INTAKE_DIR']
    # Check that intake directory is valid
    if not os.path.isdir(intake_dir):
        print("Could not find intake directory!")
        return

    lib_dir = os.environ['LIB_DIR']
    # Check that library directory is valid
    if not os.path.isdir(lib_dir):
        print("Could not find library directory!")
        return

    lib_db = os.path.join(lib_dir, os.environ['LIB_DB'])
    # Check that library database is valid
    if not os.path.isfile(os.path.join(lib_dir, lib_db)):
        print("Could not find library database!")
        return

    files = intake(intake_dir)
    for file in files:
        handle_file(file, lib_dir, lib_db)


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()
