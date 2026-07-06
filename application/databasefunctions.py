import psycopg2
from psycopg2 import pool
from datetime import datetime, timezone
import os
database_url = os.environ.get('DATABASE_URL')



'''
result = urllib.parse.urlparse(database_url)

db_pool = pool.SimpleConnectionPool(
    1, 10,
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port,
    dbname=result.path.lstrip('/')
)'''


'''db_pool = pool.SimpleConnectionPool(
    1, 10,
    dbname="postgres",
    user="abdulrahman",
    password="99628662",
    host="localhost",
    port=5432
)'''

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

#tables
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


def create_teams_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id SERIAL PRIMARY KEY,
                team_name TEXT,
                owner_id INTEGER
            );
        """)
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)



def serve_team(user_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT team_name, team_id FROM teams WHERE owner_id = %s ;", (user_id,))
        result = cursor.fetchall()
        cursor.close()
        return result   # True if user exists
    finally:
        db_pool.putconn(conn)


def serving_members(team_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT member_id, member_name, member_role, join_date, vacation_start, vacation_end FROM members WHERE team_id = %s ORDER BY member_id;", (team_id,))
        result = cursor.fetchall()
        cursor.close()
        members = []
        for row in result:
            members.append({
                "member_id": row[0],
                "member_name": row[1],
                "member_role": row[2],
                "join_date": str(row[3]) if row[3] else None,
                "vacation_start": str(row[4]) if row[4] else None,
                "vacation_end": str(row[5]) if row[5] else None
            })
        return {"members": members}
    finally:
        db_pool.putconn(conn)

def save_new_team(team_name, user_id):
    print(f"save new team {team_name} {user_id} nnnnnnnnnnnnnbnbnbnbnbn")
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teams (team_name, owner_id)
            VALUES (%s, %s);
        """, (team_name, user_id))
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)

def create_members_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id SERIAL PRIMARY KEY,
                member_name TEXT,
                member_role INTEGER,
                vacation_start DATE,
                vacation_end DATE,
                join_date DATE DEFAULT CURRENT_DATE,
                team_id INTEGER REFERENCES teams (team_id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)
def delete_member(member_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM members
            WHERE member_id = %s;
        """, (member_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        cursor.close()
        return rows_deleted > 0
    finally:
        db_pool.putconn(conn)

def delete_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DROP TABLE IF EXISTS members;
            
        """)
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)


def save_new_member(team_id, member_name, member_role=None, vacation_start=None, vacation_end=None):
    conn = db_pool.getconn()
    print(team_id, member_name, member_role, vacation_start, vacation_end)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO members (team_id, member_name, member_role, vacation_start, vacation_end)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING member_id, join_date;
        """, (team_id, member_name, member_role, vacation_start, vacation_end))

        result = cursor.fetchone()
        conn.commit()
        return result  # Returns (member_id, join_date)
    finally:
        cursor.close()
        db_pool.putconn(conn)


def update_member(member_id, member_name, member_role=None, vacation_start=None, vacation_end=None):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE members
            SET member_name = %s,
                member_role = %s,
                vacation_start = %s,
                vacation_end = %s
            WHERE member_id = %s;
        """, (member_name, member_role, vacation_start, vacation_end, member_id))
        conn.commit()
        rows_updated = cursor.rowcount
        cursor.close()
        return rows_updated > 0
    finally:
        db_pool.putconn(conn)


def create_complaints_table():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id SERIAL PRIMARY KEY,
                user_id INTEGER,
                user_email TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)


def save_complaint(user_id, user_email, message):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaints (user_id, user_email, message, created_at)
            VALUES (%s, %s, %s, %s);
        """, (user_id, user_email, message, datetime.now(timezone.utc)))
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)


def count_users():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        result = cursor.fetchone()
        cursor.close()
        return result[0]
    finally:
        db_pool.putconn(conn)


def get_all_users():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email FROM users ORDER BY id;")
        results = cursor.fetchall()
        cursor.close()
        return [
            {
                "name": row[0],
                "email": row[1],
            }
            for row in results
        ]
    finally:
        db_pool.putconn(conn)


def get_all_complaints():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_email, message, created_at FROM complaints ORDER BY complaint_id DESC;")
        results = cursor.fetchall()
        cursor.close()
        return [
            {
                "user_email": row[0],
                "message": row[1],
                "created_at": str(row[2]) if row[2] else None,
            }
            for row in results
        ]
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


#files
def save_file_metadata(user_email, user_id,original_filename):
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
def get_team_members(team_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT member_name, member_role, vacation_start, vacation_end FROM members WHERE team_id = %s ORDER BY member_id;",
            (team_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        return [
            {
                "member_name": row[0],
                "member_role": row[1],
                "vacation_start": str(row[2]) if row[2] else None,
                "vacation_end": str(row[3]) if row[3] else None,
            }
            for row in results
        ]
    finally:
        db_pool.putconn(conn)

def get_user_files(user_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT original_filename FROM filess WHERE user_id = %s;", (user_id,))
        results = cursor.fetchall()
        cursor.close()
        return [row[0] for row in results]
    finally:
        db_pool.putconn(conn)

def delete_user_file(email):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id , original_filename FROM filess WHERE user_email = %s;", (email,))
        result = cursor.fetchone()
        file_path = os.path.join(f'./temp/{result[0]}', "schedule.xlsx")

        os.remove(file_path)

        cursor.execute("DELETE  FROM filess WHERE user_email = %s;", (email,))
        conn.commit()
        cursor.close()

    finally:
        db_pool.putconn(conn)


def delete_user_team(user_id, team_name):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE owner_id = %s AND team_name = %s;", (user_id, team_name))
        conn.commit()
        cursor.close()
        return True
    finally:
        db_pool.putconn(conn)
#users
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


#printing
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
