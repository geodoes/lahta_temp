import machine
import onewire
import ds18x20
import network
import socket
import time

# Настройка пинов и устройств
dat = machine.Pin(4)
ow = onewire.OneWire(dat)
ds = ds18x20.DS18X20(ow)
led = machine.Pin(22, machine.Pin.OUT)

WIFI_SSID = "NR-410-3b1f"
WIFI_PASSWORD = "micro123"
server_ip = "192.168.1.207"
server_port = 12345

# Поиск датчиков
try:
    roms = ds.scan()
    if not roms:
        raise Exception("Нет датчиков")
except Exception:
    for _ in range(3):
        led.value(1)
        time.sleep(0.2)
        led.value(0)
        time.sleep(0.2)
    machine.reset()

# Функция мигания
def blink(times, duration=0.3, pause=0.3):
    for _ in range(times):
        led.value(1)
        time.sleep(duration)
        led.value(0)
        time.sleep(pause)
    time.sleep(1)

# Подключение к Wi-Fi
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)

    timeout = 15
    while not sta_if.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
    if not sta_if.isconnected():
        blink(1)
        machine.reset()
    else:
        blink(1, duration=1)

# Подключение к серверу
def connect_server():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, server_port))
        blink(2, duration=1)
        return s
    except Exception:
        blink(2)
        machine.reset()

# Основной цикл
connect_wifi()
sock = connect_server()

while True:
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        for rom in roms:
            temp = ds.read_temp(rom)
            if temp is None:
                raise ValueError("Ошибка датчика")
            sock.send(str(temp).encode())
            print("Отправлено:", temp)
            blink(2, duration=0.2, pause=0.2)
        time.sleep(20)
    except Exception:
        blink(3)
        machine.reset()

