import sys
sys.path.append('micropython_i2c_lcd')

import machine

from pcf8574 import PCF8574
from hd44780 import HD44780
from lcd import LCD


class Display(object):

    def __init__(self, i2c):
        pcf8574 = PCF8574(i2c)
        hd44780 = HD44780(pcf8574, num_lines=4, num_columns=20)
        self.lcd = LCD(hd44780, pcf8574)
        self._timer = machine.Timer()

    def illuminate(self):
        self.lcd.backlight_on()
        self._timer.init(mode=machine.Timer.ONE_SHOT, period=60000, callback=lambda t: self.lcd.backlight_off())
