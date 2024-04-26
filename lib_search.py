#!venv/bin/python

import argparse
import sys
import os
import re
import shutil
import lib_util
import dotenv
import psycopg2

def search_books(cursor, search_query):
    cursor.execute(search_query)
    results = cursor.fetchall()
    return results

def library_extract(cursor, ids):
    results = []
    for i in ids:
        cursor.execute(f"SELECT filename, title FROM files WHERE id = {i}")
        found = cursor.fetchall()
        if len(found) > 0:
            results.append(found[0])
    return results

def build_query(author=None, title=None, year=None, tag=None):
    base_query = "SELECT id, title, author, year FROM files WHERE"
    conditions = []
    if author:
        conditions.append(f" author ILIKE '%{author}%'")
    if title:
        conditions.append(f" title ILIKE '%{title}%'")
    if year:
        conditions.append(f" year = {year}")
    if tag:
        conditions.append(f" EXISTS ( SELECT 1 FROM json_array_elements_text(files.tags) AS elem WHERE elem = '{tag}');")
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
        conn = psycopg2.connect(os.environ["LIB_DB_URI"])
        cursor = conn.cursor()
        tags = lib_util.get_tags(cursor)
        conn.close()
        print(", ".join(tags))
        return
    if args.extract:
        if args.dir == None:
            print("Extraction requires --dir argument!")
            return
        conn = psycopg2.connect(os.environ["LIB_DB_URI"])
        cursor = conn.cursor()
        results = library_extract(cursor, args.extract)
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
        conn = psycopg2.connect(os.environ["LIB_DB_URI"])
        cursor = conn.cursor()
        results = search_books(cursor, query)
        conn.close()
        for result in results:
            print_result(result)


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()

