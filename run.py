import socket
import datetime
import pymysql

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

def insert_to_db(timestamp, temperature):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO monitor (date, t, p, hum, w, q)
                    VALUES (%s, %s, NULL, NULL, NULL, NULL)
                """
                cursor.execute(sql, (timestamp, temperature))
            connection.commit()
            print(f"Данные записаны в БД: {timestamp}, {temperature}")
    except Exception as e:
        print(f"Ошибка записи в БД: {e}")

def is_valid_data(data):
    try:
        float(data.strip())
        return True
    except ValueError:
        return False

def clean_data(data):
    # Разделение склеенных значений и фильтрация
    parts = data.strip().split()
    for part in parts:
        if is_valid_data(part):
            return float(part.strip())
    raise ValueError("Нет валидных данных")

def handle_client(conn):
    with conn:
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    print("Соединение потеряно.")
                    break

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if is_valid_data(data):
                    temperature = float(data)
                else:
                    temperature = clean_data(data)

                insert_to_db(timestamp, temperature)

            except (ConnectionResetError, ConnectionAbortedError):
                print("ESP отключился.")
                break
            except ValueError as ve:
                print(f"Ошибка: некорректные данные: {data}")
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
