# ================= SAFE BOOT WINDOW =================
import time
from machine import Pin, I2C, UART

time.sleep(2)          # allow Thonny or REPL to interrupt
print("Booting Pico...")

# ================= GPS UART0 =================
# GP0 = TX, GP1 = RX
gps = UART(0, 9600, tx=Pin(0), rx=Pin(1))

# ================= I2C LCD =================
# I2C0 on GP4=SDA, GP5=SCL
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
LCD_ADDR = 0x27

# ================= PCF8574 LCD DRIVER =================
class LCD:
    BL = 0x08
    EN = 0x04
    RS = 0x01

    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr
        self.backlight = self.BL
        self.init_lcd()

    def write(self, data):
        self.i2c.writeto(self.addr, bytes([data | self.backlight]))

    def pulse(self, data):
        self.write(data | self.EN)
        time.sleep_us(1)
        self.write(data & ~self.EN)
        time.sleep_us(50)

    def send(self, data, mode):
        self.pulse(data & 0xF0 | mode)
        self.pulse((data << 4) & 0xF0 | mode)

    def cmd(self, cmd):
        self.send(cmd, 0)

    def data(self, data):
        self.send(data, self.RS)

    def init_lcd(self):
        time.sleep_ms(20)
        self.cmd(0x33)
        self.cmd(0x32)
        self.cmd(0x28)
        self.cmd(0x0C)
        self.cmd(0x06)
        self.cmd(0x01)
        time.sleep_ms(20)

    def clear(self):
        self.cmd(0x01)
        time.sleep_ms(2)

    def move(self, col, row):
        self.cmd(0x80 + col + (0x40 if row else 0))

    def put(self, text):
        for c in text:
            self.data(ord(c))

lcd = LCD(i2c, LCD_ADDR)

# ================= GPS CONVERSION =================
def convert_to_degrees(raw, direction):
    try:
        deg = int(raw[:2])
        mins = float(raw[2:])
        val = deg + mins / 60
        if direction in ("S", "W"):
            val = -val
        return val
    except:
        return None

# ================= STARTUP MESSAGE =================
lcd.clear()
lcd.put("Waiting GPS...")
print("Waiting for GPS fix...")

# ================= MAIN LOOP =================
buffer = ""
last_lcd_update = time.ticks_ms()

while True:
    try:
        # -------- READ GPS (NON-BLOCKING) --------
        if gps.any():
            data = gps.read()
            if data:
                buffer += data.decode("utf-8", "ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
                        parts = line.split(",")

                        if len(parts) > 5 and parts[2] and parts[4]:
                            lat = convert_to_degrees(parts[2], parts[3])
                            lon = convert_to_degrees(parts[4], parts[5])

                            if lat is not None and lon is not None:
                                print("Lat:", lat)
                                print("Lon:", lon)

                                # -------- LCD (THROTTLED 1s) --------
                                if time.ticks_diff(time.ticks_ms(), last_lcd_update) > 1000:
                                    lcd.clear()
                                    lcd.move(0, 0)
                                    lcd.put("Lat:{:.6f}".format(lat))
                                    lcd.move(0, 1)
                                    lcd.put("Lon:{:.6f}".format(lon))
                                    last_lcd_update = time.ticks_ms()

        time.sleep_ms(50)

    except KeyboardInterrupt:
        lcd.clear()
        lcd.put("Stopped")
        print("Stopped by user")
        break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)

