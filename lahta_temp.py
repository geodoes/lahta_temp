import machine
import onewire
import ds18x20
import network
import socket
import time

dat = machine.Pin(4)
ow = onewire.OneWire(dat)
ds = ds18x20.DS18X20(ow)


WIFI_SSID = "NR-410-3b1f"
WIFI_PASSWORD = "micro123"
server_ip = "192.168.1.207"  # IP-адрес компьютера
server_port = 12345         # Порт, который слушает компьютер
time.sleep(2)
roms = ds.scan()
led = machine.Pin(22,machine.Pin.OUT)
led.value(0)




# Функция для подключения к Wi-Fi
def connect():
    flag_laptop = 0

    sta_if = network.WLAN(network.STA_IF)
    time.sleep(1)
    
    try:
        print("Подключение к Wi-Fi...")
        sta_if.active(True)
        time.sleep(5)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)

        print("IP адрес:", sta_if.ifconfig()[0])
        led.value(1)
        
    except OSError:
        print("Проверьте вайфай")
        time.sleep(5)
        connect()
        machine.reset()
        
    print("Подключение к компьютеру")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((server_ip, server_port))
        time.sleep(2)
            
        print(f"Подключено к компьютеру: {server_ip}:{server_port}")
        
    except OSError:
        while True:
            if flag_laptop >= 50:
                break
            else:
                led.value(0)
                time.sleep(0.3)
                led.value(1)
                flag_laptop +=1
                print("Проверьте вай фай компьютера")
            machine.reset()


        
            
     while True:
         ds.convert_temp()
         time.sleep_ms(5)
         for rom in roms:
             sensor_value = ds.read_temp(rom)
             
         s.send(str(sensor_value).encode())  # Отправка данных
         print(f"Отправлено: {sensor_value}")
         led = machine.Pin(22,machine.Pin.OUT)
         for i in range(2):
             led.value(1)
             time.sleep(0.5)
             led.value(0)
             time.sleep(0.5)
         time.sleep(20)  # Пауза между отправками данных
