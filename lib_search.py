#!venv/bin/python

import sqlite3
import argparse
import sys
import os
import re
import shutil
import lib_util
import dotenv

def search_books(conn, search_query):
    results = conn.cursor().execute(search_query).fetchall()
    return results

def library_extract(conn, ids):
    results = []
    for i in ids:
        found = conn.cursor().execute(f"SELECT filename, title FROM files WHERE id = {i}").fetchall()
        if len(found) > 0:
            results.append(found[0])
    return results

def build_query(author=None, title=None, year=None, tag=None):
    base_query = "SELECT id, title, author, year FROM files WHERE"
    conditions = []
    if author:
        conditions.append(f" author LIKE '%{author}%'")
    if title:
        conditions.append(f" title LIKE '%{title}%'")
    if year:
        conditions.append(f" year = {year}")
    if tag:
        conditions.append(f" EXISTS ( SELECT 1 FROM json_each(files.tags) WHERE json_each.value = '{tag}');")
    if len(conditions) == 0:
        return "SELECT id, title, author, year FROM files"
    return base_query + " AND".join(conditions)

def print_result(result):
    i, title, author, year = result
    print(f"{i}: {title}, {author}, {year}")

def main():

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

    parser = argparse.ArgumentParser(description="Search for books in the library")
    parser.add_argument("-a", "--author", help="Search by author name")
    parser.add_argument("-t", "--title", help="Search by book title")
    parser.add_argument("-y", "--year", help="Search by publication year")
    parser.add_argument("-g", "--tag", help="Search by tag")

    extraction_group = parser.add_argument_group('extraction', 'Options for extracting data')
    extraction_group.add_argument("-e", "--extract", nargs='+', type=int, help="Extract specific library data based on a list of IDs")
    extraction_group.add_argument("-d", "--dir", help="Directory where extracted files will be stored")

    misc_group = parser.add_argument_group("misc", "Other search functions")
    misc_group.add_argument("--tags", action="store_true", help="Print available tags")

    args = parser.parse_args()

    if args.tags:
        conn = sqlite3.connect(lib_db)
        tags = lib_util.get_tags(conn)
        conn.close()
        print(", ".join(tags))
        return
    if args.extract:
        if args.dir == None:
            print("Extraction requires --dir argument!")
            return
        conn = sqlite3.connect(lib_db)
        results = library_extract(conn, args.extract)
        conn.close()
        output_dir = os.path.abspath(args.dir)
        for result in results:
            filename, title = result
            output_filename = lib_util.format_filename(title) + os.path.splitext(filename)[1]
            source = os.path.join(lib_dir, filename)
            dest = os.path.join(output_dir, output_filename)
            print(f"Copying {source} to {dest}")
            shutil.copy(source, dest)
    else:
        query = build_query(author=args.author, title=args.title, year=args.year, tag=args.tag)
        conn = sqlite3.connect(lib_db)
        results = search_books(conn, query)
        conn.close()
        for result in results:
            print_result(result)


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()

