import psycopg2
from psycopg2 import pool
from datetime import datetime, timezone
import os
database_url = os.environ.get('DATABASE_URL')


db_pool = pool.SimpleConnectionPool(
    1, 10,
    dsn = database_url
)

def user_id(email):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
        result = cursor.fetchone()
        print(f"this is the user id according to the db {result[0]}")
        cursor.close()
        return result[0]  # True if user exists
    finally:
        db_pool.putconn(conn)


def create_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                sign_in_time TIMESTAMP,
                subscription_times INTEGER,
                subscription_status TEXT,
                subscription_start_date TIMESTAMP,
                subscription_end_date DATE
            );
        """)
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)

def create_file_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS filess (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        user_id INTEGER,
        original_filename TEXT NOT NULL)""")
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)



def save_file_metadata(user_email, user_id,
                       original_filename):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO filess (user_email, user_id, original_filename)
            VALUES (%s, %s, %s);
        """, (user_email, user_id, original_filename))
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)
def chech_file_metadata():
    pass


def user_exists(email):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1;", (email,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None  # True if user exists
    finally:
        db_pool.putconn(conn)


def save_new_user(name, email):

    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, sign_in_time)
            VALUES (%s, %s, %s);
        """, (
            name,
            email,
            datetime.now(timezone.utc)
        ))
        conn.commit()
        cursor.close()
        return True  # New user saved successfully
    finally:
        db_pool.putconn(conn)

def delete_user_file(email):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id , original_filename FROM filess WHERE user_email = %s;", (email,))
        result = cursor.fetchone()
        file_path = os.path.join(f'/d/temp/{result[0]}', "schedule.xlsx")

        os.remove(file_path)

        cursor.execute("DELETE  FROM filess WHERE user_email = %s;", (email,))
        conn.commit()
        cursor.close()

    finally:
        db_pool.putconn(conn)


def print_user_data(email):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            column_names = [desc[0] for desc in cursor.description]
            user_data = dict(zip(column_names, user))
            print("User Data:")
            for key, value in user_data.items():
                print(f"{key}: {value}")
            return user_data  # optional, in case you want to use it elsewhere
        else:
            print("User not found.")
            return None

    finally:
        db_pool.putconn(conn)

def print_all_user_data():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users;")
        users = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()

        if users:
            print("All Users:")
            for user in users:
                user_data = dict(zip(column_names, user))
                for key, value in user_data.items():
                    print(f"{key}: {value}")
                print("-" * 20)  # separator between users
            return users
        else:
            print("No users found.")
            return []

    finally:
        db_pool.putconn(conn)




def print_users():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users;")
        for row in cursor.fetchall():
            print(row)
        cursor.close()
    finally:
        db_pool.putconn(conn)
