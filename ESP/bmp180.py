# bmp180.py - MicroPython driver for BMP180
import time
import struct

class BMP180:
    def __init__(self, i2c, addr=0x77):
        self.i2c = i2c
        self.addr = addr
        self._read_calibration_data()
        self.oversample_sett = 0
        self.sea_level_pressure = 101325

    def _read_signed_16(self, register):
        data = self.i2c.readfrom_mem(self.addr, register, 2)
        result = struct.unpack('>h', data)[0]
        return result

    def _read_unsigned_16(self, register):
        data = self.i2c.readfrom_mem(self.addr, register, 2)
        result = struct.unpack('>H', data)[0]
        return result

    def _read_calibration_data(self):
        self.AC1 = self._read_signed_16(0xAA)
        self.AC2 = self._read_signed_16(0xAC)
        self.AC3 = self._read_signed_16(0xAE)
        self.AC4 = self._read_unsigned_16(0xB0)
        self.AC5 = self._read_unsigned_16(0xB2)
        self.AC6 = self._read_unsigned_16(0xB4)
        self.B1 = self._read_signed_16(0xB6)
        self.B2 = self._read_signed_16(0xB8)
        self.MB = self._read_signed_16(0xBA)
        self.MC = self._read_signed_16(0xBC)
        self.MD = self._read_signed_16(0xBE)

    def _read_raw_temp(self):
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x2E')
        time.sleep_ms(5)
        data = self.i2c.readfrom_mem(self.addr, 0xF6, 2)
        raw = struct.unpack('>H', data)[0]
        return raw

    def _read_raw_pressure(self):
        self.i2c.writeto_mem(self.addr, 0xF4, bytes([0x34 + (self.oversample_sett << 6)]))
        time.sleep_ms(2 + (3 << self.oversample_sett))
        data = self.i2c.readfrom_mem(self.addr, 0xF6, 3)
        raw = ((data[0] << 16) + (data[1] << 8) + data[2]) >> (8 - self.oversample_sett)
        return raw

    def measure(self):
        UT = self._read_raw_temp()
        UP = self._read_raw_pressure()

        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        B5 = X1 + X2
        self._temperature = ((B5 + 8) >> 4) / 10.0

        B6 = B5 - 4000
        X1 = (self.B2 * (B6 * B6 >> 12)) >> 11
        X2 = self.AC2 * B6 >> 11
        X3 = X1 + X2
        B3 = (((self.AC1 * 4 + X3) << self.oversample_sett) + 2) >> 2
        X1 = self.AC3 * B6 >> 13
        X2 = (self.B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self.oversample_sett)
        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2
        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        self._pressure = p + ((X1 + X2 + 3791) >> 4)

    @property
    def temperature(self):
        return self._temperature

    @property
    def pressure(self):
        return self._pressure

    @property
    def altitude(self):
        return 44330.0 * (1.0 - pow(self._pressure / self.sea_level_pressure, 0.1903))