import sqlite3

conn = sqlite3.connect(":memory:")  # or an actual .db file

sql = """
SELECT *
FROM NonExistentTable
"""

try:
    conn.execute(sql)
    # If this doesn't raise an error, it's at least parseable + the table exists
    print("Successfully parsed/query-planned")
except sqlite3.Error as e:
    print("Parse or planning error:", e)
    raise
