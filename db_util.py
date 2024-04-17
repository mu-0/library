import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect('library.db')

# Create a cursor object using the cursor() method
cursor = connection.cursor()

# Define the SQL query to select all rows from the table
sql_query = "SELECT * FROM files"

# Execute the SQL query
cursor.execute(sql_query)

# Fetch all rows from the executed SQL query
rows = cursor.fetchall()

# Iterate through the rows and print them
for row in rows:
    print(row)

# Close the connection to the database
connection.close()

