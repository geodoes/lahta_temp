import socket
import datetime
import pymysql
import re

HOST = '192.168.1.207'
PORT = 12345

DB_CONFIG = {
    'host': '90.156.211.242',
    'user': 'gen_user',
    'password': 'K_\\7.bbzW3ihhd',
    'database': 'default_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def insert_to_db(timestamp, temperature, pressure):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO monitor (date, t, p, hum, w, q)
                    VALUES (%s, %s, %s, NULL, NULL, NULL)
                """
                cursor.execute(sql, (timestamp, temperature, pressure))
            connection.commit()
            print(f"Данные записаны в БД: {timestamp}, {temperature}, {pressure}")
    except Exception as e:
        print(f"Ошибка записи в БД: {e}")

def handle_client(conn):
    with conn:
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    print("Соединение потеряно.")
                    break

                parts = re.split(r'[ ,]+', data)
                if len(parts) != 2:
                    print(f"Некорректные данные: {data}")
                    continue

                temperature = float(parts[0])
                pressure = float(parts[1])
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_to_db(timestamp, temperature, pressure)

            except (ConnectionResetError, ConnectionAbortedError):
                print("ESP отключился.")
                break
            except ValueError as ve:
                print(f"Ошибка преобразования: {ve}")
            except Exception as e:
                print(f"Ошибка во время обработки: {e}")
                break

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Ожидание подключения на {HOST}:{PORT}...")

        while True:
            try:
                conn, addr = s.accept()
                print(f"Подключено к устройству: {addr}")
                handle_client(conn)
            except Exception as e:
                print(f"Ошибка подключения: {e}")

if __name__ == "__main__":
    start_server()
