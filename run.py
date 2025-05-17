import datetime
import re
import socket
import time
import pymysql
import serial.tools.list_ports

HOST = '192.168.1.180'
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

################ГИГРОМЕТР###########################

port = "COM6"
baudrate = 19200

ser = serial.Serial(port, baudrate=baudrate, timeout=1)

stand_name = 4

def calc_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

def get_gygro():
    request = bytearray([0x01, 0x03, 0x00, 0x01, 0x00, 0x02])
    crc = calc_crc(request)
    request += crc
    ser.write(request)
    # Прочитайте ожидаемое количество байт
    response = ser.read(9)  # для 2 регистров (1+1+1+2*2+2)
    print(f"RESPONSE - {response}")
    data = response[3:7]
    P = int.from_bytes(data[0:2])
    Temp = int.from_bytes(data[2:4])

    return Temp / 100

def insert_to_db(timestamp, temperature, pressure, w):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO monitor (date, t, p, hum, w, q)
                    VALUES (%s, %s, %s, NULL, %s, %s)
                """
                cursor.execute(sql, (timestamp, temperature, pressure, w, stand_name))
            connection.commit()
            print(f"Данные записаны в БД: {timestamp}, {temperature}, {pressure}, {w}, {stand_name}")
    except Exception as e:
        print(f"Ошибка записи в БД: {e}")

def handle_client(conn):
    print("Опрашиваю метеостанцию")



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

                try:
                    time.sleep(2)
                    air_temp = get_gygro()  # Получаем температуру воздуха
                except Exception as e:
                    print(f"Ошибка при получении данных с гигрометра: {e}")
                    air_temp = None

                temperature = float(parts[0])
                pressure = float(parts[1])
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Передаем air_temp в качестве параметра w
                insert_to_db(timestamp, temperature, pressure, air_temp)

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