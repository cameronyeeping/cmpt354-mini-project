import sqlite3
from sqlite3 import Error


def create_table(conn, create_table_sql):
    # create_table_sql is a query (i think)
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

# db_file should be the path to an existing .db file
# returns connection object
def create_connection(db_file):
    conn = None 
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

if __name__ == '__main__':
    conn = create_connection()