import re

# returns a list of tags. tags in the tag field are a json-encoded array.
def get_tags(cursor):
    tags = []

    cursor.execute("SELECT tags FROM files")
    found = cursor.fetchall()
    for item in found:
        item_tags = item[0]
        for tag in item_tags:
            if tag not in tags and tag != "":
                tags.append(tag)

    tags.sort()
    return tags

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

