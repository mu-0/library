import sqlite3
import argparse
import sys
import os
import re
import shutil

lib_dir = "lib"

# Converts a string to a filename-appropriate one
def format_filename(s):
    # Convert the filename to lowercase
    s = s.lower()
    # Replace spaces with underscores
    s = s.replace(" ", "_")
    # Remove any characters that are not alphanumeric, underscores, or hyphens
    s = re.sub(r'[^a-z0-9_-]', '', s)
    # Ensure the filename does not start or end with underscores or hyphens
    s = s.strip("_-")
    # Truncate the filename to a maximum length of 255 characters
    s = s[:255]
    return s

def connect_to_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def search_books(conn, search_query):
    cursor = conn.cursor()
    cursor.execute(search_query)
    results = cursor.fetchall()
    return results

def library_extract(conn, ids):
    results = []
    cursor = conn.cursor()
    for i in ids:
        cursor.execute(f"SELECT filename, title FROM files WHERE id = {i}")
        found = cursor.fetchall()
        if len(found) > 0:
            results.append(found[0])
    return results

def build_query(author=None, title=None, year=None, tags=None):
    base_query = "SELECT id, title, author, year FROM files WHERE"
    conditions = []
    if author:
        conditions.append(f" author LIKE '%{author}%'")
    if title:
        conditions.append(f" title LIKE '%{title}%'")
    if year:
        conditions.append(f" year = {year}")
    if tags:
        conditions.append(f" tags LIKE '%{tags}%'")
    if len(conditions) == 0:
        return "SELECT id, title, author, year FROM files"
    return base_query + " AND".join(conditions)

def print_result(result):
    i, title, author, year = result
    print(f"{i}: {title}, {author}, {year}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Search for books in the library")
    parser.add_argument("-a", "--author", help="Search by author name")
    parser.add_argument("-t", "--title", help="Search by book title")
    parser.add_argument("-y", "--year", help="Search by publication year")
    parser.add_argument("-g", "--tags", help="Search by tags")

    extraction_group = parser.add_argument_group('extraction', 'Options for extracting data')
    extraction_group.add_argument("-e", "--extract", nargs='+', type=int, help="Extract specific library data based on a list of IDs")
    extraction_group.add_argument("-d", "--dir", help="Directory where extracted files will be stored")

    args = parser.parse_args()

    conn = connect_to_db('library.db')

    if args.extract:
        if args.dir == None:
            print("Extraction requires --dir argument!")
            return
        results = library_extract(conn, args.extract)
        output_dir = os.path.abspath(args.dir)
        for result in results:
            filename, title = result
            output_filename = format_filename(title) + os.path.splitext(filename)[1]
            source = os.path.join(lib_dir, filename)
            dest = os.path.join(output_dir, output_filename)
            print(f"Copying {source} to {dest}")
            shutil.copy(source, dest)
    else:
        query = build_query(author=args.author, title=args.title, year=args.year, tags=args.tags)
        results = search_books(conn, query)
        for result in results:
            print_result(result)

    conn.close()

if __name__ == "__main__":
    main()

