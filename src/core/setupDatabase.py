import mysql.connector
import os

def create_database_if_not_exists(cursor, db_name):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
    print(f"Database '{db_name}' dicek / dibuat.")

def execute_sql_file(cursor, sql_file_path):
    with open(sql_file_path, 'r', encoding='utf-8') as file:
        sql = file.read()
        # Eksekusi per statement (dipisah dengan ;)
        for statement in sql.split(';'):
            stmt = statement.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Gagal eksekusi statement: {stmt[:100]}...\n{e}")

def setup_database(host, user, password, db_name, sql_path):
    try:
        print("Menghubungkan ke MySQL...")
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        create_database_if_not_exists(cursor, db_name)

        cursor.execute(f"USE {db_name};")
        execute_sql_file(cursor, sql_path)

        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error saat setup: {err}")
